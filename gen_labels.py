import re
import sys
import os
import numpy as np

def get_record_files(folder):
    files = []
    for fname in os.listdir(folder):
        if fname.endswith('.record'):
            fpath = os.path.join(folder, fname)
            files.append((os.path.getctime(fpath), fpath))
    files.sort()  # 按创建时间排序
    return [f[1] for f in files]

def extract_attrs_from_file(fpath, pattern):
    results = []
    with open(fpath, 'r', encoding='utf-8') as f:
        for line in f:
            match = pattern.search(line)
            if match:
                results.append(match.group(1))
    return results

if len(sys.argv) != 2:
    print(f"用法: python extract_monster_attrs.py <record_folder>")
    sys.exit(1)

folder = sys.argv[1]
if folder.startswith("record_"):
    # 生成test_label（即未公开数据的label）
    pattern = re.compile(r"\[User Action\] \{'type': 'predict', 'label_pred': (\{.*?\})\}")
    record_files = get_record_files(folder)
    assert len(record_files) == 200, f"必须完成每局游戏，实际只有 {len(record_files)} 个记录文件"

    all_attrs = []
    for fpath in record_files:
        attrs = extract_attrs_from_file(fpath, pattern)
        assert len(attrs) == 3, f"文件 {fpath} 匹配到 {len(attrs)} 个pattern，需为3"
        for a in attrs:
            # 直接用eval转为dict（假定输入可信）
            all_attrs.append(eval(a))

    assert len(all_attrs) == 600, f"总共应有600个匹配，实际{len(all_attrs)}"
    # 保存为npy
    out_path = os.path.join(folder, "labels.npy")
    np.save(out_path, np.array(all_attrs, dtype=object))
    print(f"已保存 {len(all_attrs)} 条属性到 {out_path}")
elif folder.startswith("predict_"):
    # 生成val_label（val文件夹的预测label）
    # 补全缺失
    import re
    pred_csv = os.path.join(folder, "predict_results.csv")
    assert os.path.exists(pred_csv), f"找不到 {pred_csv}"
    total_games = 200
    total_rounds = 3
    total_labels = total_games * total_rounds
    all_attrs = [None] * total_labels
    # 正则非贪婪提取每行的game_id, round_id, vllm_pred（第一个大括号内容）
    line_pattern = re.compile(r'^(\d+),(\d+),({.*?})')
    with open(pred_csv, encoding="utf-8") as f:
        for line in f:
            m = line_pattern.match(line)
            if not m:
                continue
            gid = int(m.group(1))
            rid = int(m.group(2))
            idx = gid * total_rounds + (rid - 1)
            vllm_pred_str = m.group(3)
            try:
                label_dict = eval(vllm_pred_str)
            except Exception:
                label_dict = None
            all_attrs[idx] = label_dict
    empty_label = {
        "best_atk_spd": [],
        "weak": [],
        "resist": [],
        "special_eff": [],
        "slow_eff": [],
        "occurrence": []
    }
    fill_count = 0
    for i in range(total_labels):
        if not isinstance(all_attrs[i], dict):
            all_attrs[i] = empty_label.copy()
            fill_count += 1
    print(f"填充了 {fill_count} 个缺失的标签")
    # 保存为npy
    out_path = os.path.join(folder, "labels.npy")
    np.save(out_path, np.array(all_attrs, dtype=object))
    print(f"已保存 {len(all_attrs)} 条属性到 {out_path}")
else:
    print(f"目录名应以 record_ 或 predict_ 开头")
    sys.exit(1)