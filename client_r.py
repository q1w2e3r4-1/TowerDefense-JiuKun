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

for gid in range(100):
    os.system(f'python client.py  --action auto --game_id {gid} --record_dir {record_dir}')