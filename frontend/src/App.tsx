import { useEffect, useState, ChangeEvent } from "react"
import "./App.css"

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js"

import { Bar, Line } from "react-chartjs-2"

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend
)

const STORAGE_KEY = "api_key"

/* ---------------- TYPES ---------------- */

type Page = "items" | "dashboard"

interface Item {
  id: number
  name: string
  type: string
  price: number
}

interface ScoreBucket {
  bucket: string
  count: number
}

interface TimelinePoint {
  date: string
  submissions: number
}

interface PassRate {
  task: string
  pass_rate: number
}

/* ---------------- LAB OPTIONS ---------------- */

const LABS = ["lab-01", "lab-02", "lab-03", "lab-04"]

/* ---------------- DASHBOARD ---------------- */

function Dashboard() {
  const token = localStorage.getItem(STORAGE_KEY)

  const [lab, setLab] = useState<string>("lab-04")

  const [scores, setScores] = useState<ScoreBucket[]>([])
  const [timeline, setTimeline] = useState<TimelinePoint[]>([])
  const [passRates, setPassRates] = useState<PassRate[]>([])

  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    async function loadAnalytics(): Promise<void> {
      try {
        setLoading(true)
        setError(null)

        const headers = {
          Authorization: `Bearer ${token}`,
        }

        const [scoresRes, timelineRes, passRes] = await Promise.all([
          fetch(`/analytics/scores?lab=${lab}`, { headers }),
          fetch(`/analytics/timeline?lab=${lab}`, { headers }),
          fetch(`/analytics/pass-rates?lab=${lab}`, { headers }),
        ])

        if (!scoresRes.ok || !timelineRes.ok || !passRes.ok) {
          throw new Error("Failed to fetch analytics")
        }

        const scoresData: ScoreBucket[] = await scoresRes.json()
        const timelineData: TimelinePoint[] = await timelineRes.json()
        const passData: PassRate[] = await passRes.json()

        setScores(scoresData)
        setTimeline(timelineData)
        setPassRates(passData)
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message)
        } else {
          setError("Unknown error")
        }
      } finally {
        setLoading(false)
      }
    }

    loadAnalytics()
  }, [lab, token])

  const scoreChartData = {
    labels: scores.map((s) => s.bucket),
    datasets: [
      {
        label: "Students",
        data: scores.map((s) => s.count),
      },
    ],
  }

  const timelineChartData = {
    labels: timeline.map((t) => t.date),
    datasets: [
      {
        label: "Submissions",
        data: timeline.map((t) => t.submissions),
      },
    ],
  }

  function handleLabChange(e: ChangeEvent<HTMLSelectElement>) {
    setLab(e.target.value)
  }

  if (!token) {
    return <p>No API key found in localStorage.</p>
  }

  return (
    <div>
      <h2>Analytics Dashboard</h2>

      <label>
        Lab:
        <select value={lab} onChange={handleLabChange}>
          {LABS.map((l) => (
            <option key={l} value={l}>
              {l}
            </option>
          ))}
        </select>
      </label>

      {loading && <p>Loading...</p>}
      {error && <p>Error: {error}</p>}

      {!loading && !error && (
        <>
          <section>
            <h3>Score Distribution</h3>
            <Bar data={scoreChartData} />
          </section>

          <section>
            <h3>Submissions Timeline</h3>
            <Line data={timelineChartData} />
          </section>

          <section>
            <h3>Pass Rates</h3>

            <table>
              <thead>
                <tr>
                  <th>Task</th>
                  <th>Pass Rate</th>
                </tr>
              </thead>

              <tbody>
                {passRates.map((row) => (
                  <tr key={row.task}>
                    <td>{row.task}</td>
                    <td>{(row.pass_rate * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </>
      )}
    </div>
  )
}

/* ---------------- ITEMS TABLE ---------------- */

function ItemsTable() {
  const token = localStorage.getItem(STORAGE_KEY)

  const [items, setItems] = useState<Item[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!token) return

    async function loadItems(): Promise<void> {
      try {
        const res = await fetch("/items", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })

        if (!res.ok) {
          throw new Error("Failed to fetch items")
        }

        const data: Item[] = await res.json()
        setItems(data)
      } catch (err) {
        if (err instanceof Error) {
          setError(err.message)
        } else {
          setError("Unknown error")
        }
      }
    }

    loadItems()
  }, [token])

  if (error) {
    return <p>Error: {error}</p>
  }

  return (
    <div>
      <h2>Items</h2>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Type</th>
            <th>Price</th>
          </tr>
        </thead>

        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{item.id}</td>
              <td>{item.name}</td>
              <td>{item.type}</td>
              <td>{item.price}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

/* ---------------- MAIN APP ---------------- */

function App() {
  const [page, setPage] = useState<Page>("items")

  return (
    <div className="app">
      <header className="app-header">
        <h1>Inventory App</h1>

        <nav>
          <button onClick={() => setPage("items")}>Items</button>
          <button onClick={() => setPage("dashboard")}>Dashboard</button>
        </nav>
      </header>

      <main>
        {page === "items" && <ItemsTable />}
        {page === "dashboard" && <Dashboard />}
      </main>
    </div>
  )
}

export default App