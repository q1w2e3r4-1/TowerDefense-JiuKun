import re
import os
import matplotlib.pyplot as plt

record_dir = "record_1128_1344"  # 你的文件夹路径
pattern = re.compile(r"Round over\. Used money: (\d+) / (\d+), Build (\d+) towers\.")

totals = []
builds = []

for fname in os.listdir(record_dir):
    if fname.endswith(".record"):
        path = os.path.join(record_dir, fname)
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = pattern.search(line)
                if m:
                    used, total, build = m.groups()
                    totals.append(int(total))
                    builds.append(int(build))
                    print(f"{fname}: used={used}, total={total}, build={build}")

# 绘制散点图并保存为png文件
if totals and builds:
    plt.scatter(totals, builds, alpha=0.7)
    plt.xlabel('Total Money')
    plt.ylabel('Build Towers')
    plt.title('Total vs Build Scatter Plot')
    plt.grid(True)
    plt.savefig('total_vs_build2.png')
    plt.close()