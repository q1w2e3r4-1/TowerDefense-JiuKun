set -x
# python finetune/data_preprocess.py --input_dir /home/ws/data/game/merge --output_dir /home/LLaMA-Factory/data --output_name kun.json

# # for debug
# python finetune/data_preprocess.py --input_dir /home/ws/data/game/merge --output_dir /home/ws/data/game/merge --output_name kun.json

# cot
python finetune/data_preprocess.py --input_dir /home/ws/cot --output_dir /home/ws/cot --output_name kun_cot.json --cot
python finetune/data_preprocess.py --input_dir /home/ws/cot --output_dir /home/LLaMA-Factory/data --output_name kun_cot.json --cot