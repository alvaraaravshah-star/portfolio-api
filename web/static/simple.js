// Render API URL
const API_BASE = 'https://portfolio-api-27sc.onrender.com';

async function loadOptions(){
  try{
    const d = await fetch(`${API_BASE}/available-dates`);
    const di = await d.json();
    const ds = document.getElementById('date-select');
    ds.innerHTML='';
    (di.dates||[]).forEach(date=>{ const o=document.createElement('option'); o.value=date; o.textContent=date; ds.appendChild(o)});
  }catch(e){console.error(e)}
  try{
    const r = await fetch(`${API_BASE}/available-investor-types`);
    const ri = await r.json();
    const rs = document.getElementById('investor-select');
    rs.innerHTML='';
    (ri.investor_types||[]).forEach(t=>{ const o=document.createElement('option'); o.value=t; o.textContent=t; rs.appendChild(o)});
  }catch(e){console.error(e)}
}

async function getRecommendation(){
  const date = document.getElementById('date-select').value;
  const investor = document.getElementById('investor-select').value;
  const area = document.getElementById('result-area');
  area.innerHTML = '<em>Loading...</em>';
  try{
    const resp = await fetch(`${API_BASE}/recommend`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({target_date:date,investor_type:investor})});
    if(!resp.ok){ area.innerHTML = '<pre>'+await resp.text()+'</pre>'; return; }
    const json = await resp.json();
    area.innerHTML = '<pre>'+JSON.stringify(json,null,2)+'</pre>';
  }catch(e){ area.innerHTML = '<pre>'+e.toString()+'</pre>'; }
}

document.getElementById('get-btn').addEventListener('click', getRecommendation);
window.addEventListener('load', loadOptions);
