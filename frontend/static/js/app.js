const state = {
  token: localStorage.getItem('token') || '',
  user: JSON.parse(localStorage.getItem('user') || '{}'),
};

function $(id) {
  return document.getElementById(id);
}

function escapeHtml(s) {
  return String(s)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

async function api(path, { method = 'GET', body = null } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  const contentType = response.headers.get('content-type') || '';
  const data = contentType.includes('application/json')
    ? await response.json().catch(() => ({}))
    : {};

  if (!response.ok) {
    const msg = data?.detail ? String(data.detail) : `HTTP ${response.status}`;
    throw new Error(msg);
  }
  return data;
}

function setToken(token) {
  state.token = token || '';
  if (state.token) {
    localStorage.setItem('token', state.token);
  } else {
    localStorage.removeItem('token');
  }
}

function setUser(user) {
  state.user = user || {};
  localStorage.setItem('user', JSON.stringify(state.user));
}

function logout() {
  if (!confirm('Are you sure you want to logout?')) {
    return;
  }
  setToken('');
  setUser({});
  window.location.href = '/login';
}

function ensureAuth() {
  if (!state.token) {
    window.location.href = '/login';
    return false;
  }
  return true;
}

function refreshUserUI() {
  const email = state.user?.email || 'user@example.com';
  const avatar = (email[0] || 'U').toUpperCase();

  document.querySelectorAll('#userAvatar, #profileAvatar').forEach((el) => {
    el.textContent = avatar;
  });
  document.querySelectorAll('#userEmail, #profileEmail').forEach((el) => {
    el.textContent = email;
  });
}

async function loadFoods() {
  const dd = $('foodDropdown');
  if (!dd) return;
  dd.innerHTML = '';

  try {
    const foods = await api('/diet/foods');
    const opt0 = document.createElement('option');
    opt0.value = '';
    opt0.textContent = '(not selected)';
    dd.appendChild(opt0);

    for (const item of foods || []) {
      const opt = document.createElement('option');
      opt.value = item;
      opt.textContent = item;
      dd.appendChild(opt);
    }
  } catch (error) {
    console.error('Failed to load foods:', error);
  }
}

async function loadHistory() {
  const el = $('history');
  if (!el) return [];
  el.textContent = 'Loading…';

  try {
    const rows = await api('/diet/history');
    if (!rows || !rows.length) {
      el.textContent = '(no history yet)';
      return [];
    }
    el.innerHTML = rows
      .map(
        (r) => `
        <div class="history-item">
          <div class="history-time">⏰ ${escapeHtml(r.created_at || '')}</div>
          <div class="history-question">${escapeHtml(r.query_text || '')}</div>
          <div class="history-food"><strong>Food:</strong> ${escapeHtml(r.selected_food || '-')}</div>
          <div class="history-response">${escapeHtml((r.response_text || '').substring(0, 150))}...</div>
        </div>`
      )
      .join('');
    return rows;
  } catch (error) {
    el.innerHTML = `<div class="alert alert-error">Error: ${escapeHtml(error.message)}</div>`;
    return [];
  }
}

async function loadProfile() {
  const profileEmail = $('profileEmail');
  const diabetesEl = $('profileDiabetes');
  const ageEl = $('profileAge');
  const weightEl = $('profileWeight');
  const activityEl = $('profileActivity');
  const joinedEl = $('profileJoined');

  try {
    const user = await api('/auth/profile');
    setUser(user);
    refreshUserUI();

    if (profileEmail) profileEmail.textContent = user.email || '';
    if (diabetesEl) diabetesEl.value = user.type2_diabetes ? 'true' : 'false';
    if (ageEl) ageEl.value = user.age || '';
    if (weightEl) weightEl.value = user.weight_kg || '';
    if (activityEl) activityEl.value = user.activity_level || '';
    if (joinedEl && user.created_at) {
      const date = new Date(user.created_at);
      joinedEl.textContent = `Member since ${date.toLocaleDateString()}`;
    }
    return user;
  } catch (error) {
    console.error('Failed to load profile:', error);
    return null;
  }
}

async function updateProfile() {
  const msg = $('profileMsg');
  if (msg) msg.textContent = '';

  try {
    const payload = {
      type2_diabetes: $('profileDiabetes')?.value === 'true',
      age: $('profileAge')?.value ? Number($('profileAge').value) : null,
      weight_kg: $('profileWeight')?.value ? Number($('profileWeight').value) : null,
      activity_level: $('profileActivity')?.value || null,
    };

    await api('/auth/profile', { method: 'PUT', body: payload });
    if (msg) msg.innerHTML = '<div class="alert alert-success">✓ Profile updated</div>';
    await loadProfile();
  } catch (error) {
    if (msg) msg.innerHTML = `<div class="alert alert-error">❌ ${escapeHtml(error.message)}</div>`;
  }
}

async function askQuestion() {
  const msg = $('askMsg');
  const answerEl = $('answer');
  const refsEl = $('refs');
  if (msg) msg.textContent = '';
  if (answerEl) answerEl.innerHTML = '<span class="loading"></span> Working…';
  if (refsEl) refsEl.textContent = '';

  try {
    const payload = {
      query_text: $('question')?.value.trim() || '',
      selected_food: $('foodDropdown')?.value || null,
      portion: $('portion')?.value || null,
      free_text_food: $('freeFood')?.value.trim() || null,
    };
    if (!payload.query_text) throw new Error('Please enter a question.');

    const data = await api('/diet/query', { method: 'POST', body: payload });
    if (answerEl) answerEl.innerHTML = `<div class="answer-section">${escapeHtml(data.formatted_answer || '')}</div>`;

    if (refsEl) {
      const refs = data.references || [];
      if (!refs.length) {
        refsEl.innerHTML = '<div class="alert alert-warning">No references retrieved</div>';
      } else {
        refsEl.innerHTML = refs
          .map(
            (r) => `
            <div class="reference-card">
              <div class="reference-source">📄 ${escapeHtml(r.source || '')}</div>
              <div class="reference-snippet">${escapeHtml(r.snippet || '')}</div>
            </div>`
          )
          .join('');
      }
    }

    if (msg) msg.innerHTML = '<div class="alert alert-success">✓ Done</div>';
  } catch (error) {
    if (answerEl) answerEl.innerHTML = `<div class="alert alert-error">❌ ${escapeHtml(error.message)}</div>`;
    if (msg) msg.innerHTML = `<div class="alert alert-error">Error: ${escapeHtml(error.message)}</div>`;
  }
}

async function initDashboard() {
  if (!ensureAuth()) return;
  refreshUserUI();

  try {
    const history = await api('/diet/history');
    const totalQueriesEl = $('totalQueries');
    const recentQueriesEl = $('recentQueries');
    const savedAdviceEl = $('savedAdvice');
    const recentActivityEl = $('recentActivity');
    const recent = history || [];

    if (totalQueriesEl) totalQueriesEl.textContent = String(recent.length);
    if (recentQueriesEl) recentQueriesEl.textContent = String(recent.slice(0, 7).length);
    if (savedAdviceEl) savedAdviceEl.textContent = String(recent.length ? recent.length : 0);
    if (recentActivityEl) {
      recentActivityEl.innerHTML =
        recent
          .slice(0, 3)
          .map(
            (r) => `
            <div class="history-item">
              <div class="history-time">⏰ ${escapeHtml(r.created_at || '')}</div>
              <div class="history-question">${escapeHtml(r.query_text || '')}</div>
            </div>`
          )
          .join('') || '<p class="muted">No recent activity</p>';
    }
  } catch (error) {
    console.error('Failed to load dashboard data:', error);
  }
}

async function initAsk() {
  if (!ensureAuth()) return;
  refreshUserUI();
  await loadFoods();
}

async function initHistory() {
  if (!ensureAuth()) return;
  refreshUserUI();
  await loadHistory();
}

async function initProfile() {
  if (!ensureAuth()) return;
  refreshUserUI();
  await loadProfile();
}

window.state = state;
window.api = api;
window.escapeHtml = escapeHtml;
window.logout = logout;
window.loadFoods = loadFoods;
window.loadHistory = loadHistory;
window.loadProfile = loadProfile;
window.updateProfile = updateProfile;
window.askQuestion = askQuestion;
window.initDashboard = initDashboard;
window.initAsk = initAsk;
window.initHistory = initHistory;
window.initProfile = initProfile;
window.setToken = setToken;
window.setUser = setUser;

