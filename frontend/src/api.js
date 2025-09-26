export async function advise(profile){
  const res = await fetch('/api/advise', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile)
  })
  if(!res.ok){
    const text = await res.text().catch(()=> '')
    throw new Error(text || 'Failed to get advice')
  }
  return res.json()
}

export async function fetchCourse(id){
  const res = await fetch(`/api/courses/${encodeURIComponent(id)}`)
  if(!res.ok) throw new Error('Course not found')
  return res.json()
}
