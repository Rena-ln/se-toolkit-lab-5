from fastapi import APIRouter, Depends, Query
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import select, func, case, distinct

from app.database import get_session
from app.models.item import ItemRecord
from app.models.interaction import InteractionLog
from app.models.learner import Learner

router = APIRouter()


def _lab_title_fragment(lab: str) -> str:
    # "lab-04" → "Lab 04"
    parts = lab.split("-")
    if len(parts) == 2 and parts[0].lower() == "lab":
        return f"Lab {parts[1]}"
    return lab


@router.get("/scores")
async def get_scores(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    fragment = _lab_title_fragment(lab)

    # find the lab
    result = await session.exec(
        select(ItemRecord).where(
            ItemRecord.type == "lab",
            ItemRecord.title.contains(fragment),
        )
    )
    lab_item = result.scalars().first()

    # find tasks
    result = await session.exec(
        select(ItemRecord.id).where(ItemRecord.parent_id == lab_item.id)
    )
    task_ids = result.scalars().all()

    bucket_case = case(
        (InteractionLog.score <= 25, "0-25"),
        (InteractionLog.score <= 50, "26-50"),
        (InteractionLog.score <= 75, "51-75"),
        else_="76-100",
    )

    stmt = (
        select(bucket_case.label("bucket"), func.count())
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(bucket_case)
    )

    rows = await session.exec(stmt)
    pairs = rows.all()

    counts = {bucket: count for bucket, count in pairs}

    buckets = ["0-25", "26-50", "51-75", "76-100"]
    return [{"bucket": b, "count": counts.get(b, 0)} for b in buckets]


@router.get("/pass-rates")
async def get_pass_rates(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    fragment = _lab_title_fragment(lab)

    result = await session.exec(
        select(ItemRecord).where(
            ItemRecord.type == "lab",
            ItemRecord.title.contains(fragment),
        )
    )
    lab_item = result.scalars().first()

    stmt = (
        select(
            ItemRecord.title,
            func.avg(InteractionLog.score),
            func.count(InteractionLog.id),
        )
        .join(InteractionLog, InteractionLog.item_id == ItemRecord.id)
        .where(ItemRecord.parent_id == lab_item.id)
        .group_by(ItemRecord.title)
        .order_by(ItemRecord.title)
    )

    rows = await session.exec(stmt)
    results = rows.all()

    response = []
    for title, avg_score, attempts in results:
        response.append(
            {"task": title, "avg_score": round(avg_score, 1), "attempts": attempts}
        )
    return response


@router.get("/timeline")
async def get_timeline(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    fragment = _lab_title_fragment(lab)

    result = await session.exec(
        select(ItemRecord).where(
            ItemRecord.type == "lab",
            ItemRecord.title.contains(fragment),
        )
    )
    lab_item = result.scalars().first()

    result = await session.exec(
        select(ItemRecord.id).where(ItemRecord.parent_id == lab_item.id)
    )
    task_ids = result.scalars().all()

    date_col = func.date(InteractionLog.created_at)

    stmt = (
        select(date_col.label("date"), func.count().label("submissions"))
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(date_col)
        .order_by(date_col)
    )

    rows = await session.exec(stmt)
    timeline = rows.all()

    return [
        {"date": str(date), "submissions": submissions}
        for date, submissions in timeline
    ]


@router.get("/groups")
async def get_groups(
    lab: str = Query(..., description="Lab identifier, e.g. 'lab-01'"),
    session: AsyncSession = Depends(get_session),
):
    fragment = _lab_title_fragment(lab)

    result = await session.exec(
        select(ItemRecord).where(
            ItemRecord.type == "lab",
            ItemRecord.title.contains(fragment),
        )
    )
    lab_item = result.scalars().first()

    result = await session.exec(
        select(ItemRecord.id).where(ItemRecord.parent_id == lab_item.id)
    )
    task_ids = result.scalars().all()

    stmt = (
        select(
            Learner.student_group,
            func.avg(InteractionLog.score),
            func.count(distinct(Learner.id)),
        )
        .join(Learner, Learner.id == InteractionLog.learner_id)
        .where(InteractionLog.item_id.in_(task_ids))
        .group_by(Learner.student_group)
        .order_by(Learner.student_group)
    )

    rows = await session.exec(stmt)
    groups = rows.all()

    return [
        {"group": group, "avg_score": round(avg_score, 1), "students": students}
        for group, avg_score, students in groups
    ]
