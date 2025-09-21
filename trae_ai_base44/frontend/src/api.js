const API = (path) => (location.origin.replace('/dashboard','') + path);
export async function getJSON(path){ const r = await fetch(API(path)); if(!r.ok) throw new Error('request failed'); return r.json(); }
export async function postJSON(path, body){ const r = await fetch(API(path), {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)}); if(!r.ok) throw new Error('request failed'); return r.json(); }
