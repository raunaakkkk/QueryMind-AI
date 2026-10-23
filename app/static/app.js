const state = {
  history: [],
  currentResults: [],
  currentSql: '',
  requestId: 0,
  activeController: null,
  requestPending: false
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
const executionTime = document.getElementById('execution-time');
const exportButton = document.getElementById('export-csv');
const copySqlButton = document.getElementById('copy-sql');
const runQueryButton = document.getElementById('run-query-button');
const exploreTableButton = document.getElementById('explore-table');
const tableSelect = document.getElementById('table-select');
const exampleSelect = document.getElementById('example-select');
const questionInput = document.getElementById('question-input');

function setRequestPending(pending) {
  state.requestPending = pending;
  runQueryButton.disabled = pending;
  runQueryButton.setAttribute('aria-busy', String(pending));
  runQueryButton.querySelector('.button-label').textContent = pending ? 'Running…' : 'Run query';
  exploreTableButton.disabled = pending;
  tableSelect.disabled = pending;
  exampleSelect.disabled = pending;
  questionInput.disabled = pending;
}

function beginRequest() {
  if (state.requestPending) {
    return null;
  }

  state.requestId += 1;
  state.activeController = new AbortController();
  setRequestPending(true);
  return {
    id: state.requestId,
    signal: state.activeController.signal
  };
}

function isCurrentRequest(request) {
  return request !== null && request.id === state.requestId;
}

function finishRequest(request) {
  if (!isCurrentRequest(request)) {
    return;
  }
  state.activeController = null;
  setRequestPending(false);
}

function cancelActiveRequest() {
  state.requestId += 1;
  state.activeController?.abort();
  state.activeController = null;
  setRequestPending(false);
}

class ApiError extends Error {
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  let data;
  try {
    data = await response.json();
  } catch {
    throw new ApiError(`The server returned an unreadable response (${response.status}).`, response.status);
  }

  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail.map((item) => item.msg).join(', ') : data.detail;
    throw new ApiError(data.error || detail || `Request failed (${response.status}).`, response.status, data);
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

const columnLabels = {
  total_count: 'Total count',
  average_marks: 'Average marks',
  total_marks: 'Total marks',
  highest_marks: 'Highest marks',
  lowest_marks: 'Lowest marks',
  department_id: 'Department ID',
  student_id: 'Student ID',
  department_name: 'Department',
  course_id: 'Course ID',
  course_name: 'Course',
  enrollment_id: 'Enrollment ID',
  mark_id: 'Mark ID',
  year: 'Year',
  name: 'Name',
  age: 'Age',
  gender: 'Gender',
  email: 'Email',
  credits: 'Credits',
  semester: 'Semester',
  marks: 'Marks',
  grade: 'Grade'
};

function setResultCount(count) {
  const rowCount = Number(count);
  if (!Number.isFinite(rowCount)) {
    resultCount.textContent = 'Results unavailable';
    return;
  }
  resultCount.textContent = `${formatNumber(rowCount)} ${rowCount === 1 ? 'row' : 'rows'}`;
}

function clearResults(message = 'Run a query or explore a table to see results.', countLabel = 'No results yet') {
  const head = table.querySelector('thead');
  const body = table.querySelector('tbody');
  head.replaceChildren();
  const row = document.createElement('tr');
  const cell = document.createElement('td');
  cell.className = 'empty-cell';
  cell.colSpan = 1;
  cell.textContent = message;
  row.append(cell);
  body.replaceChildren(row);
  state.currentResults = [];
  exportButton.disabled = true;
  resultCount.textContent = countLabel;
  executionTime.textContent = '';
}

function renderTable(rows, columns, emptyMessage = 'No rows returned.') {
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
    heading.textContent = columnLabels[column] || column;
    heading.title = column;
    headerRow.append(heading);
  });
  head.replaceChildren(headerRow);

  if (normalizedRows.length === 0) {
    const emptyRow = document.createElement('tr');
    const emptyCell = document.createElement('td');
    emptyCell.className = 'empty-cell';
    emptyCell.colSpan = Math.max(normalizedColumns.length, 1);
    emptyCell.textContent = emptyMessage;
    emptyRow.append(emptyCell);
    body.replaceChildren(emptyRow);
  } else {
    const tableRows = normalizedRows.map((row) => {
      const tableRow = document.createElement('tr');
      normalizedColumns.forEach((column) => {
        const cell = document.createElement('td');
        const value = row[column];
        cell.textContent = value === null ? 'NULL' : value === undefined ? '' : String(value);
        if (typeof value === 'number') {
          cell.classList.add('numeric-cell');
        }
        tableRow.append(cell);
      });
      return tableRow;
    });
    body.replaceChildren(...tableRows);
  }

  state.currentResults = normalizedRows;
  exportButton.disabled = normalizedRows.length === 0;
  setResultCount(normalizedRows.length);
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
  const displaySql = sql.replace(
    /\s+(LEFT JOIN|INNER JOIN|RIGHT JOIN|JOIN|FROM|WHERE|GROUP BY|ORDER BY|HAVING|LIMIT)\b/gi,
    '\n$1'
  );
  const highlighted = displaySql.replace(tokenPattern, (token) => {
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
  const request = beginRequest();
  if (!request) {
    return;
  }
  const question = questionInput.value.trim();
  if (!question) {
    finishRequest(request);
    setStatus('Please enter a question to get started.', 'error');
    questionInput.focus();
    return;
  }

  setStatus('Running your query…', 'loading');
  clearResults('Query is running…', 'Loading…');
  setSql('');
  explanationText.textContent = 'Waiting for the query to complete.';

  try {
    const data = await fetchJson('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
      signal: request.signal
    });
    if (!isCurrentRequest(request)) {
      return;
    }

    if (data.supported === false) {
      clearResults('This question is not supported.', 'Not supported');
      setSql('');
      explanationText.textContent = 'Try one of the example questions or rephrase your request.';
      setStatus('Unsupported question. Try one of the examples.', 'error');
      return;
    }

    const rows = Array.isArray(data.results) ? data.results : [];
    const columns = Array.isArray(data.columns) ? data.columns : [];
    const count = Number(data.result_count ?? rows.length);
    setSql(data.sql || '');
    explanationText.textContent = data.explanation || 'Query completed.';
    renderTable(rows, columns, 'No matching records found.');
    setResultCount(count);
    const elapsed = Number(data.execution_time_ms);
    executionTime.textContent = Number.isFinite(elapsed)
      ? `${formatNumber(elapsed, Number.isInteger(elapsed) ? 0 : 2)} ms`
      : '';
    setStatus(
      count === 0 ? 'Query completed. No matching records.' : 'Query completed successfully.',
      'success'
    );

    state.history = [question, ...state.history.filter((entry) => entry !== question)].slice(0, 5);
    renderHistory();
  } catch (error) {
    if (!isCurrentRequest(request) || error.name === 'AbortError') {
      return;
    }
    const unsupported = error instanceof ApiError
      && error.status === 400
      && error.payload?.supported === false;
    clearResults(
      unsupported ? 'This question is not supported.' : 'Results are unavailable for this request.',
      unsupported ? 'Not supported' : 'Unavailable'
    );
    setSql('');
    explanationText.textContent = unsupported
      ? 'Try one of the example questions or rephrase your request.'
      : 'No results are available because the request could not be completed.';
    setStatus(
      unsupported
        ? 'Unsupported question. Try one of the examples.'
        : 'Could not run the query. Please try again.',
      'error'
    );
  } finally {
    finishRequest(request);
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
  const request = beginRequest();
  if (!request) {
    return;
  }
  const tableName = tableSelect.value;
  clearResults('Loading table preview…', 'Loading…');
  setSql('');
  setStatus(`Loading ${tableName} preview…`, 'loading');
  try {
    const data = await fetchJson(`/api/tables/${encodeURIComponent(tableName)}`, { signal: request.signal });
    if (!isCurrentRequest(request)) {
      return;
    }
    const rows = Array.isArray(data.rows) ? data.rows : [];
    renderTable(rows, data.columns || [], 'This table has no preview rows.');
    setSql(`SELECT * FROM ${tableName} LIMIT 25;`);
    setStatus(`Table preview loaded: ${tableName}.`, 'success');
  } catch {
    if (!isCurrentRequest(request)) {
      return;
    }
    clearResults('Table preview is unavailable.', 'Unavailable');
    setSql('');
    setStatus('Could not load the table preview. Please try again.', 'error');
  } finally {
    finishRequest(request);
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
  const sql = state.currentSql;
  if (!sql) {
    return;
  }
  const requestId = state.requestId;
  try {
    await navigator.clipboard.writeText(sql);
    if (requestId === state.requestId && state.currentSql === sql) {
      setStatus('SQL copied to clipboard.', 'success');
    }
  } catch {
    if (requestId === state.requestId && state.currentSql === sql) {
      setStatus('Clipboard unavailable. Select and copy the SQL preview instead.', 'error');
    }
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
  cancelActiveRequest();
  questionInput.value = '';
  exampleSelect.value = '';
  setStatus('');
  setSql('');
  highlightSql('-- Your query will appear here');
  explanationText.textContent = 'A plain-language summary of your results will appear here.';
  clearResults();
  questionInput.focus();
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
