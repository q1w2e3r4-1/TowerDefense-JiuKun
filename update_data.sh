set -x
python finetune/data_preprocess.py --input_dir /home/ws/data/game/merge --output_dir /home/LLaMA-Factory/data --output_name kun.json

# for debug
python finetune/data_preprocess.py --input_dir /home/ws/data/game/merge --output_dir /home/ws/data/game/merge --output_name kun.json