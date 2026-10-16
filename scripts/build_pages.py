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
    shutil.copyfile(ROOT / 'question_bank.json', OUTPUT / 'question_bank.json')
    (OUTPUT / '.nojekyll').touch()
    print(f'Built {len(bank["questions"])} questions into {OUTPUT}')


if __name__ == '__main__':
    main()
