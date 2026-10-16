"""Package only the public search UI and question bank for GitHub Pages."""
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / '_site'
ASSETS = ('index.html', 'styles.css', 'app.mjs', 'search.mjs')


def main():
    bank = json.loads((ROOT / 'question_bank.json').read_text(encoding='utf-8'))
    if bank.get('version') != 1 or not isinstance(bank.get('questions'), dict):
        raise ValueError('Unsupported question bank format')
    OUTPUT.mkdir(exist_ok=True)
    allowed = {*ASSETS, 'question_bank.json', '.nojekyll'}
    if any(path.name not in allowed for path in OUTPUT.iterdir()):
        raise ValueError('_site contains unexpected files; refusing to publish them')
    for asset in ASSETS:
        shutil.copyfile(ROOT / 'site' / asset, OUTPUT / asset)
    # 网页只需要题目、选项和最新确认结果，不发布提交时间、累计统计或记录来源。
    public_bank = {'version': 1, 'questions': {}}
    for key, question in bank['questions'].items():
        attempts = [{field: attempt.get(field) for field in ('options', 'answer', 'correct')}
                    for attempt in question['attempts'] if isinstance(attempt.get('correct'), bool)]
        if attempts:
            public_bank['questions'][key] = {'question': question['question'], 'attempts': attempts}
    (OUTPUT / 'question_bank.json').write_text(
        json.dumps(public_bank, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8'
    )
    (OUTPUT / '.nojekyll').touch()
    print(f'Built {len(bank["questions"])} questions into {OUTPUT}')


if __name__ == '__main__':
    main()
