import json
import os
from predictor import LLMPredictor, DummyPredictor
from datetime import datetime
now = datetime.now()
date_str = now.strftime("%m%d_%H%M")
predict_dir = f'predict_{date_str}'
ERR_CNT = 0

def score_prediction(pred: dict, label: dict) -> dict:
    keys = ["best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence"]
    scores = {}
    for key in keys:
        pred_set = set(pred.get(key, []))
        label_set = set(label.get(key, []))
        intersection = len(pred_set & label_set)
        union = len(pred_set | label_set)
        score = (intersection / union if union > 0 else 1.0) * 100
        scores[key] = score
    scores['avg'] = sum(scores.values()) / len(keys)
    return scores

def score_game(pred_list, label_list):
    # pred_list, label_list: List[dict]，每局三轮
    assert len(pred_list) == len(label_list)
    total = 0
    for pred, label in zip(pred_list, label_list):
        total += score_prediction(pred, label)['avg']
    return total  # 范围[0, 300]

def compare_predictors(vllm: LLMPredictor, dummy: DummyPredictor, prompt, game_id, round_id):
    vllm_result_str = vllm.infer(prompt, game_id=game_id, round_id=round_id)
    if vllm_result_str is None:
        return None, None, None
    vllm_result_str = vllm_result_str.replace("'", '"')
    dummy_result_str = dummy.infer(prompt, game_id=game_id, round_id=round_id)
    vllm_result = json.loads(vllm_result_str)
    dummy_result = json.loads(dummy_result_str)
    scores = score_prediction(vllm_result, dummy_result)
    # print(f"LLMPredictor预测: {vllm_result}")
    # print(f"DummyPredictor标答: {dummy_result}")
    print(f"各项得分: {scores}")
    return vllm_result, dummy_result, scores

# 批量评测与结果保存

def batch_eval(vllm: LLMPredictor, dummy: DummyPredictor, prompts, game_ids, round_ids, out_dir):
    global ERR_CNT
    os.makedirs(out_dir, exist_ok=True)
    model_name = vllm.get_model_name()
    with open(os.path.join(out_dir, "model_name.txt"), "w", encoding="utf-8") as f_model_name:
        f_model_name.write(model_name if model_name else "Unknown Model")
    result_path = os.path.join(out_dir, "predict_results.csv")
    score_path = os.path.join(out_dir, "predict_scores.csv")
    with open(result_path, "w", encoding="utf-8") as f_res, open(score_path, "w", encoding="utf-8") as f_score:
        # 写表头
        f_res.write("game_id,round_id,vllm_pred,dummy_label\n")
        f_score.write("game_id,round_id,best_atk_spd,weak,resist,special_eff,slow_eff,occurrence,avg\n")
        for prompt, gid, rid in zip(prompts, game_ids, round_ids):
            print(f"Evaluating Game {gid}, Round {rid}...")
            vllm_pred, dummy_label, scores = compare_predictors(vllm, dummy, prompt, gid, rid)
            if scores is None: 
                print(f"Skipping Game {gid}, Round {rid} due to invalid prediction.")
                ERR_CNT += 1
                continue
            f_res.write(f"{gid},{rid},{json.dumps(vllm_pred, ensure_ascii=False)},{json.dumps(dummy_label, ensure_ascii=False)}\n")
            f_score.write(f"{gid},{rid},{scores['best_atk_spd']:.2f},{scores['weak']:.2f},{scores['resist']:.2f},{scores['special_eff']:.2f},{scores['slow_eff']:.2f},{scores['occurrence']:.2f},{scores['avg']:.2f}\n")

# 用法示例
if __name__ == "__main__":
    import numpy as np
    from finetune.prompt import generate_system_prompt

    # names = np.load("data/game/val/names.npy", allow_pickle=True)
    # labels = np.load("data/game/val/labels.npy", allow_pickle=True)
    # data = np.load("data/game/val/data.npy", allow_pickle=True)

    names = np.load("data/data/names.npy", allow_pickle=True)
    labels = np.load("data/data/labels.npy", allow_pickle=True)
    data = np.load("data/data/data.npy", allow_pickle=True)

    prompts = []
    game_ids = []
    round_ids = []
    L, R = (0, 200)
    for i in range(L * 3, R * 3, 3):
        stories = []
        for j in range(3):
            name = names[i + j]
            stories.append(data[i + j])
            prompts.append(generate_system_prompt(name, stories))
            game_ids.append(i // 3)
            round_ids.append(j + 1)

    vllm = LLMPredictor()
    # dummy = DummyPredictor(answer_dir="data/game/val")
    dummy = DummyPredictor(answer_dir="data/data")
    batch_eval(vllm, dummy, prompts, game_ids, round_ids, predict_dir)
    print(f"Total invalid predictions skipped: {ERR_CNT}")
