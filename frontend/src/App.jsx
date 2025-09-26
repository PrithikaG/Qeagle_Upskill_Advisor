import { useState } from 'react'
import { advise } from './api'
import PlanCard from './components/PlanCard'
import GapMap from './components/GapMap'
import PieTimeline from './components/PieTimeline'

export default function App(){
  const [skills, setSkills] = useState('')
  const [level, setLevel] = useState('')
  const [goal, setGoal] = useState('')
  const [resp, setResp] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const onSubmit = async (e)=>{
    e.preventDefault()
    setErr('')
    setResp(null)

    if(!goal.trim() || !level){
      setErr('Please choose a level and enter a target role.')
      return
    }

    const profile = {
      skills: skills.split(',').map(s=>s.trim()).filter(Boolean),
      level,
      goal_role: goal.trim()
    }

    setLoading(true)
    try{
      const data = await advise(profile)
      setResp(data)
    }catch(ex){
      setErr(ex.message || 'Something went wrong.')
    }finally{
      setLoading(false)
    }
  }

  async function downloadPDF(profile){
    try {
      const payload = {
        ...profile,
        prefs: {
          notes: resp?.notes || "",
        }
      }
      const res = await fetch('/api/advise/pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      if (!res.ok) throw new Error('Failed to download PDF')

      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'UpskillPlan.pdf'
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      alert('Error downloading PDF: ' + e.message)
    }
  }

  const onReset = ()=>{
    setSkills('')
    setLevel('')
    setGoal('')
    setResp(null)
    setErr('')
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="brand">
          <div className="logo-burst" />
          <h1>Upskill Advisor</h1>
        </div>
        <p className="tagline">Personalized learning plans from your skills & goals</p>
      </header>

      <main className="container">
        <form className="glass-card form" onSubmit={onSubmit}>
          <div className="field">
            <label>Current skills (comma separated)</label>
            <input
              value={skills}
              onChange={e=>setSkills(e.target.value)}
              placeholder="e.g., python, manual testing"
            />
          </div>

          <div className="two-col">
            <div className="field">
              <label>Level</label>
              <select value={level} onChange={e=>setLevel(e.target.value)}>
                <option value="">Select level…</option>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </div>

            <div className="field">
              <label>Target role</label>
              <input
                value={goal}
                onChange={e=>setGoal(e.target.value)}
                placeholder="e.g., SDET"
              />
            </div>
          </div>

          <div className="actions">
            <button className="btn-primary" disabled={loading}>
              {loading ? 'Generating…' : 'Generate Plan'}
            </button>
            <button type="button" className="btn-ghost" onClick={onReset}>Reset</button>
          </div>

          {err && <div className="alert">{err}</div>}
        </form>

        {loading && (
          <div className="loader-wrap">
            <div className="loader" />
            <div className="loader-text">Assembling your plan…</div>
          </div>
        )}

        {resp && (
          <>
            <section className="results">
              <h2 className="section-title">Recommended Learning Path</h2>
              <div className="grid">
                {(resp.plan || []).map((item, idx)=>(
                  <PlanCard key={idx} item={item} />
                ))}
              </div>
            </section>

            <section className="aux">
              <div className="glass-card timeline-card">
                <h3 style={{marginTop:0}}>Timeline</h3>
                <PieTimeline
                  schedule={resp.timeline?.schedule || []}
                  totalWeeks={resp.timeline?.weeks || 0}
                />
                {resp.notes && (
                  <div style={{marginTop:12}}>
                    <strong>Notes:</strong>
                    <p style={{marginTop:6}}>{resp.notes}</p>
                  </div>
                )}
                <button
                  className="btn-primary"
                  style={{marginTop: '20px'}}
                  onClick={() => downloadPDF({
                    skills: skills.split(',').map(s=>s.trim()).filter(Boolean),
                    level,
                    goal_role: goal.trim()
                  })}
                >
                  Download Plan as PDF
                </button>
              </div>

              <div className="glass-card gapmap-card">
                <h3 style={{marginTop:0}}>Gap Map</h3>
                <GapMap gapMap={resp.gap_map || {}} />
              </div>
            </section>
          </>
        )}
      </main>

      <footer className="footer">© {new Date().getFullYear()} Upskill Advisor</footer>
    </div>
  )
}
