import json
import time
from checker import MonsterAttributeChecker
import subprocess
import requests
import time
import numpy as np

class Predictor:
    def infer(self, prompt, **kargs) -> str:
        raise NotImplementedError
    
class LLMPredictor(Predictor):
    def __init__(self, port=8000, host="127.0.0.1", extra_args=None):
        self.port = port
        self.host = host
        self.extra_args = extra_args or []
        self._wait_until_ready()

    def _wait_until_ready(self, timeout=60):
        url = f"http://{self.host}:{self.port}/v1/completions"
        for _ in range(timeout):
            try:
                resp = requests.post(url, timeout=2)
                if resp.status_code in (400, 200):
                    print("LLM server is ready.")
                    return
            except Exception:
                time.sleep(1)
        raise RuntimeError("LLM server did not start in time.")

    def infer(self, prompt, **kargs) -> str:
        url = f"http://{self.host}:{self.port}/v1/completions"
        payload = {
            "prompt": prompt,
            "max_tokens": kargs.get("max_tokens", 65536),
            "temperature": kargs.get("temperature", 0.7)
        }
        checker = MonsterAttributeChecker()
        for attempt in range(3):
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            result_text = resp.json()["choices"][0]["text"]
            ok, msg = checker.check(result_text)
            if ok:
                return result_text
            else:
                print(f"[LLMPredictor] Checker failed: {msg}. Retrying ({attempt+1}/3)...")
                time.sleep(1)
        print(f"[LLMPredictor] Checker failed after 3 attempts: {msg}")
        return None

class DummyPredictor(Predictor):
    def __init__(self, answer_dir):
        self.answer_dir = answer_dir  # 标准答案存放目录
        self.labels = np.load(f"{self.answer_dir}/labels.npy", allow_pickle=True)

    def infer(self, prompt, **kargs) -> str:
        game_id = kargs.get('game_id')
        round_id = kargs.get('round_id')
        idx = game_id * 3 + round_id - 1
        if idx < 0 or idx >= len(self.labels):
            raise IndexError(f"Invalid game_id/round_id: idx={idx}, total={len(self.labels)}")
        answer = self.labels[idx]
        return json.dumps(answer, ensure_ascii=False)