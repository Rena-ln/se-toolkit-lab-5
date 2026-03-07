"""ETL pipeline: fetch data from the autochecker API and load it into the database.

The autochecker dashboard API provides two endpoints:
- GET /api/items — lab/task catalog
- GET /api/logs  — anonymized check results (supports ?since= and ?limit= params)

Both require HTTP Basic Auth (email + password from settings).
"""

from datetime import datetime
import httpx

from sqlmodel import select, func
from sqlmodel.ext.asyncio.session import AsyncSession

from app.settings import settings
from app.models.item import ItemRecord
from app.models.learner import Learner
from app.models.interaction import InteractionLog


# ---------------------------------------------------------------------------
# Extract — fetch data from the autochecker API
# ---------------------------------------------------------------------------


async def fetch_items() -> list[dict]:
    """Fetch the lab/task catalog from the autochecker API."""

    url = f"{settings.autochecker_api_url}/api/items"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            auth=(settings.autochecker_email, settings.autochecker_password),
        )

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch items: {response.status_code} {response.text}"
        )

    return response.json()


async def fetch_logs(since: datetime | None = None) -> list[dict]:
    """Fetch check results from the autochecker API."""

    url = f"{settings.autochecker_api_url}/api/logs"

    all_logs = []
    current_since = since

    async with httpx.AsyncClient() as client:

        while True:

            params = {"limit": 500}

            if current_since:
                params["since"] = current_since.isoformat()

            response = await client.get(
                url,
                params=params,
                auth=(settings.autochecker_email, settings.autochecker_password),
            )

            if response.status_code != 200:
                raise Exception(
                    f"Failed to fetch logs: {response.status_code} {response.text}"
                )

            data = response.json()

            logs = data.get("logs", [])
            has_more = data.get("has_more", False)

            if not logs:
                break

            all_logs.extend(logs)

            last_log = logs[-1]
            current_since = datetime.fromisoformat(
                last_log["submitted_at"].replace("Z", "+00:00")
            )

            if not has_more:
                break

    return all_logs


# ---------------------------------------------------------------------------
# Load — insert fetched data into the local database
# ---------------------------------------------------------------------------


async def load_items(items: list[dict], session: AsyncSession) -> int:
    """Load items (labs and tasks) into the database."""

    created = 0
    lab_lookup = {}

    # First process labs
    for item in items:

        if item["type"] != "lab":
            continue

        title = item["title"]

        result = await session.exec(
            select(ItemRecord).where(
                ItemRecord.type == "lab",
                ItemRecord.title == title,
            )
        )

        existing = result.first()

        if existing:
            lab_lookup[item["lab"]] = existing
            continue

        lab = ItemRecord(type="lab", title=title)

        session.add(lab)
        await session.flush()

        lab_lookup[item["lab"]] = lab
        created += 1

    # Then process tasks
    for item in items:

        if item["type"] != "task":
            continue

        parent_lab = lab_lookup.get(item["lab"])

        if not parent_lab:
            continue

        title = item["title"]

        result = await session.exec(
            select(ItemRecord).where(
                ItemRecord.type == "task",
                ItemRecord.title == title,
                ItemRecord.parent_id == parent_lab.id,
            )
        )

        existing = result.first()

        if existing:
            continue

        task = ItemRecord(
            type="task",
            title=title,
            parent_id=parent_lab.id,
        )

        session.add(task)
        created += 1

    await session.commit()

    return created


async def load_logs(
    logs: list[dict], items_catalog: list[dict], session: AsyncSession
) -> int:
    """Load interaction logs into the database."""

    created = 0

    # Map (lab_short, task_short) → title
    lookup = {}

    for item in items_catalog:
        lookup[(item["lab"], item["task"])] = item["title"]

    for log in logs:

        # Find or create learner
        result = await session.exec(
            select(Learner).where(Learner.external_id == log["student_id"])
        )

        learner = result.first()

        if not learner:
            learner = Learner(
                external_id=log["student_id"],
                student_group=log["group"],
            )
            session.add(learner)
            await session.flush()

        # Find item title
        title = lookup.get((log["lab"], log["task"]))

        if not title:
            continue

        result = await session.exec(
            select(ItemRecord).where(ItemRecord.title == title)
        )

        item = result.first()

        if not item:
            continue

        # Check duplicate interaction
        result = await session.exec(
            select(InteractionLog).where(
                InteractionLog.external_id == log["id"]
            )
        )

        existing = result.first()

        if existing:
            continue

        interaction = InteractionLog(
            external_id=log["id"],
            learner_id=learner.id,
            item_id=item.id,
            kind="attempt",
            score=log["score"],
            checks_passed=log["passed"],
            checks_total=log["total"],
            created_at=datetime.fromisoformat(
                log["submitted_at"].replace("Z", "+00:00")
            ),
        )

        session.add(interaction)
        created += 1

    await session.commit()

    return created


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


async def sync(session: AsyncSession) -> dict:
    """Run the full ETL pipeline."""

    # Step 1 — fetch and load items
    items = await fetch_items()
    await load_items(items, session)

    # Step 2 — find last synced interaction timestamp
    result = await session.exec(
        select(func.max(InteractionLog.created_at))
    )

    last_timestamp = result.one()

    # Step 3 — fetch logs
    logs = await fetch_logs(last_timestamp)

    # Step 4 — load logs
    new_records = await load_logs(logs, items, session)

    # Step 5 — count total interactions
    result = await session.exec(
        select(func.count(InteractionLog.id))
    )

    total_records = result.one()

    return {
        "new_records": new_records,
        "total_records": total_records,
    }
