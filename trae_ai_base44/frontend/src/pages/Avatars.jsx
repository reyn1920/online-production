import React from 'react'
export default function Avatars(){
  return (
    <div className="max-w-5xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-4">Avatars</h1>
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card">
          <div className="text-xl font-semibold">Linly Talker (default)</div>
          <div className="text-sm opacity-80">Use adapter to render with your audio + image.</div>
        </div>
        <div className="card">
          <div className="text-xl font-semibold">Talking Heads (optional)</div>
          <div className="text-sm opacity-80">Switch engine per job for side‑by‑side comparisons.</div>
        </div>
      </div>
      <div className="card mt-4">
        <div className="text-lg font-semibold mb-2">Visual Proofs</div>
        <pre className="text-xs bg-black/40 p-3 rounded-lg">python validators/make_visual_proofs.py{`\n`}python validators/quick_validation_run.py</pre>
      </div>
    </div>
  )
}
