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
        # 查询/v1/models获取model名称
        url = f"http://{self.host}:{self.port}/v1/models"
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            models = resp.json().get("data", [])
            if models and "id" in models[0]:
                lora_model = None
                normal_model = None
                for m in models:
                    if "id" in m:
                        if "lora" in m["id"].lower():
                            lora_model = m["id"]
                        if not normal_model:
                            normal_model = m["id"]
                if lora_model:
                    self.model_name = lora_model
                    print(f"Auto-detected lora model name: {self.model_name}")
                elif normal_model:
                    self.model_name = normal_model
                    print(f"Auto-detected model name: {self.model_name}")
            else:
                raise RuntimeError("No model id found in /v1/models response.")
        except Exception as e:
            print(f"Failed to get model name from /v1/models: {e}")
            self.model_name = None

    def get_model_name(self):
        return self.model_name
    
    def _wait_until_ready(self, timeout=60):
        url = f"http://{self.host}:{self.port}/health"
        for _ in range(timeout):
            try:
                resp = requests.get(url, timeout=2)
                if resp.status_code == 200:
                    print("LLM server is ready.")
                    return
            except Exception:
                time.sleep(1)
        raise RuntimeError("LLM server did not start in time.")

    def infer(self, prompt, **kargs) -> str:
        url = f"http://{self.host}:{self.port}/v1/chat/completions"
        if not self.model_name:
            raise RuntimeError("Model name not set. Cannot call chat/completions.")
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": kargs.get("max_tokens", 8192),
            "temperature": kargs.get("temperature", 0.7),
            "chat_template_kwargs": {"enable_thinking": False}
        }
        checker = MonsterAttributeChecker()
        fallback_ans = None
        for attempt in range(3):
            resp = requests.post(url, json=payload)
            resp.raise_for_status()
            result = resp.json()["choices"][0]
            # chat/completions接口返回的是message.content
            result_text = result["message"]["content"] if "message" in result else result.get("text", "")
            result_text = result_text.replace("'", '"')
            ok, msg = checker.check(result_text)
            if ok:
                return result_text
            else:
                ok1, msg1 = checker.check(result_text, level=1)
                if ok1:
                    fallback_ans = result_text
                print(f"[LLMPredictor] Checker failed: {msg}. Retrying ({attempt+1}/3)...")
                time.sleep(1)
        print(f"[LLMPredictor] Checker failed after 3 attempts: {msg}, fallback to {fallback_ans}")
        return fallback_ans
    
    

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