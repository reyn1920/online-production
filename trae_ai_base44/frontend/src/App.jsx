import React, {useState} from 'react'
import Dashboard from './pages/Dashboard.jsx'
import Automation from './pages/Automation.jsx'
import Avatars from './pages/Avatars.jsx'

const Tab = ({id,label,active,set}) => (
  <button onClick={()=>set(id)} className={"px-4 py-2 rounded-xl mr-2 " + (active===id ? "bg-emerald-500 text-black" : "bg-slate-700")}>{label}</button>
)

export default function App(){
  const [tab,setTab]=useState('dash')
  return (
    <div>
      <div className="max-w-5xl mx-auto p-4 flex items-center justify-between">
        <div className="text-2xl font-bold">Base44</div>
        <div>
          <Tab id="dash" label="Front Page" active={tab} set={setTab}/>
          <Tab id="auto" label="Automation" active={tab} set={setTab}/>
          <Tab id="ava" label="Avatars" active={tab} set={setTab}/>
        </div>
      </div>
      {tab==='dash' && <Dashboard/>}
      {tab==='auto' && <Automation/>}
      {tab==='ava' && <Avatars/>}
    </div>
  )
}
