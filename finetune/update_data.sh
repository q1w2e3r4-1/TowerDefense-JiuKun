set -x
python finetune/data_preprocess.py --input_dir /home/ws/data/game/train --output_dir /home/LLaMA-Factory/data --output_name kun.json
python finetune/data_preprocess.py --input_dir /home/ws/data/game/val --output_dir /home/LLaMA-Factory/data --output_name kun_val.json

# for debug
python finetune/data_preprocess.py --input_dir /home/ws/data/game/train --output_dir /home/ws/data/game/train --output_name kun.json
python finetune/data_preprocess.py --input_dir /home/ws/data/game/val --output_dir /home/ws/data/game/val --output_name kun_val.json