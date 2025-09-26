export default function GapMap({ gapMap }){
  const entries = Object.entries(gapMap || {})
  if(entries.length === 0){
    return <div style={{opacity:.8}}>No hard gaps found from the JD. Great job—this plan adds depth/breadth.</div>
  }

  return (
    <div className="gapmap">
      <div className="chips">
        {entries.map(([skill], i)=>(
          <span key={i} className="chip">{skill}</span>
        ))}
      </div>
    </div>
  )
}
