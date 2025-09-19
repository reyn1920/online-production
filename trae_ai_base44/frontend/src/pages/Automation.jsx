import React,{useEffect,useState} from 'react'
import {getJSON, postJSON} from '../api.js'
export default function Automation(){
  const [streams,setStreams]=useState([])
  const refresh=async()=>{ setStreams(await getJSON('/streams')) }
  useEffect(()=>{ refresh() },[])
  const toggle = async (name, enabled)=>{
    await postJSON('/streams/'+name, {enabled: !enabled}); refresh()
  }
  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">Income Streams</h1>
      <div className="grid md:grid-cols-2 gap-4">
        {streams.map(s=>(
          <div key={s.name} className="card">
            <div className="flex items-center justify-between">
              <div className="font-semibold">{s.name.replace('_',' ')}</div>
              <button className={"btn " + (s.enabled?'btn-on':'btn-off')} onClick={()=>toggle(s.name,s.enabled)}>
                {s.enabled?'On':'Off'}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
