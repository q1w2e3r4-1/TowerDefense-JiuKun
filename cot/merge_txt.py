import os

# 合并顺序
file_list = [
    "cot/output0-200.txt",
    "cot/output200-300.txt",
    "cot/output300-400.txt",
    "cot/output400-800.txt",
    "cot/output800-950.txt",
    "cot/output950-1000.txt",
    "cot/output1000-1200.txt"
]

import numpy as np

lines = []
total = 0
for fname in file_list:
    with open(fname, "r", encoding="utf-8") as fin:
        for line in fin:
            lines.append(line.rstrip('\n'))
            total += 1

out_path = "cot/cot.npy"
np.save(out_path, np.array(lines, dtype=object))
print(f"合并完成，共 {total} 行，输出到 {out_path}")
