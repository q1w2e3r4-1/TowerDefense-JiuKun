import json
import os
from predictor import LLMPredictor, DummyPredictor
from datetime import datetime
now = datetime.now()
date_str = now.strftime("%m%d_%H%M")
predict_dir = f'predict_{date_str}'

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
    dummy_result_str = dummy.infer(prompt, game_id=game_id, round_id=round_id)
    vllm_result = json.loads(vllm_result_str)
    dummy_result = json.loads(dummy_result_str)
    scores = score_prediction(vllm_result, dummy_result)
    print(f"LLMPredictor预测: {vllm_result}")
    print(f"DummyPredictor标答: {dummy_result}")
    print(f"各项得分: {scores}")
    return vllm_result, dummy_result, scores

# 批量评测与结果保存

def batch_eval(vllm: LLMPredictor, dummy: DummyPredictor, prompts, game_ids, round_ids, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    result_path = os.path.join(out_dir, "predict_results.csv")
    score_path = os.path.join(out_dir, "predict_scores.csv")
    with open(result_path, "w", encoding="utf-8") as f_res, open(score_path, "w", encoding="utf-8") as f_score:
        # 写表头
        f_res.write("game_id,round_id,vllm_pred,dummy_label\n")
        f_score.write("game_id,round_id,best_atk_spd,weak,resist,special_eff,slow_eff,occurrence,avg\n")
        for prompt, gid, rid in zip(prompts, game_ids, round_ids):
            vllm_pred, dummy_label, scores = compare_predictors(vllm, dummy, prompt, gid, rid)
            f_res.write(f"{gid},{rid},{json.dumps(vllm_pred, ensure_ascii=False)},{json.dumps(dummy_label, ensure_ascii=False)}\n")
            f_score.write(f"{gid},{rid},{scores['best_atk_spd']:.2f},{scores['weak']:.2f},{scores['resist']:.2f},{scores['special_eff']:.2f},{scores['slow_eff']:.2f},{scores['occurrence']:.2f},{scores['avg']:.2f}\n")

# 用法示例
if __name__ == "__main__":
    # 假设有 prompts, game_ids, round_ids 三个列表
    prompts = ["怪物描述1", "怪物描述2", "怪物描述3"]
    game_ids = [0, 0, 0]
    round_ids = [1, 2, 3]
    vllm = LLMPredictor()
    dummy = DummyPredictor(answer_dir="/path/to/label_dir")
    batch_eval(vllm, dummy, prompts, game_ids, round_ids, predict_dir)
