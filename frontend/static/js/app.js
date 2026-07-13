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

function formatAnswer(text) {
  const safe = escapeHtml(text || '');
  const lines = safe.split('\n');

  const html = [];
  let listOpen = false;
  let listType = 'ul';

  const closeList = () => {
    if (listOpen) {
      html.push(`</${listType}>`);
      listOpen = false;
      listType = 'ul';
    }
  };

  const pushHeading = (content) => {
    closeList();
    html.push(`<h3 class="answer-heading">${content}</h3>`);
  };

  const pushParagraph = (content) => {
    closeList();
    html.push(`<p class="answer-paragraph">${content}</p>`);
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      closeList();
      continue;
    }

    const headingMatch = line.match(/^\*\*\s*(.+?)\s*\*\*\s*:?$/);
    const listMatch = line.match(/^([*+\-])\s+(.+)$/);
    const numberedMatch = line.match(/^(\d+)\.\s+(.+)$/);
    const quoteMatch = line.match(/^>\s+(.+)$/);

    if (headingMatch) {
      pushHeading(headingMatch[1]);
      continue;
    }

    if (quoteMatch) {
      closeList();
      html.push(`<blockquote class="answer-quote">${quoteMatch[1]}</blockquote>`);
      continue;
    }

    if (listMatch || numberedMatch) {
      const itemText = listMatch ? listMatch[2] : numberedMatch[2];
      const currentType = numberedMatch ? 'ol' : 'ul';

      if (!listOpen || listType !== currentType) {
        closeList();
        listOpen = true;
        listType = currentType;
        html.push(`<${listType} class="answer-list">`);
      }
      html.push(`<li>${itemText}</li>`);
      continue;
    }

    if (/^[A-Z][A-Za-z ]{2,}:$/.test(line) || /^Sources Used|^References from RAG|^Summary Recommendation|^Meal Plan|^Budget Guidance|^Nutrition \/ Health Reasoning|^Foods to Avoid|^Better Alternatives|^Comparison \/ Ranking/i.test(line)) {
      pushHeading(line.replace(/:$/, ''));
      continue;
    }

    pushParagraph(line);
  }

  closeList();
  return `<div class="answer-section answer-text">${html.join('')}</div>`;
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

async function loadCurrentUser() {
  if (!ensureAuth()) return null;
  if (state.user?.email) {
    return state.user;
  }

  try {
    const user = await api('/auth/profile');
    setUser(user);
    return user;
  } catch (error) {
    console.error('Failed to load current user:', error);
    return null;
  }
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
          <div class="history-response" style="display: none;">${escapeHtml(r.response_text || '')}</div>
        </div>`
      )
      .join('');

    el.querySelectorAll('.history-response').forEach((response) => {
      response.style.display = 'none';
      response.style.overflow = 'visible';
      response.style.maxHeight = 'none';
    });

    if (!el.dataset.historyClickBound) {
      el.addEventListener('click', (event) => {
        const item = event.target.closest('.history-item');
        if (!item || !el.contains(item)) return;
        const response = item.querySelector('.history-response');
        const expanded = item.classList.toggle('expanded');
        if (response) {
          response.style.display = expanded ? 'block' : 'none';
        }
      });
      el.dataset.historyClickBound = 'true';
    }

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

    if (!payload.query_text) {
      throw new Error('Please enter a question.');
    }

    const data = await api('/diet/query', { method: 'POST', body: payload });

    if (answerEl) {
      sessionStorage.setItem(
        'last_ai_result',
        JSON.stringify({
          query_text: payload.query_text,
          selected_food: payload.selected_food,
          portion: payload.portion,
          free_text_food: payload.free_text_food,
          answer: data.formatted_answer || '',
          references: data.references || [],
        })
      );
      window.location.href = '/results';
      return;
    }

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

    if (msg) {
      msg.innerHTML = '<div class="alert alert-success">✓ Done</div>';
    }
  } catch (error) {
    if (answerEl) {
      answerEl.innerHTML = `<div class="alert alert-error">❌ ${escapeHtml(error.message)}</div>`;
    }

    if (msg) {
      msg.innerHTML = `<div class="alert alert-error">Error: ${escapeHtml(error.message)}</div>`;
    }
  }
}

async function initDashboard() {
  if (!ensureAuth()) return;
  await loadCurrentUser();
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
  await loadCurrentUser();
  refreshUserUI();
  await loadFoods();
}

function formatAnswerFromText(text) {
  return formatAnswer(text);
}

function loadResultPage() {
  const result = sessionStorage.getItem('last_ai_result');
  const pageBody = $('resultBody');
  const queryText = $('resultQueryText');
  const selectedFood = $('resultSelectedFood');
  const portion = $('resultPortion');
  const freeFood = $('resultFreeFood');
  const answerEl = $('answer');
  const refsEl = $('refs');

  if (!result) {
    if (pageBody) {
      pageBody.innerHTML = '<div class="alert alert-error">No result data found. Please ask a question first.</div>';
    }
    return;
  }

  const data = JSON.parse(result);

  if (queryText) queryText.textContent = data.query_text || 'No question provided';
  if (selectedFood) selectedFood.textContent = data.selected_food || 'None';
  if (portion) portion.textContent = data.portion || 'Not set';
  if (freeFood) freeFood.textContent = data.free_text_food || 'None';
  if (answerEl) answerEl.innerHTML = formatAnswer(data.answer || 'No answer available.');

  if (refsEl) {
    const refs = data.references || [];
    refsEl.innerHTML = refs.length
      ? refs
          .map(
            (r) => `
            <div class="reference-card">
              <div class="reference-source">📄 ${escapeHtml(r.source || '')}</div>
              <div class="reference-snippet">${escapeHtml(r.snippet || '')}</div>
            </div>`
          )
          .join('')
      : '<div class="alert alert-warning">No references retrieved</div>';
  }
}

async function initHistory() {
  if (!ensureAuth()) return;
  await loadCurrentUser();
  refreshUserUI();
  await loadHistory();
}

async function initProfile() {
  if (!ensureAuth()) return;
  await loadCurrentUser();
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
window.formatAnswer = formatAnswer;
window.formatAnswerFromText = formatAnswerFromText;
window.loadResultPage = loadResultPage;
