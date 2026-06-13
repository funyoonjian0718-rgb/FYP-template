// Shared frontend helpers for NutriDiag
const state = { token: localStorage.getItem('token')||'', user: JSON.parse(localStorage.getItem('user')||'{}') };

function escapeHtml(s){ return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#039;"); }

async function api(path, {method='GET', body=null}={}){
  const headers = {'Content-Type':'application/json'};
  if(state.token) headers['Authorization']=`Bearer ${state.token}`;
  const res = await fetch(path, {method, headers, body: body? JSON.stringify(body): null});
  const data = await res.json().catch(()=>({}));
  if(!res.ok) { const msg = data?.detail? String(data.detail): `HTTP ${res.status}`; throw new Error(msg); }
  return data;
}

function logout(){ if(confirm('Are you sure you want to logout?')){ state.token=''; localStorage.removeItem('token'); localStorage.removeItem('user'); window.location.href='/login'; } }

async function loadFoods(){ const dd = document.getElementById('foodDropdown'); if(!dd) return; dd.innerHTML=''; try{ const foods = await api('/diet/foods'); const opt0 = document.createElement('option'); opt0.value=''; opt0.textContent='(not selected)'; dd.appendChild(opt0); for(const f of foods){ const opt = document.createElement('option'); opt.value=f; opt.textContent=f; dd.appendChild(opt);} }catch(e){ console.error('Failed to load foods:', e); } }

async function loadHistory(){ const el = document.getElementById('history'); if(!el) return; el.textContent='Loading…'; try{ const rows = await api('/diet/history'); if(!rows.length){ el.textContent='(no history yet)'; return; } el.innerHTML = rows.map(r=>`<div class="history-item"><div class="history-time">⏰ ${escapeHtml(r.created_at||'')}</div><div class="history-question"><strong>Q:</strong> ${escapeHtml(r.query_text)}</div><div class="history-food"><strong>Food:</strong> ${escapeHtml(r.selected_food||'-')}</div><div class="history-response"><strong>A:</strong> ${escapeHtml((r.response_text||'').substring(0,150))}...</div></div>`).join(''); }catch(e){ el.innerHTML=`<div class="alert alert-error">Error: ${escapeHtml(e.message)}</div>`; } }

async function loadProfile(){ try{ const user = await api('/auth/profile'); state.user = user; localStorage.setItem('user', JSON.stringify(user)); const pe = document.getElementById('profileEmail'); if(pe) pe.textContent = user.email||''; const pd = document.getElementById('profileDiabetes'); if(pd) pd.value = user.type2_diabetes? 'true':'false'; const pa = document.getElementById('profileAge'); if(pa) pa.value = user.age||''; const pw = document.getElementById('profileWeight'); if(pw) pw.value = user.weight_kg||''; const pact = document.getElementById('profileActivity'); if(pact) pact.value = user.activity_level||''; const joined = user.created_at? new Date(user.created_at): null; const pj = document.getElementById('profileJoined'); if(pj && joined) pj.textContent = `Member since ${joined.toLocaleDateString()}`; }catch(e){ console.error('Failed to load profile:', e); } }

async function updateProfile(){ const msg = document.getElementById('profileMsg'); if(!msg) return; msg.textContent=''; try{ const payload = { type2_diabetes: document.getElementById('profileDiabetes').value === 'true', age: parseInt(document.getElementById('profileAge').value) || null, weight_kg: parseFloat(document.getElementById('profileWeight').value) || null, activity_level: document.getElementById('profileActivity').value || null }; await api('/auth/profile', {method:'PUT', body: payload}); msg.innerHTML = '<div class="alert alert-success">✓ Profile updated</div>'; setTimeout(()=> loadProfile(), 500); }catch(e){ msg.innerHTML = `<div class="alert alert-error">❌ ${escapeHtml(e.message)}</div>`; } }

// expose for pages that call directly
window.state = state; window.api = api; window.escapeHtml = escapeHtml; window.logout = logout; window.loadFoods = loadFoods; window.loadHistory = loadHistory; window.loadProfile = loadProfile; window.updateProfile = updateProfile;
const state = {
  token: localStorage.getItem("token") || "",
};

function $(id) {
  return document.getElementById(id);
}

function setStatus() {
  const el = $("authStatus");
  el.textContent = state.token ? "Logged in" : "Not logged in";
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll("\"", "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, { method = "GET", body = null } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;
  const res = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = data?.detail ? String(data.detail) : `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

async function loadFoods() {
  const dd = $("foodDropdown");
  dd.innerHTML = "";
  const foods = await api("/diet/foods");
  const opt0 = document.createElement("option");
  opt0.value = "";
  opt0.textContent = "(not selected)";
  dd.appendChild(opt0);
  for (const f of foods) {
    const opt = document.createElement("option");
    opt.value = f;
    opt.textContent = f;
    dd.appendChild(opt);
  }
}

$("btnRegister").addEventListener("click", async () => {
  const msg = $("regMsg");
  msg.textContent = "";
  try {
    const payload = {
      email: $("regEmail").value.trim(),
      password: $("regPassword").value,
      type2_diabetes: $("regT2").value === "true",
      age: $("regAge").value ? Number($("regAge").value) : null,
      weight_kg: $("regWeight").value ? Number($("regWeight").value) : null,
      activity_level: $("regActivity").value || null,
    };
    const data = await api("/auth/register", { method: "POST", body: payload });
    state.token = data.access_token;
    localStorage.setItem("token", state.token);
    msg.textContent = "Registered and logged in.";
    setStatus();
  } catch (e) {
    msg.innerHTML = `<span class="danger">${escapeHtml(e.message)}</span>`;
  }
});

$("btnLogin").addEventListener("click", async () => {
  const msg = $("loginMsg");
  msg.textContent = "";
  try {
    const payload = {
      email: $("loginEmail").value.trim(),
      password: $("loginPassword").value,
    };
    const data = await api("/auth/login", { method: "POST", body: payload });
    state.token = data.access_token;
    localStorage.setItem("token", state.token);
    msg.textContent = "Logged in.";
    setStatus();
  } catch (e) {
    msg.innerHTML = `<span class="danger">${escapeHtml(e.message)}</span>`;
  }
});

$("btnLogout").addEventListener("click", () => {
  state.token = "";
  localStorage.removeItem("token");
  setStatus();
  $("loginMsg").textContent = "Logged out.";
});

$("btnAsk").addEventListener("click", async () => {
  const msg = $("askMsg");
  msg.textContent = "";
  $("answer").textContent = "Working…";
  $("refs").textContent = "";
  try {
    const payload = {
      query_text: $("question").value.trim(),
      selected_food: $("foodDropdown").value || null,
      portion: $("portion").value || null,
      free_text_food: $("freeFood").value.trim() || null,
    };
    const data = await api("/diet/query", { method: "POST", body: payload });
    $("answer").textContent = data.formatted_answer;
    const refs = data.references || [];
    if (!refs.length) {
      $("refs").textContent = "(no references retrieved)";
    } else {
      $("refs").innerHTML = refs
        .map(
          (r) => `
          <div style="margin-bottom:10px;">
            <div><b>${escapeHtml(r.source)}</b></div>
            <div class="mono">${escapeHtml(r.snippet)}</div>
          </div>`
        )
        .join("");
    }
    msg.textContent = "Done.";
  } catch (e) {
    $("answer").innerHTML = `<span class="danger">${escapeHtml(e.message)}</span>`;
    msg.innerHTML = `<span class="danger">${escapeHtml(e.message)}</span>`;
  }
});

$("btnHistory").addEventListener("click", async () => {
  const el = $("history");
  el.textContent = "Loading…";
  try {
    const rows = await api("/diet/history");
    if (!rows.length) {
      el.textContent = "(no history yet)";
      return;
    }
    el.innerHTML = rows
      .map(
        (r) => `
        <div style="border:1px solid #223155;border-radius:10px;padding:10px;margin-bottom:10px;">
          <div class="muted">${escapeHtml(r.created_at)}</div>
          <div><b>Food:</b> ${escapeHtml(r.selected_food || "(none)")}, <b>Portion:</b> ${escapeHtml(
          r.portion || "(none)"
        )}</div>
          <div class="mono" style="margin-top:8px;">${escapeHtml(r.query_text)}</div>
        </div>`
      )
      .join("");
  } catch (e) {
    el.innerHTML = `<span class="danger">${escapeHtml(e.message)}</span>`;
  }
});

setStatus();
loadFoods().catch(() => {});

