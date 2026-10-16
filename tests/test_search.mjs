import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { normalize, prepareQuestions, searchQuestions } from '../site/search.mjs';

const options = { a1: '2006年', a2: '2007年', a3: '2008年', a4: '2009年' };
const bank = { version: 1, questions: {
  album: { question: '陈奕迅在哪一年发行专辑《认了吧》？', attempts: [
    { answer: '2006年', correct: false, options },
    { answer: '2007年', correct: true, options },
  ] },
  sameTitle: { question: '陈奕迅在哪一年发行专辑《认了吧》？', attempts: [
    { answer: '2005年', correct: false, options: { a1: '2005年', a2: '2007年' } },
  ] },
  song: { question: '歌曲《十年》的作曲人是谁？', attempts: [
    { answer: '陈小霞', correct: true, options: { a1: '陈小霞', a2: '林夕' } },
  ] },
  unknown: { question: '未知题目', attempts: [{ answer: 'A', correct: null }] },
} };
const items = prepareQuestions(bank);

test('only confirmed records are indexed; same-title variants stay separate', () => {
  assert.equal(items.length, 3);
  assert.equal(items.filter(item => item.question.includes('认了吧')).length, 2);
});
test('status includes green, red and unverified options', () => {
  assert.deepEqual(items[0].options.map(option => option.correct), [false, true, null, null]);
});
test('latest confirmed status wins, and unknown does not override it', () => {
  const item = prepareQuestions({ version: 1, questions: { a: { question: '题目', attempts: [
    { answer: 'A', correct: true, options: { a1: 'A' } },
    { answer: 'A', correct: false, options: { a2: 'A' } },
    { answer: 'A', correct: null, options: { a3: 'A' } },
  ] } } })[0];
  assert.equal(item.options[0].label, 'a2');
  assert.equal(item.options[0].correct, false);
});
test('exact and substring search ignore spacing, punctuation and case', () => {
  assert.equal(normalize('《ＥＡＳＯＮ》 ＡＩＲ'), 'easonair');
  assert.equal(searchQuestions(items, '认了吧').length, 2);
  assert.equal(searchQuestions(items, '《十年》')[0].id, 'song');
});
test('fuzzy matching tolerates a typo and multiple unordered keywords', () => {
  assert.equal(searchQuestions(items, '陈奕讯在哪一年')[0].id, 'album');
  assert.equal(searchQuestions(items, '专辑 陈奕迅').length, 2);
});
test('answer text can also be searched; unrelated terms return no results', () => {
  assert.equal(searchQuestions(items, '陈小霞')[0].id, 'song');
  assert.equal(searchQuestions(items, '这道题根本不存在xyz').length, 0);
});
test('filters distinguish correct answers from elimination-only questions', () => {
  assert.equal(searchQuestions(items, '', 'correct').length, 2);
  assert.equal(searchQuestions(items, '', 'wrong').length, 1);
});
test('deployed data matches the Python schema and can all be searched', async () => {
  const real = JSON.parse(await readFile(new URL('../question_bank.json', import.meta.url), 'utf8'));
  const prepared = prepareQuestions(real);
  assert.ok(prepared.length > 0);
  for (const item of prepared) {
    assert.ok(searchQuestions(prepared, item.question).some(result => result.id === item.id));
    assert.ok(item.correctOptions.length + item.wrongOptions.length > 0);
  }
});
