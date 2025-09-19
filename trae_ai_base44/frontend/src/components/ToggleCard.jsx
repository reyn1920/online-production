import React from 'react'
export default function ToggleCard({title,desc,on, onToggle}){
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xl font-semibold">{title}</div>
          <div className="text-sm opacity-75 mt-1">{desc}</div>
        </div>
        <button className={"btn " + (on?'btn-on':'btn-off')} onClick={onToggle}>
          {on ? 'On' : 'Off'}
        </button>
      </div>
    </div>
  )
}
