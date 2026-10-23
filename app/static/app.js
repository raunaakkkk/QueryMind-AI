const state = {
  history: [],
  currentResults: [],
  currentSql: ''
};

const summaryCards = document.getElementById('summary-cards');
const chartArea = document.getElementById('chart-area');
const table = document.getElementById('results-table');
const sqlPreview = document.getElementById('sql-preview');
const explanationText = document.getElementById('explanation-text');
const statusEl = document.getElementById('status');
const historyList = document.getElementById('history-list');
const historyEmpty = document.getElementById('history-empty');
const resultCount = document.getElementById('result-count');
const exportButton = document.getElementById('export-csv');
const copySqlButton = document.getElementById('copy-sql');
const runQueryButton = document.getElementById('run-query-button');

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`The server returned an unreadable response (${response.status}).`);
  }

  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join(', ') : data.detail;
    throw new Error(data.error || detail || `Request failed (${response.status}).`);
  }
  return data;
}

function setStatus(message, kind = '') {
  statusEl.textContent = message;
  statusEl.className = `status${kind ? ` ${kind}` : ''}`;
}

function formatNumber(value, digits = 0) {
  const number = Number(value);
  return Number.isFinite(number)
    ? number.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits })
    : '—';
}

async function loadSummary() {
  try {
    const data = await fetchJson('/api/analytics/summary');
    const cards = [
      { label: 'Students', value: formatNumber(data.total_students) },
      { label: 'Departments', value: formatNumber(data.total_departments) },
      { label: 'Courses', value: formatNumber(data.total_courses) },
      { label: 'Average mark', value: formatNumber(data.average_marks, 1) },
    ];

    summaryCards.replaceChildren(...cards.map((card) => {
      const element = document.createElement('div');
      element.className = 'summary-card';
      const label = document.createElement('h3');
      label.textContent = card.label;
      const value = document.createElement('p');
      value.textContent = card.value;
      element.append(label, value);
      return element;
    }));
  } catch (error) {
    summaryCards.replaceChildren(createMessage(error.message, 'inline-error'));
  }

  try {
    const distribution = await fetchJson('/api/analytics/department-distribution');
    renderDistribution(distribution);
  } catch (error) {
    chartArea.replaceChildren(createMessage(error.message, 'inline-error'));
  }
}

function createMessage(text, className) {
  const message = document.createElement('p');
  message.className = className;
  message.textContent = text;
  return message;
}

function renderDistribution(distribution) {
  if (!Array.isArray(distribution) || distribution.length === 0) {
    chartArea.replaceChildren(createMessage('No department data is available.', 'loading-placeholder'));
    return;
  }

  const maxValue = Math.max(...distribution.map((item) => Number(item.student_count) || 0), 1);
  const rows = distribution.map((item) => {
    const count = Number(item.student_count) || 0;
    const row = document.createElement('div');
    row.className = 'chart-row';

    const label = document.createElement('span');
    label.className = 'chart-label';
    label.textContent = item.department ?? 'Unknown department';
    label.title = label.textContent;

    const track = document.createElement('div');
    track.className = 'chart-track';
    track.setAttribute('aria-hidden', 'true');
    const bar = document.createElement('div');
    bar.className = 'chart-bar';
    bar.style.width = `${Math.max((count / maxValue) * 100, count > 0 ? 1 : 0)}%`;
    track.append(bar);

    const value = document.createElement('span');
    value.className = 'chart-value';
    value.textContent = formatNumber(count);
    row.append(label, track, value);
    return row;
  });

  chartArea.replaceChildren(...rows);
}

function renderTable(rows, columns) {
  const normalizedRows = Array.isArray(rows) ? rows : [];
  const normalizedColumns = Array.isArray(columns) && columns.length
    ? columns
    : (normalizedRows.length ? Object.keys(normalizedRows[0]) : []);
  const head = table.querySelector('thead');
  const body = table.querySelector('tbody');
  const headerRow = document.createElement('tr');

  normalizedColumns.forEach((column) => {
    const heading = document.createElement('th');
    heading.scope = 'col';
    heading.textContent = column;
    headerRow.append(heading);
  });
  head.replaceChildren(headerRow);

  if (normalizedRows.length === 0) {
    const emptyRow = document.createElement('tr');
    const emptyCell = document.createElement('td');
    emptyCell.className = 'empty-cell';
    emptyCell.colSpan = Math.max(normalizedColumns.length, 1);
    emptyCell.textContent = 'No rows returned.';
    emptyRow.append(emptyCell);
    body.replaceChildren(emptyRow);
  } else {
    const tableRows = normalizedRows.map((row) => {
      const tableRow = document.createElement('tr');
      normalizedColumns.forEach((column) => {
        const cell = document.createElement('td');
        cell.textContent = row[column] == null ? '' : String(row[column]);
        tableRow.append(cell);
      });
      return tableRow;
    });
    body.replaceChildren(...tableRows);
  }

  state.currentResults = normalizedRows;
  exportButton.disabled = normalizedRows.length === 0;
  resultCount.textContent = formatNumber(normalizedRows.length);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (character) => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  })[character]);
}

const sqlKeywords = new Set([
  'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 'ON', 'AS',
  'GROUP', 'BY', 'ORDER', 'ASC', 'DESC', 'LIMIT', 'COUNT', 'AVG', 'MAX',
  'MIN', 'SUM', 'DISTINCT', 'AND', 'OR', 'NOT', 'IN', 'IS', 'NULL', 'LIKE',
  'HAVING', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END'
]);

function highlightSql(sql) {
  const tokenPattern = /(--[^\n]*|'(?:''|[^'])*'|\b[A-Za-z_][A-Za-z_0-9]*\b|\b\d+(?:\.\d+)?\b|\?)/g;
  const highlighted = sql.replace(tokenPattern, (token) => {
    let className = '';
    if (token.startsWith('--')) {
      className = 'sql-comment';
    } else if (token.startsWith("'")) {
      className = 'sql-string';
    } else if (/^\d/.test(token)) {
      className = 'sql-number';
    } else if (sqlKeywords.has(token.toUpperCase())) {
      className = 'sql-keyword';
    }
    const escaped = escapeHtml(token);
    return className ? `<span class="${className}">${escaped}</span>` : escaped;
  });

  sqlPreview.innerHTML = `<code>${highlighted}</code>`;
}

function setSql(sql) {
  state.currentSql = sql || '';
  highlightSql(state.currentSql || '-- Your query will appear here');
  copySqlButton.disabled = !state.currentSql;
}

async function handleQuery(event) {
  event.preventDefault();
  const questionInput = document.getElementById('question-input');
  const question = questionInput.value.trim();
  if (!question) {
    setStatus('Please enter a question to get started.', 'error');
    questionInput.focus();
    return;
  }

  setStatus('Running your query…', 'loading');
  runQueryButton.disabled = true;
  runQueryButton.setAttribute('aria-busy', 'true');
  runQueryButton.querySelector('.button-label').textContent = 'Running…';

  try {
    const data = await fetchJson('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });

    setSql(data.sql || '');
    explanationText.textContent = data.explanation || 'Query completed.';
    renderTable(data.results || [], data.columns || []);
    setStatus(`Returned ${formatNumber(data.result_count ?? 0)} result(s) in ${formatNumber(data.execution_time_ms ?? 0)} ms.`, 'success');

    state.history = [question, ...state.history.filter((entry) => entry !== question)].slice(0, 5);
    renderHistory();
  } catch (error) {
    setStatus(error.message || 'The query could not be completed.', 'error');
  } finally {
    runQueryButton.disabled = false;
    runQueryButton.removeAttribute('aria-busy');
    runQueryButton.querySelector('.button-label').textContent = 'Run query';
  }
}

function renderHistory() {
  const items = state.history.map((question) => {
    const item = document.createElement('li');
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'history-item';
    button.textContent = question;
    button.addEventListener('click', () => {
      document.getElementById('question-input').value = question;
      document.getElementById('question-input').focus();
    });
    item.append(button);
    return item;
  });
  historyList.replaceChildren(...items);
  historyEmpty.classList.toggle('visible', state.history.length === 0);
}

async function exploreTable() {
  const tableName = document.getElementById('table-select').value;
  const exploreButton = document.getElementById('explore-table');
  exploreButton.disabled = true;
  try {
    const data = await fetchJson(`/api/tables/${encodeURIComponent(tableName)}`);
    renderTable(data.rows || [], data.columns || []);
    setSql(`SELECT * FROM ${tableName} LIMIT 25;`);
    setStatus(`Showing ${formatNumber((data.rows || []).length)} preview row(s) from ${tableName}.`, 'success');
  } catch (error) {
    setStatus(error.message || 'The table preview could not be loaded.', 'error');
  } finally {
    exploreButton.disabled = false;
  }
}

function exportCsv() {
  if (!state.currentResults.length) {
    return;
  }
  const columns = Object.keys(state.currentResults[0]);
  const lines = [columns.map(escapeCsvValue).join(',')];
  for (const row of state.currentResults) {
    lines.push(columns.map((key) => escapeCsvValue(row[key])).join(','));
  }

  const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'query_results.csv';
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function escapeCsvValue(value) {
  return `"${String(value ?? '').replace(/"/g, '""')}"`;
}

async function copySql() {
  if (!state.currentSql) {
    return;
  }
  try {
    await navigator.clipboard.writeText(state.currentSql);
    setStatus('SQL copied to clipboard.', 'success');
  } catch {
    setStatus('Could not access the clipboard. Select and copy the SQL preview instead.', 'error');
  }
}

function setExample() {
  const select = document.getElementById('example-select');
  if (select.value) {
    document.getElementById('question-input').value = select.value;
    document.getElementById('question-input').focus();
  }
}

function resetForm() {
  document.getElementById('question-input').value = '';
  document.getElementById('example-select').value = '';
  setStatus('');
  setSql('');
  highlightSql('-- Your query will appear here');
  explanationText.textContent = 'A plain-language summary of your results will appear here.';
  table.querySelector('thead').replaceChildren();
  const emptyRow = document.createElement('tr');
  const emptyCell = document.createElement('td');
  emptyCell.className = 'empty-cell';
  emptyCell.textContent = 'Run a query or explore a table to see results.';
  emptyRow.append(emptyCell);
  table.querySelector('tbody').replaceChildren(emptyRow);
  state.currentResults = [];
  resultCount.textContent = '—';
  exportButton.disabled = true;
  document.getElementById('question-input').focus();
}

document.getElementById('query-form').addEventListener('submit', handleQuery);
document.getElementById('table-select').addEventListener('change', exploreTable);
document.getElementById('explore-table').addEventListener('click', exploreTable);
document.getElementById('export-csv').addEventListener('click', exportCsv);
document.getElementById('example-select').addEventListener('change', setExample);
document.getElementById('copy-sql').addEventListener('click', copySql);
document.getElementById('reset-button').addEventListener('click', resetForm);

loadSummary();
renderHistory();
exploreTable();
