import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--file1', type=str, required=True, help='第一个labels.npy')
parser.add_argument('--file2', type=str, required=True, help='第二个labels.npy')
args = parser.parse_args()

labels1 = np.load(args.file1, allow_pickle=True)
labels2 = np.load(args.file2, allow_pickle=True)

assert len(labels1) == len(labels2), f"两个npy长度不一致: {len(labels1)} vs {len(labels2)}"

diff_count = 0
for i, (a, b) in enumerate(zip(labels1, labels2)):
    diff = False
    for key in set(a.keys()).union(b.keys()):
        va = a.get(key)
        vb = b.get(key)
        if sorted(va) != sorted(vb):
            if not diff:
                print(f"Index {i} 不同：")
                diff = True
            print(f"  {key}: {va}  !=  {vb}")
    if diff:
        diff_count += 1
print(f"总共有 {diff_count} 处不同")

# python ./cmp_label_npy.py --file1 ./record_1127_1352/labels.npy --file2 ./record_1127_1414/labels.npy