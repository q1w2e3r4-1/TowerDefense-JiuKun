import os
from datetime import datetime
now = datetime.now()
date_str = now.strftime("%m%d_%H%M")

# 创建记录目录和score.csv文件，并写入标题
record_dir = f'record_{date_str}'
os.makedirs(record_dir, exist_ok=True)
score_csv_path = os.path.join(record_dir, 'score.csv')
with open(score_csv_path, 'w', encoding='utf-8') as f:
    f.write('game_id,score_pred,score_game\n')

# for gid in range(60, 61):
#     print(f'Running game_id: {gid}')
#     # os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir}')
#     os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir} --label_dir ./data/game/lora-4B')
import threading

def func1():
    for gid in range(0, 100):
        print(f'Running game_id: {gid}')
        os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir}')
        # os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir} --label_dir ./data/game/lora-4B')
def func2():
    for gid in range(100, 200):
        print(f'Running game_id: {gid}')
        os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir}')
        # os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir} --label_dir ./data/game/lora-4B')
t1 = threading.Thread(target=func1)
t2 = threading.Thread(target=func2)
t1.start()
t2.start()
t1.join()
t2.join()
