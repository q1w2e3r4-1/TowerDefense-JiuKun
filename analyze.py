import os
import sys
import csv
from collections import defaultdict

def analyze_score_csv(record_dir):
    score_path = os.path.join(record_dir, 'score.csv')
    if not os.path.exists(score_path):
        print(f"score.csv not found in {record_dir}")
        return
    games = []
    score_pred_list = []
    score_game_list = []
    with open(score_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                games.append(row['game_id'])
                score_pred_list.append(float(row['score_pred']))
                score_game_list.append(float(row['score_game']))
            except Exception:
                continue
    n_games = len(games)
    avg_pred = sum(score_pred_list) / n_games if n_games else 0
    avg_game = sum(score_game_list) / n_games if n_games else 0
    print(f"分析文件: {score_path}")
    print(f"游戏局数: {n_games}")
    print(f"平均预测分: {avg_pred:.2f}")
    print(f"平均游戏得分: {avg_game:.2f}")



# 比较两个predict_scores.csv，输出每局每项分数的delta（相同则留空，否则显示delta）
def compare_predict_scores_csv(csv1, csv2):
    # 读取csv为dict: (game_id, round_id) -> {label: value}
    def read_predict_scores(path):
        data = {}
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                gid = int(row['game_id'])
                rid = int(row['round_id'])
                data[(gid, rid)] = {k: float(row[k]) for k in ['best_atk_spd', 'weak', 'resist', 'special_eff', 'slow_eff', 'occurrence']}
        return data

    d1 = read_predict_scores(csv1)
    d2 = read_predict_scores(csv2)
    labels = ['best_atk_spd', 'weak', 'resist', 'special_eff', 'slow_eff', 'occurrence']
    header = f"{'game_id':>7} | {'round':>5} | " + ' | '.join(f"{label:>12}" for label in labels)
    print(header)
    print('-' * len(header))
    all_keys = sorted(set(d1.keys()) | set(d2.keys()))
    for key in all_keys:
        row1 = d1.get(key, {})
        row2 = d2.get(key, {})
        out = [f"{key[0]:>7}", f"{key[1]:>5}"]
        for label in labels:
            v1 = row1.get(label)
            v2 = row2.get(label)
            if v1 is not None and v2 is not None:
                if abs(v1 - v2) < 1e-8:
                    out.append(f"{'':>12}")
                else:
                    out.append(f"{v1-v2:>12.4f}")
            else:
                out.append(f"{'':>12}")
        print(' | '.join(out))

def analyze_predict_scores(score_csv_path):
    # 读取分数
    scores = defaultdict(lambda: {k: [0.0, 0.0, 0.0] for k in [
        "best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence", "avg"]})
    valid_rounds = defaultdict(set)
    with open(score_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gid = int(row["game_id"])
            rid = int(row["round_id"]) - 1  # round_id: 1,2,3 -> idx: 0,1,2
            valid_rounds[gid].add(rid)
            for k in ["best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence", "avg"]:
                scores[gid][k][rid] = float(row[k])
    # 统计
    print(f"分析文件: {score_csv_path}")
    print(f"game_id | best_atk_spd | weak | resist | special_eff | slow_eff | occurrence | avg | 有效轮数")
    print("-"*100)
    max_gid = max(scores.keys()) if scores else -1
    total_games = max_gid + 1 if max_gid >= 0 else 0
    sum_avg = 0.0
    valid_games = 0
    sum_items = [0.0] * 7  # 各项分数累加
    for gid in range(max_gid+1):
        valid = valid_rounds.get(gid, set())
        if len(valid) < 3:
            # 缺轮，全部记0
            vals = [0.0]*7
        else:
            vals = [sum(scores[gid][k]) for k in ["best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence", "avg"]]
            sum_avg += vals[-1]
            for i in range(7):
                sum_items[i] += vals[i]
            valid_games += 1
        print(f"{gid:>7} | " + " | ".join(f"{v:>10.2f}" for v in vals) + f" | {len(valid)}")
    print("注：缺轮的game_id全部记为0分")
    # 汇总统计
    avg_score = sum_avg / valid_games if valid_games else 0.0
    avg_items = [x / valid_games if valid_games else 0.0 for x in sum_items]
    item_names = ["best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence", "avg"]
    print(f"游戏局数: {total_games}")
    print(f"有效局数: {valid_games}")
    print(f"平均预测分: {avg_score:.2f}")
    print("各项平均分:")
    for name, avg in zip(item_names, avg_items):
        print(f"  {name:>14}: {avg:.2f}")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        folder = sys.argv[1]
        score_csv = os.path.join(folder, "predict_scores.csv")
        record_csv = os.path.join(folder, "score.csv")
        if os.path.exists(score_csv):
            analyze_predict_scores(score_csv)
        elif os.path.exists(record_csv):
            analyze_score_csv(folder)
        else:
            print(f"{score_csv} 和 {record_csv} 都不存在，无法分析分数。")
    elif len(sys.argv) == 4 and sys.argv[1] == "--cmp":
        # 优先比较predict_scores.csv
        csv1 = os.path.join(sys.argv[2], 'predict_scores.csv')
        csv2 = os.path.join(sys.argv[3], 'predict_scores.csv')
        if os.path.exists(csv1) and os.path.exists(csv2):
            compare_predict_scores_csv(csv1, csv2)
        else:
            print('predict_scores.csv not found in one of the directories.')
    else:
        print("用法: python analyze.py <record_dir> 或 python analyze.py --cmp <dir_new> <dir_old>")
