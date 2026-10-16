"""持久化答题记录；只复用网站确认过的答案。"""

import hashlib
import json
import os
from pathlib import Path
import tempfile
from datetime import datetime, timezone
from uuid import uuid4


DEFAULT_PATH = Path(__file__).resolve().with_name("question_bank.json")


def normalize(text):
    return " ".join(text.split())


def question_key(question, options):
    # 标签/选项顺序可能改变；选项集合不同则视为另一题，避免同名题误匹配。
    identity = [normalize(question), sorted(normalize(text) for _, text in options)]
    return hashlib.sha256(json.dumps(identity, ensure_ascii=False).encode("utf-8")).hexdigest()


class QuestionBank:
    def __init__(self, path=DEFAULT_PATH):
        self.path = Path(path)
        if self.path.exists():
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
            if self.data.get("version") != 1 or not isinstance(self.data.get("questions"), dict):
                raise ValueError("题库格式不受支持，请检查 question_bank.json")
        else:
            self.data = {"version": 1, "questions": {}}

    def lookup(self, question, options):
        entry = self.data["questions"].get(question_key(question, options), {})
        known = {}
        for attempt in entry.get("attempts", []):
            if isinstance(attempt.get("correct"), bool):
                known[normalize(attempt["answer"])] = attempt["correct"]
        correct_label = next(
            (label for label, text in options if known.get(normalize(text)) is True), None
        )
        remaining = [(label, text) for label, text in options if known.get(normalize(text)) is not False]
        return correct_label, remaining

    def record(self, question, options, label, source, before):
        key = question_key(question, options)
        entry = self.data["questions"].setdefault(key, {"question": question, "attempts": []})
        attempt = {
            "id": uuid4().hex,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "options": dict(options),
            "label": label,
            "answer": dict(options)[label],
            "source": source,
            "correct": None,
            "result": "unconfirmed",
            "before": before,
        }
        entry["attempts"].append(attempt)
        self.save()
        return attempt

    def resolve(self, attempt, after):
        before = attempt["before"]
        attempt["after"] = after
        # 必须确认只完成了一题；页面缺少统计、计数未更新或跳变都不能判错。
        if before is not None and after is not None and after[0] - before[0] == 1:
            delta = after[1] - before[1]
            if delta in (0, 1):
                attempt["correct"] = bool(delta)
        attempt["result"] = "confirmed" if attempt["correct"] is not None else "unconfirmed"
        self.save()
        return attempt["correct"]

    def save(self):
        # 同目录临时文件 + 原子替换，避免进程中断时留下半截 JSON。
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                         prefix=self.path.name + ".", suffix=".tmp", delete=False) as handle:
            temporary = handle.name
            try:
                json.dump(self.data, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            except BaseException:
                os.unlink(temporary)
                raise
        try:
            os.replace(temporary, self.path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
