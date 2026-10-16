export function normalize(text) {
  return String(text ?? '').normalize('NFKC').toLocaleLowerCase().replace(/[\p{P}\p{S}\s]/gu, '');
}

// 与 Python 题库一致：答案状态按文本匹配，仅使用最近一次明确对错。
export function prepareQuestions(bank) {
  if (bank?.version !== 1 || !bank.questions || typeof bank.questions !== 'object') {
    throw new Error('不支持的题库格式');
  }
  const identity = text => String(text).trim().replace(/\s+/gu, ' ');
  return Object.entries(bank.questions).flatMap(([id, entry]) => {
    const confirmed = (entry.attempts ?? []).filter(a => typeof a.correct === 'boolean');
    if (!confirmed.length) return [];
    const states = new Map();
    for (const attempt of confirmed) states.set(identity(attempt.answer), attempt.correct);
    const latestOptions = [...confirmed].reverse().find(a => a.options && typeof a.options === 'object')?.options;
    const options = Object.entries(latestOptions ?? {}).sort(([a], [b]) => a.localeCompare(b)).map(([label, text]) => ({
      label, text, correct: states.get(identity(text)) ?? null,
    }));
    // 兼容只有答案文本、没有完整选项的有效题库条目。
    if (!options.length) for (const [text, correct] of states) options.push({ label: '', text, correct });
    const correctOptions = options.filter(option => option.correct === true);
    const wrongOptions = options.filter(option => option.correct === false);
    return [{ id, question: entry.question, options, correctOptions, wrongOptions,
      searchable: normalize(entry.question), answers: options.map(o => normalize(o.text)),
      updatedAt: confirmed.at(-1).submitted_at }];
  });
}

function distanceToSubstring(query, text) {
  // Levenshtein 的首行置零，允许在长题干中查找带少量错字的短片段。
  let previous = Array(text.length + 1).fill(0);
  for (let row = 1; row <= query.length; row++) {
    const current = [row];
    for (let column = 1; column <= text.length; column++) {
      current[column] = Math.min(current[column - 1] + 1, previous[column] + 1,
        previous[column - 1] + (query[row - 1] === text[column - 1] ? 0 : 1));
    }
    previous = current;
  }
  return Math.min(...previous);
}

export function scoreQuestion(item, rawQuery) {
  const query = normalize(rawQuery).slice(0, 160);
  if (!query) return 1;
  if (item.searchable === query) return 100;
  if (item.searchable.includes(query)) return 90 + query.length / Math.max(item.searchable.length, 1);
  const tokens = String(rawQuery).trim().split(/\s+/u).map(normalize).filter(Boolean);
  if (tokens.length > 1 && tokens.every(token => item.searchable.includes(token))) return 85;
  if (query.length >= 4) {
    const distance = distanceToSubstring(query, item.searchable);
    if (distance <= (query.length >= 8 ? 2 : 1)) return 70 - distance;
  }
  if (item.answers.some(answer => answer.includes(query))) return 50;
  return 0;
}

export function searchQuestions(items, query, filter = 'all') {
  return items.filter(item => filter === 'correct' ? item.correctOptions.length > 0
    : filter === 'wrong' ? !item.correctOptions.length && item.wrongOptions.length > 0 : true)
    .map(item => ({ item, score: scoreQuestion(item, query) }))
    .filter(result => result.score > 0)
    .sort((a, b) => b.score - a.score)
    .map(result => result.item);
}
