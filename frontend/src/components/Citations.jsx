export default function Citations({ items }){
  if(!items || items.length===0) return null

  const clean = (txt='') => String(txt).replace(/\[.*?\]/g, '').trim()

  return (
    <div className="citations">
      <b>Citations:</b>
      <ul>
        {items.slice(0,3).map((c,i)=>(
          <li key={i}>{clean(c?.span || '')}</li>
        ))}
      </ul>
    </div>
  )
}
