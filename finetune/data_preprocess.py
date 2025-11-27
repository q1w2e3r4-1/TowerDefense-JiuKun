
import argparse
import os
import numpy as np
import json
from prompt import SYSTEM_PROMPT, concat_input

def convert_to_llamafactory_jsonl(input_dir, output_dir, output_name="llamafactory.jsonl", cot=False):
    data_path = os.path.join(input_dir, "data.npy")
    names_path = os.path.join(input_dir, "names.npy")
    labels_path = os.path.join(input_dir, "labels.npy")
    output_path = os.path.join(output_dir, output_name)
    data = np.load(data_path, allow_pickle=True)
    names = np.load(names_path, allow_pickle=True)
    labels = np.load(labels_path, allow_pickle=True)
    if cot:
        cot_path = os.path.join(input_dir, "cot.npy")
        cot_lines = np.load(cot_path, allow_pickle=True)
        assert len(cot_lines) == len(labels), f"cot长度{len(cot_lines)}与labels不符{len(labels)}"
    
    assert len(data) == len(names) == len(labels)
    assert len(data) % 3 == 0, "data/labels/names长度必须为3的倍数"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Converting {len(data)} samples to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as fout:
        for i in range(0, len(data), 3):
            for k, ninp in enumerate([[data[i]], [data[i], data[i+1]], [data[i], data[i+1], data[i+2]]]):
                idx = i + k
                output_str = str(labels[idx])
                if cot:
                    output_str = f"[REASONING]\n{cot_lines[idx]}\n[ANSWER]\n{str(labels[idx])}"
                item = {
                    "instruction": SYSTEM_PROMPT.strip(),
                    "input": concat_input(names[idx], ninp),
                    "output": output_str
                }
                fout.write(json.dumps(item, ensure_ascii=False) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing data.npy, names.npy, labels.npy')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save output jsonl file')
    parser.add_argument('--output_name', type=str, default='llamafactory.jsonl', help='Output jsonl filename')
    parser.add_argument('--cot', action='store_true', help='If set, add COT reasoning to output')
    args = parser.parse_args()
    convert_to_llamafactory_jsonl(args.input_dir, args.output_dir, args.output_name, cot=args.cot)

if __name__ == '__main__':
    main()
    # python finetune/data_preprocess.py --input_dir /home/ws/data/game/train --output_dir /home/LLaMA-Factory/data --output_name kun.json
    # python finetune/data_preprocess.py --input_dir /home/ws/data/game/val --output_dir /home/LLaMA-Factory/data --output_name kun_val.json

    # for debug
    # python finetune/data_preprocess.py --input_dir /home/ws/data/game/train --output_dir /home/ws/data/game/train --output_name kun.json
    # python finetune/data_preprocess.py --input_dir /home/ws/data/game/val --output_dir /home/ws/data/game/val --output_name kun_val.json

    # with cot
    # python finetune/data_preprocess.py --input_dir /home/ws/cot --output_dir /home/ws/cot --output_name kun_cot.json --cot
    # python finetune/data_preprocess.py --input_dir /home/ws/cot --output_dir /home/LLaMA-Factory/data --output_name kun_cot.json --cot