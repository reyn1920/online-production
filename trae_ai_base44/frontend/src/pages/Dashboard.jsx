import React, {useEffect, useState} from 'react'
import ToggleCard from '../components/ToggleCard.jsx'
import {getJSON, postJSON} from '../api.js'

export default function Dashboard(){
  const [state, setState] = useState({go_live:false, automation:false})
  const [health, setHealth] = useState(null)

  const refresh = async () => {
    const s = await getJSON('/state'); setState(s)
    const h = await getJSON('/health'); setHealth(h)
  }
  useEffect(()=>{ refresh() },[])

  const setLive = async (v)=>{ await postJSON('/state', {go_live:v}); refresh() }
  const setAuto = async (v)=>{ await postJSON('/state', {automation:v}); refresh() }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">Base44 Control</h1>
      <div className="grid md:grid-cols-2 gap-4">
        <ToggleCard title="Go Live" desc="Expose services to the world (ensure network rules first)." on={state.go_live} onToggle={()=>setLive(!state.go_live)}/>
        <ToggleCard title="Automation" desc="Start or stop automation loops." on={state.automation} onToggle={()=>setAuto(!state.automation)}/>
      </div>

      <div className="grid md:grid-cols-3 gap-4 mt-6">
        <div className="card">
          <div className="text-lg font-semibold mb-2">API</div>
          <div className="text-sm opacity-80 mb-2">Health</div>
          <pre className="text-xs bg-black/40 p-3 rounded-lg">{health ? JSON.stringify(health,null,2) : '...'}</pre>
        </div>
        <div className="card">
          <div className="text-lg font-semibold mb-2">Audits</div>
          <div className="text-sm">Run from terminal before going live:</div>
          <pre className="text-xs bg-black/40 p-3 rounded-lg">python tools/py_audit.py .{`\n`}python tools/rule1_guard.py .</pre>
        </div>
        <div className="card">
          <div className="text-lg font-semibold mb-2">Avatars</div>
          <div className="text-sm opacity-80">Linly Talker as default; Talking Heads optional. Use validators to create proof media.</div>
          <pre className="text-xs bg-black/40 p-3 rounded-lg">python validators/make_visual_proofs.py{`\n`}python validators/quick_validation_run.py</pre>
        </div>
      </div>
    </div>
  )
}
