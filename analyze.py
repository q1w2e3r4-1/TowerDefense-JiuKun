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


def compare_score_csv(dir_new, dir_old):
    def read_scores(d):
        path = os.path.join(d, 'score.csv')
        scores = {}
        if not os.path.exists(path):
            print(f"score.csv not found in {d}")
            return scores
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    gid = row['game_id']
                    scores[gid] = {
                        'score_pred': float(row['score_pred']),
                        'score_game': float(row['score_game'])
                    }
                except Exception:
                    continue
        return scores

    scores_new = read_scores(dir_new)
    scores_old = read_scores(dir_old)
    all_gids = set(scores_new.keys()) | set(scores_old.keys())
    print(f"对比 {dir_new}/score.csv 与 {dir_old}/score.csv")
    print(f"共计对局: {len(all_gids)}")
    print(f"game_id | new_pred | old_pred | Δpred | 状态_pred | new_game | old_game | Δgame | 状态_game")
    print("-"*100)
    for gid in sorted(all_gids, key=lambda x: int(x)):
        n = scores_new.get(gid)
        o = scores_old.get(gid)
        if n and o:
            delta_pred = n['score_pred'] - o['score_pred']
            delta_game = n['score_game'] - o['score_game']
            status_pred = "提升" if delta_pred > 0 else ("下降" if delta_pred < 0 else "持平")
            status_game = "提升" if delta_game > 0 else ("下降" if delta_game < 0 else "持平")
            print(f"{gid:>7} | {n['score_pred']:^8.2f} | {o['score_pred']:^8.2f} | {delta_pred:^6.2f} | {status_pred:^8} | {n['score_game']:^8.2f} | {o['score_game']:^8.2f} | {delta_game:^6.2f} | {status_game:^8}")
        elif n and not o:
            print(f"{gid:>7} | {n['score_pred']:^8.2f} | {'-':^8} | {'-':^6} | {'新增':^8} | {n['score_game']:^8.2f} | {'-':^8} | {'-':^6} | {'新增':^8}")
        elif o and not n:
            print(f"{gid:>7} | {'-':^8} | {o['score_pred']:^8.2f} | {'-':^6} | {'移除':^8} | {'-':^8} | {o['score_game']:^8.2f} | {'-':^6} | {'移除':^8}")

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
    for gid in range(max_gid+1):
        valid = valid_rounds.get(gid, set())
        if len(valid) < 3:
            # 缺轮，全部记0
            vals = [0.0]*7
        else:
            vals = [sum(scores[gid][k]) for k in ["best_atk_spd", "weak", "resist", "special_eff", "slow_eff", "occurrence", "avg"]]
            sum_avg += vals[-1]
            valid_games += 1
        print(f"{gid:>7} | " + " | ".join(f"{v:>10.2f}" for v in vals) + f" | {len(valid)}")
    print("注：缺轮的game_id全部记为0分")
    # 汇总统计
    avg_score = sum_avg / valid_games if valid_games else 0.0
    print(f"游戏局数: {total_games}")
    print(f"有效局数: {valid_games}")
    print(f"平均预测分: {avg_score:.2f}")

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
        compare_score_csv(sys.argv[2], sys.argv[3])
    else:
        print("用法: python analyze.py <record_dir> 或 python analyze.py --cmp <dir_new> <dir_old>")
