import { useEffect, useState } from 'react'
import './App.css'

const API = 'http://localhost:8000/api'
const today = new Date().toISOString().slice(0, 10)
const initialFilters = { start_date: today, end_date: today, min_calories: '0', max_calories: '10000' }

function number(value) {
  return Number(value || 0).toLocaleString(undefined, { maximumFractionDigits: 1 })
}

function App() {
  const [foods, setFoods] = useState([])
  const [filters, setFilters] = useState(initialFilters)
  const [report, setReport] = useState({ entries: [], totals: {}, count: 0 })
  const [form, setForm] = useState({ food_id: '', entry_date: today, servings: '1' })
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  async function request(path, options = {}) {
    const response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
    if (!response.ok) {
      const body = await response.json().catch(() => ({}))
      throw new Error(body.detail || 'Request failed')
    }
    return response.status === 204 ? null : response.json()
  }

  async function refresh() {
    const foodData = await request('/foods')
    setFoods(foodData)
    setForm((current) => ({ ...current, food_id: current.food_id || String(foodData[0]?.id || '') }))
  }

  async function runReport(event) {
    event?.preventDefault()
    try {
      const params = new URLSearchParams(filters)
      setReport(await request(`/report?${params}`))
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => {
    refresh().then(runReport).catch((err) => setError(`${err.message}. Start the API to load your tracker.`))
  }, [])

  async function saveEntry(event) {
    event.preventDefault()
    const payload = { ...form, food_id: Number(form.food_id), servings: Number(form.servings) }
    try {
      await request(editingId ? `/entries/${editingId}` : '/entries', {
        method: editingId ? 'PUT' : 'POST', body: JSON.stringify(payload),
      })
      setEditingId(null)
      setForm({ food_id: String(foods[0]?.id || ''), entry_date: today, servings: '1' })
      await refresh()
      await runReport()
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  function beginEdit(entry) {
    setEditingId(entry.id)
    setForm({ food_id: String(entry.food_id), entry_date: entry.entry_date, servings: String(entry.servings) })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function removeEntry(id) {
    try {
      await request(`/entries/${id}`, { method: 'DELETE' })
      await refresh()
      await runReport()
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }

  const metrics = [
    ['Calories', 'calories', 'kcal'], ['Protein', 'protein_g', 'g'],
    ['Carbs', 'carbs_g', 'g'], ['Fat', 'fat_g', 'g'],
  ]

  return (
    <main className="app-shell">
      <header className="topbar">
        <div><p className="eyebrow">DAILY NUTRITION</p><h1>Macro Tracker</h1></div>
        <span className="today-label">{new Date().toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric' })}</span>
      </header>

      {error && <div className="alert" role="alert">{error}</div>}

      <section className="entry-section">
        <div className="section-heading"><div><p className="eyebrow">FOOD LOG</p><h2>{editingId ? 'Edit entry' : 'Add an entry'}</h2></div></div>
        <form className="entry-form" onSubmit={saveEntry}>
          <label>Food<select required value={form.food_id} onChange={(e) => setForm({ ...form, food_id: e.target.value })}>
            {foods.map((food) => <option key={food.id} value={food.id}>{food.name} · {number(food.calories)} kcal / serving</option>)}
          </select></label>
          <label>Date<input required type="date" value={form.entry_date} onChange={(e) => setForm({ ...form, entry_date: e.target.value })} /></label>
          <label>Servings<input required type="number" min="0.1" max="100" step="0.1" value={form.servings} onChange={(e) => setForm({ ...form, servings: e.target.value })} /></label>
          <div className="form-actions"><button className="primary-button" type="submit">{editingId ? 'Save changes' : 'Add to log'}</button>
            {editingId && <button className="secondary-button" type="button" onClick={() => { setEditingId(null); setForm({ food_id: String(foods[0]?.id || ''), entry_date: today, servings: '1' }) }}>Cancel</button>}</div>
        </form>
      </section>

      <section className="report-section">
        <div className="section-heading"><div><p className="eyebrow">NUTRITION REPORT</p><h2>Logged nutrition</h2></div><span className="result-count">{report.count} {report.count === 1 ? 'entry' : 'entries'}</span></div>
        <form className="filter-bar" onSubmit={runReport}>
          <label>From<input type="date" required value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} /></label>
          <label>To<input type="date" required value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} /></label>
          <label>Min kcal / entry<input type="number" min="0" value={filters.min_calories} onChange={(e) => setFilters({ ...filters, min_calories: e.target.value })} /></label>
          <label>Max kcal / entry<input type="number" min="0" value={filters.max_calories} onChange={(e) => setFilters({ ...filters, max_calories: e.target.value })} /></label>
          <button className="secondary-button filter-button" type="submit">Apply filters</button>
        </form>

        <div className="totals-row">{metrics.map(([label, key, unit]) => <div className="total" key={key}><span>{label}</span><strong>{number(report.totals[key])}<small> {unit}</small></strong></div>)}</div>
        <div className="table-wrap">
          <table><thead><tr><th>Date</th><th>Food</th><th>Servings</th><th>Calories</th><th>Protein</th><th>Carbs</th><th>Fat</th><th><span className="sr-only">Actions</span></th></tr></thead>
            <tbody>{report.entries.length ? report.entries.map((entry) => <tr key={entry.id}>
              <td>{entry.entry_date}</td><td className="food-cell">{entry.food_name}</td><td>{number(entry.servings)}</td>
              <td>{number(entry.calories)} kcal</td><td>{number(entry.protein_g)} g</td><td>{number(entry.carbs_g)} g</td><td>{number(entry.fat_g)} g</td>
              <td className="row-actions"><button type="button" title="Edit entry" onClick={() => beginEdit(entry)}>Edit</button><button type="button" title="Delete entry" onClick={() => removeEntry(entry.id)}>Delete</button></td>
            </tr>) : <tr><td className="empty-state" colSpan="8">No food entries match these filters.</td></tr>}</tbody>
          </table>
        </div>
      </section>

      <section className="catalog-section"><h2>Food catalog</h2><p>Loaded from the database · {foods.length} foods</p>
        <div className="catalog-list">{foods.map((food) => <span key={food.id}>{food.name}<small>{number(food.calories)} kcal</small></span>)}</div>
      </section>
    </main>
  )
}

export default App
