import os
import json
from openai import OpenAI
import numpy as np
from finetune.prompt import generate_reasoning_prompt
from predictor import LLMReasoning
predictor = LLMReasoning()

names = np.load("data/game/train/names.npy", allow_pickle=True)
labels = np.load("data/game/train/labels.npy", allow_pickle=True)
data = np.load("data/game/train/data.npy", allow_pickle=True)

L, R = (400, 800)
results_list = []
for i in range(L * 3, R * 3, 3):
  stories = []
  for j in range(3):
    print(f"Processing monster index: {i+j}")
    name = names[i+j]
    ground_truth = labels[i+j]
    stories.append(data[i + j])
    prompt = generate_reasoning_prompt(name, stories, ground_truth)
    # print(prompt)
    while True:
      try:
        res = predictor.infer(prompt)
        if(len(res) > 5000):
          print("too long!!!, retrying")
          continue
        results_list.append(res)
        print(f"Generated prompt for monster index {i+j}, prompt len: {len(prompt)}, res len: {len(res)}\n")
        break
      except Exception as e:
        print(f"Error during inference: {e}. Retrying...")

# 写入output.txt
with open(f"cot/output{L}-{R}.txt", "w", encoding="utf-8") as f:
  for item in results_list:
    f.write(json.dumps(item, ensure_ascii=False) + "\n")
