import { useEffect, useState } from 'react'
import { fetchCourse } from '../api'
import Citations from './Citations'

export default function PlanCard({ item }){
  const [c, setC] = useState(null)

  useEffect(()=>{
    let active = true
    fetchCourse(item.course_id).then(data=>{
      if(active) setC(data)
    }).catch(()=>{})
    return ()=>{ active = false }
  }, [item.course_id])

  return (
    <div className="card">
      <div className="card-top">
        <div className="pill">{c?.difficulty || 'Course'}</div>
      </div>

      <h3 className="card-title">{c?.title || item.course_id}</h3>

      {c && (
        <div className="meta">
          <span><strong>Skills:</strong> {(c.skills||[]).join(', ') || '—'}</span>
          <span><strong>Duration:</strong> {c.duration_weeks ?? '—'} weeks</span>
          <span><strong>Level:</strong> {c.difficulty || '—'}</span>
        </div>
      )}

      {item.why && <p className="why">{item.why}</p>}

      <Citations items={item.citations} />
    </div>
  )
}
