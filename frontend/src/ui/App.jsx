import React, { useEffect, useState } from 'react'
function Toggle({label, value, onChange}){
  return (<label style={{display:'flex',gap:8,alignItems:'center'}}>
    <input type="checkbox" checked={!!value} onChange={e=>onChange(e.target.checked)} /><span>{label}</span>
  </label>)
}
export default function App(){
  const [channelId, setChannelId] = useState('channel_001')
  const [toggles, setToggles] = useState({live_on:false, auto_on:false, review_required:true, humanize_web_on:true})
  const [url, setUrl] = useState('https://example.org')

  const fetchToggles = async () => {
    const r = await fetch(`/automation/toggles?channel_id=${encodeURIComponent(channelId)}`)
    const j = await r.json(); setToggles(j)
  }
  useEffect(()=>{ fetchToggles() }, [channelId])

  const update = async (patch)=>{
    const next = {...toggles, ...patch}; setToggles(next)
    await fetch('/automation/toggles', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({channel_id:channelId, ...patch})})
  }
  const enqueueBrowse = async ()=>{
    await fetch('/webhuman/enqueue', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({url, headless:false})})
    alert('Enqueued (visible window)')
  }
  return (
    <div style={{padding:20, fontFamily:'ui-sans-serif, system-ui'}}>
      <h1>TRAE.AI Console (Live)</h1>
      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:20}}>
        <section style={{padding:16, border:'1px solid #ddd', borderRadius:12}}>
          <h3>Channel</h3>
          <input value={channelId} onChange={e=>setChannelId(e.target.value)} style={{width:'100%'}} />
          <div style={{display:'grid', gap:8, marginTop:12}}>
            <Toggle label="Live" value={toggles.live_on} onChange={v=>update({live_on:v})} />
            <Toggle label="Auto" value={toggles.auto_on} onChange={v=>update({auto_on:v})} />
            <Toggle label="Review Required" value={toggles.review_required} onChange={v=>update({review_required:v})} />
            <Toggle label="Humanize Web" value={toggles.humanize_web_on} onChange={v=>update({humanize_web_on:v})} />
          </div>
        </section>
        <section style={{padding:16, border:'1px solid #ddd', borderRadius:12}}>
          <h3>Web Task (Headful)</h3>
          <input value={url} onChange={e=>setUrl(e.target.value)} style={{width:'100%'}} />
          <button onClick={enqueueBrowse} style={{marginTop:12}}>Run Visible</button>
        </section>
      </div>
    </div>
  )
}
