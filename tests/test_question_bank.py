import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import dailyMission as mission
from question_bank import QuestionBank


OPTIONS = [('a1', 'First album'), ('a2', 'Second album'), ('a3', 'Third album'), ('a4', 'Fourth album')]


def page(answered=10, correct=6, participated=0, options=OPTIONS):
    return (
        f'<div id="inner">({participated}/1)</div>'
        f'<div>累计答题：<span>{answered}</span> 累计答对: <span>{correct}</span></div>'
        '<font><b>【题目】</b> Which album?</font>'
        + ''.join(f'<div class="qs_option"><input id="{label}">{label}. {text}</div>' for label, text in options)
    )


class ImmediateWait:
    def __init__(self, driver, timeout):
        self.driver = driver

    def until(self, condition):
        result = condition(self.driver)
        if not result:
            raise mission.TimeoutException()
        return result


class Element:
    def __init__(self, driver, label):
        self.driver = driver
        self.label = label
        self.text = f'({driver.participated}/1)'

    def is_displayed(self):
        return True

    def is_enabled(self):
        return True

    def click(self):
        if self.label == 'submit':
            self.driver.submitted += 1
            if self.driver.result is not None:
                self.driver.participated = 1
                self.driver.page_source = page(11, 6 + self.driver.result, 1)
        else:
            self.driver.selected = self.label


class Driver:
    def __init__(self, result=True, options=OPTIONS):
        self.result = result
        self.participated = 0
        self.submitted = 0
        self.selected = None
        self.page_source = page(options=options)

    def get(self, url):
        pass

    def find_element(self, by, value):
        return Element(self, 'submit' if by == mission.By.XPATH else value)


class QuestionBankTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bank = QuestionBank(Path(self.temp.name) / 'bank.json')
        self.wait = patch.object(mission, 'WebDriverWait', ImmediateWait)
        self.wait.start()
        self.addCleanup(self.wait.stop)
        mission._api_call_count = 0

    def remember(self, label, correct):
        attempt = self.bank.record('Which album?', OPTIONS, label, 'api', [10, 6])
        self.bank.resolve(attempt, [11, 6 + correct])
        return attempt

    def test_correct_answer_reused_after_option_reordering_without_api(self):
        self.remember('a2', True)
        reordered = [('a1', 'Second album'), ('a2', 'First album'), *OPTIONS[2:]]
        driver = Driver(options=reordered)
        # 已达到 API 上限时，仍允许题库命中。
        mission._api_call_count = 3
        with patch.object(mission, 'get_answer_from_api') as api:
            attempt = mission.answer_question(driver, 0, bank=self.bank)
        api.assert_not_called()
        self.assertEqual(driver.selected, 'a1')
        self.assertEqual(attempt['answer'], 'Second album')
        self.assertEqual(attempt['source'], 'question_bank')

    def test_wrong_answer_excluded_from_prompt_and_fallback(self):
        self.remember('a1', False)
        driver = Driver()
        with patch.object(mission, 'get_answer_from_api', return_value='a1') as api:
            attempt = mission.answer_question(driver, 0, bank=self.bank)
        prompt = api.call_args.args[0]
        self.assertNotIn('a1.', prompt)
        self.assertNotIn('First album', prompt)
        self.assertIn('a2. Second album', prompt)
        self.assertEqual(driver.selected, 'a2')
        self.assertEqual(attempt['source'], 'fallback')

    def test_unseen_question_uses_original_prompt_and_api(self):
        driver = Driver()
        original_prompt = mission.build_prompt(driver)
        with patch.object(mission, 'get_answer_from_api', return_value='a4') as api:
            attempt = mission.answer_question(driver, 0, bank=self.bank)
        api.assert_called_once_with(original_prompt)
        self.assertEqual(driver.selected, 'a4')
        self.assertEqual(attempt['source'], 'api')
        self.assertEqual(attempt['correct'], None)

    def test_single_remaining_option_still_calls_api(self):
        for label, _ in OPTIONS[:-1]:
            self.remember(label, False)
        with patch.object(mission, 'get_answer_from_api', return_value='a4') as api:
            mission.answer_question(Driver(), 0, bank=self.bank)
        api.assert_called_once()
        self.assertIn('a4.', api.call_args.args[0])
        self.assertNotIn('a3.', api.call_args.args[0])

    def test_all_options_wrong_stops_without_api_or_submission(self):
        for label, _ in OPTIONS:
            self.remember(label, False)
        driver = Driver()
        with patch.object(mission, 'get_answer_from_api') as api:
            self.assertIsNone(mission.answer_question(driver, 0, bank=self.bank))
        api.assert_not_called()
        self.assertEqual(driver.submitted, 0)

    def test_latest_confirmed_result_overrides_older_result(self):
        self.remember('a1', True)
        self.remember('a1', False)
        self.bank.record('Which album?', OPTIONS, 'a1', 'api', [11, 7])
        label, remaining = self.bank.lookup('Which album?', OPTIONS)
        self.assertIsNone(label)
        self.assertNotIn(OPTIONS[0], remaining)

    def test_different_option_set_does_not_reuse_answer(self):
        self.remember('a1', True)
        changed = [*OPTIONS[:-1], ('a4', 'Different album')]
        self.assertEqual(self.bank.lookup('Which album?', changed), (None, changed))

    def test_unknown_results_never_mark_answer_wrong(self):
        for after in (None, [10, 6], [12, 7], [11, 8], [11, 5]):
            with self.subTest(after=after):
                attempt = self.bank.record('Which album?', OPTIONS, 'a1', 'api', [10, 6])
                self.assertIsNone(self.bank.resolve(attempt, after))
        self.assertEqual(self.bank.lookup('Which album?', OPTIONS), (None, OPTIONS))

    def test_results_persist_and_are_available_to_next_account(self):
        self.remember('a1', False)
        self.remember('a2', True)
        restored = QuestionBank(self.bank.path)
        self.assertEqual(restored.lookup('Which album?', OPTIONS), ('a2', OPTIONS[1:]))
        entry = next(iter(json.loads(self.bank.path.read_text())['questions'].values()))
        self.assertEqual(len(entry['attempts']), 2)
        self.assertEqual(list(self.bank.path.parent.glob('*.tmp')), [])

    def test_corrupt_file_is_not_overwritten(self):
        original = self.bank.path
        # 使用临时测试文件，不涉及用户题库。
        original.write_text('{broken')
        with self.assertRaises(json.JSONDecodeError):
            QuestionBank(original)
        self.assertEqual(original.read_text(), '{broken')

    def test_stats_accept_nested_markup_and_missing_is_unknown(self):
        self.assertEqual(mission.read_answer_stats(page()), [10, 6])
        self.assertIsNone(mission.read_answer_stats('<div>请登录</div>'))

    def test_option_prefixes_are_removed_but_english_words_are_kept(self):
        driver = Driver()
        driver.page_source = driver.page_source.replace('a1. First', 'A. First').replace('a2. Second', 'Second')
        self.assertEqual(mission.extract_question(driver)[1], OPTIONS)

    def test_api_budget_blocks_uncached_questions(self):
        mission._api_call_count = 3
        driver = Driver()
        with patch.object(mission, 'get_answer_from_api') as api:
            self.assertIsNone(mission.answer_question(driver, 0, bank=self.bank))
        api.assert_not_called()
        self.assertEqual(driver.submitted, 0)

    def test_submission_click_exception_remains_unknown(self):
        driver = Driver(result=None)
        real_click = Element.click

        def click(element):
            if element.label == 'submit':
                raise RuntimeError('connection lost')
            real_click(element)

        with patch.object(Element, 'click', click), \
                patch.object(mission, 'get_answer_from_api', return_value='a2'):
            attempt = mission.answer_question(driver, 0, bank=self.bank)
        self.assertIsNone(self.bank.resolve(attempt, mission.read_answer_stats(driver.page_source)))
        self.assertEqual(self.bank.lookup('Which album?', OPTIONS), (None, OPTIONS))

    def test_whole_loop_records_correct_wrong_and_unknown_results(self):
        for result in (True, False, None):
            with self.subTest(result=result):
                bank = QuestionBank(Path(self.temp.name) / f'{result}.json')
                driver = Driver(result=result)
                with patch.object(mission, 'QuestionBank', return_value=bank), \
                        patch.object(mission, 'get_answer_from_api', return_value='a2'):
                    mission.question(driver)
                attempt = next(iter(bank.data['questions'].values()))['attempts'][0]
                self.assertIs(attempt['correct'], result)
                self.assertEqual(driver.submitted, 1)


if __name__ == '__main__':
    unittest.main()
