import { prepareQuestions, searchQuestions } from './search.mjs';

const $ = selector => document.querySelector(selector);
const results = $('#results');
const search = $('#search');
const dialog = $('#answer-dialog');
let questions = [];
let currentFilter = 'all';
let visibleCount = 12;
let debounce;
let ready = false;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function showAnswer(item) {
  $('#dialog-question').textContent = item.question;
  const options = $('#dialog-options');
  options.replaceChildren();
  for (const option of item.options) {
    const state = option.correct === true ? 'correct' : option.correct === false ? 'wrong' : 'unknown';
    const row = element('div', `option ${state}`);
    const status = element('span', 'option-state');
    status.append(element('b', '', state === 'correct' ? '✓' : state === 'wrong' ? '×' : '—'),
      element('span', '', state === 'correct' ? '正确' : state === 'wrong' ? '错误' : '未验证'));
    row.append(element('span', 'option-label', option.label.toUpperCase()), element('span', 'option-text', option.text), status);
    options.append(row);
  }
  dialog.showModal();
}

function render() {
  if (!ready) return;
  const matches = searchQuestions(questions, search.value, currentFilter);
  const hasQuery = Boolean(search.value.trim());
  $('#results-heading').textContent = hasQuery ? '搜索结果' : '题库索引';
  $('#result-count').textContent = `${matches.length} 道题目`;
  $('#clear-search').hidden = !search.value;
  $('#empty-state').hidden = matches.length > 0;
  $('#load-more').hidden = matches.length <= visibleCount;
  results.replaceChildren();
  for (const [index, item] of matches.slice(0, visibleCount).entries()) {
    const card = element('button', 'question-card');
    card.type = 'button';
    card.setAttribute('aria-label', `查看选项：${item.question}`);
    const top = element('div', 'card-top');
    const hasCorrect = item.correctOptions.length > 0;
    top.append(element('span', 'card-index', `Q / ${String(index + 1).padStart(3, '0')}`),
      element('span', `card-status${hasCorrect ? '' : ' only-wrong'}`, hasCorrect ? '已确认答案' : '已有排除项'));
    const bottom = element('div', 'card-bottom');
    bottom.append(element('span', `answer-preview${hasCorrect ? '' : ' only-wrong'}`, hasCorrect
      ? item.correctOptions.map(option => option.text).join(' / ') : `已排除 ${item.wrongOptions.length} 个错误选项`),
    element('span', 'card-arrow', '↗'));
    card.append(top, element('h3', '', item.question), bottom);
    card.addEventListener('click', () => showAnswer(item));
    results.append(card);
  }
}

function refresh() { visibleCount = 12; render(); }
function clearSearch() { search.value = ''; refresh(); search.focus(); }

async function loadBank() {
  ready = false;
  results.setAttribute('aria-busy', 'true');
  $('#error-state').hidden = true;
  $('#empty-state').hidden = true;
  $('#result-count').textContent = '正在加载';
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch('./question_bank.json', { cache: 'no-store', signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    questions = prepareQuestions(await response.json());
    $('#total-questions').textContent = questions.length;
    $('#correct-count').textContent = questions.reduce((sum, item) => sum + item.correctOptions.length, 0);
    $('#wrong-count').textContent = questions.reduce((sum, item) => sum + item.wrongOptions.length, 0);
    const latest = questions.map(item => new Date(item.updatedAt)).filter(date => !Number.isNaN(+date)).sort((a, b) => b - a)[0];
    $('#updated-at').textContent = latest ? `最近记录 · ${latest.toLocaleDateString('zh-CN', { timeZone: 'Asia/Shanghai' })}` : '题库已就绪';
    search.disabled = false;
    $('#search-submit').disabled = false;
    ready = true;
    render();
  } catch (error) {
    $('#error-state').hidden = false;
    $('#result-count').textContent = '加载失败';
    $('#updated-at').textContent = '暂时无法读取题库';
  } finally {
    clearTimeout(timeout);
    results.setAttribute('aria-busy', 'false');
  }
}

$('#search-form').addEventListener('submit', event => { event.preventDefault(); clearTimeout(debounce); refresh(); });
search.addEventListener('input', event => {
  clearTimeout(debounce);
  if (!event.isComposing) debounce = setTimeout(refresh, 120);
});
search.addEventListener('compositionend', () => { clearTimeout(debounce); refresh(); });
$('#clear-search').addEventListener('click', clearSearch);
$('#reset-search').addEventListener('click', () => {
  currentFilter = 'all';
  document.querySelector('[data-filter="all"]').click();
  clearSearch();
});
document.querySelectorAll('[data-query]').forEach(button => button.addEventListener('click', () => {
  search.value = button.dataset.query;
  refresh();
  search.focus();
}));
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  currentFilter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(item => {
    const active = item === button;
    item.classList.toggle('active', active);
    item.setAttribute('aria-pressed', String(active));
  });
  refresh();
}));
$('#load-more').addEventListener('click', () => {
  const previousCount = visibleCount;
  visibleCount += 12;
  render();
  results.children[previousCount]?.focus();
});
$('#retry-load').addEventListener('click', loadBank);
$('#close-dialog').addEventListener('click', () => dialog.close());
$('#dialog-done').addEventListener('click', () => dialog.close());
dialog.addEventListener('click', event => {
  const rect = dialog.getBoundingClientRect();
  if (event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right
    || event.clientY < rect.top || event.clientY > rect.bottom)) dialog.close();
});
loadBank();
