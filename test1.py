import re
import os
import matplotlib.pyplot as plt

record_dir = "record_1128_1745"  # 你的文件夹路径
pattern = re.compile(r"shop size = (\d+)")

totals = []
builds = []

for fname in os.listdir(record_dir):
    if fname.endswith(".record"):
        path = os.path.join(record_dir, fname)
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = pattern.search(line)
                if m:
                    shop_size = m.groups()[0]
                    totals.append(int(shop_size))

print(totals)
from collections import Counter
cnt = Counter(totals)
print(cnt)