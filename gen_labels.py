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
pattern = re.compile(r"\[User Action\] \{'type': 'predict', 'label_pred': (\{.*?\})\}")
record_files = get_record_files(folder)
assert len(record_files) == 200, f"必须完成每局游戏，实际只有 {len(record_files)} 个记录文件"

all_attrs = []
for fpath in record_files:
    attrs = extract_attrs_from_file(fpath, pattern)
    assert len(attrs) == 3, f"文件 {fpath} 匹配到 {len(attrs)} 个pattern，需为3"
    all_attrs.extend(attrs)

assert len(all_attrs) == 600, f"总共应有600个匹配，实际{len(all_attrs)}"
# 保存为npy
out_path = os.path.join(folder, "monster_attrs.npy")
np.save(out_path, np.array(all_attrs, dtype=object))
print(f"已保存 {len(all_attrs)} 条属性到 {out_path}")
