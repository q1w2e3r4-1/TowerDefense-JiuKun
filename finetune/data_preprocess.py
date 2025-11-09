
import argparse
import os
import numpy as np
import json

SYSTEM_PROMPT = """
You are a strategic game analyst for a tower defense game that unfolds over multiple rounds. Information about future enemies may appear early, woven into the lore across 1 to 3 interconnected stories. Your job is to extract precise attributes for a specific monster—which will be named by the user—by analyzing all provided story passages as a single context.

Given the target monster name and one or more narrative passages, carefully infer the following six attributes based only on explicit or strongly implied clues about that monster in any of the stories. Output your answer strictly in valid JSON format, with no additional text, explanation, or markdown.
"""

def convert_to_llamafactory_jsonl(input_dir, output_dir, output_name="llamafactory.jsonl"):
    data_path = os.path.join(input_dir, "data.npy")
    names_path = os.path.join(input_dir, "names.npy")
    labels_path = os.path.join(input_dir, "labels.npy")
    output_path = os.path.join(output_dir, output_name)
    data = np.load(data_path, allow_pickle=True)
    names = np.load(names_path, allow_pickle=True)
    labels = np.load(labels_path, allow_pickle=True)
    assert len(data) == len(names) == len(labels)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Converting {len(data)} samples to {output_path}")
    with open(output_path, 'w', encoding='utf-8') as fout:
        for d, n, l in zip(data, names, labels):
            item = {
                "instruction": SYSTEM_PROMPT.strip(),
                "input": str(d) + str(n),
                "output": str(l)
            }
            fout.write(json.dumps(item, ensure_ascii=False) + '\n')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_dir', type=str, required=True, help='Directory containing data.npy, names.npy, labels.npy')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save output jsonl file')
    parser.add_argument('--output_name', type=str, default='llamafactory.jsonl', help='Output jsonl filename')
    args = parser.parse_args()
    convert_to_llamafactory_jsonl(args.input_dir, args.output_dir, args.output_name)

if __name__ == '__main__':
    main()
    # python finetune/data_preprocess.py --input_dir /home/ws/data/game/train --output_dir /home/LLaMA-Factory/data --output_name kun.json
    # python finetune/data_preprocess.py --input_dir /home/ws/data/game/val --output_dir /home/LLaMA-Factory/data --output_name kun_val.json