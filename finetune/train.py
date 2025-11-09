import argparse
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments

SYSTEM_PROMPT = """
You are a strategic game analyst for a tower defense game that unfolds over multiple rounds. Information about future enemies may appear early, woven into the lore across 1 to 3 interconnected stories. Your job is to extract precise attributes for a specific monster—which will be named by the user—by analyzing all provided story passages as a single context.

Given the target monster name and one or more narrative passages, carefully infer the following six attributes based only on explicit or strongly implied clues about that monster in any of the stories. Output your answer strictly in valid JSON format, with no additional text, explanation, or markdown.
"""
class NpyDataset(Dataset):
    def __init__(self, data_path, names_path, labels_path, tokenizer):
        self.data = np.load(data_path, allow_pickle=True)  # List[str]
        self.names = np.load(names_path, allow_pickle=True)  # List[str]
        self.labels = np.load(labels_path, allow_pickle=True)  # List[str]
        assert len(self.data) == len(self.labels) == len(self.names)
        self.tokenizer = tokenizer
        self.prompt = SYSTEM_PROMPT

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # 拼接prompt、data、names为输入，并限制最大长度
        input_text = self.prompt + str(self.data[idx]) + str(self.names[idx])
        input_ids = self.tokenizer.encode(
            input_text,
            add_special_tokens=False,
            max_length=2048,
            truncation=True
        )
        label_ids = self.tokenizer.encode(
            str(self.labels[idx]),
            add_special_tokens=False,
            max_length=2048,
            truncation=True
        )
        return {
            'input_ids': input_ids,
            'labels': label_ids
        }

def collate_fn(batch):
    input_ids = [torch.tensor(item['input_ids'], dtype=torch.long) for item in batch]
    labels = [torch.tensor(item['labels'], dtype=torch.long) for item in batch]
    # attention_mask: 非0为1，0为pad
    attention_mask = [torch.where(seq != 0, torch.ones_like(seq), torch.zeros_like(seq)) for seq in input_ids]
    # 构造最终labels
    final_labels = []
    for inp, lab in zip(input_ids, labels):
        # inp: [input_token1, ..., input_tokenN, name_token1, ...]
        # lab: [output_token1, ...]
        total_len = len(inp) + len(lab)
        label = torch.full((total_len,), -100, dtype=torch.long)
        label[len(inp):] = lab
        final_labels.append(label)
    max_len = 2048
    final_labels = torch.nn.utils.rnn.pad_sequence(final_labels, batch_first=True, padding_value=-100)
    final_labels = final_labels[:, :max_len]
    # attention_mask也补齐
    attention_mask = torch.nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0)
    attention_mask = attention_mask[:, :max_len]
    # input_ids也补齐（拼接output部分）
    final_input_ids = []
    for inp, lab in zip(input_ids, labels):
        final_input_ids.append(torch.cat([inp, lab]))
    final_input_ids = torch.nn.utils.rnn.pad_sequence(final_input_ids, batch_first=True, padding_value=0)
    final_input_ids = final_input_ids[:, :max_len]
    return {
        'input_ids': final_input_ids,
        'attention_mask': attention_mask,
        'labels': final_labels,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True, help='Parent directory containing data.npy, names.npy, labels.npy')
    parser.add_argument('--val_dir', type=str, default=None, help='Validation set parent directory (optional)')
    parser.add_argument('--model_path', type=str, required=True, help='Pretrained model name or path')
    parser.add_argument('--output_dir', type=str, default='./output', help='Output directory')
    parser.add_argument('--batch_size', type=int, default=1)
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--lr', type=float, default=5e-5)
    args = parser.parse_args()

    data_path = f"{args.data_dir}/data.npy"
    names_path = f"{args.data_dir}/names.npy"
    labels_path = f"{args.data_dir}/labels.npy"

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(args.model_path)

    train_dataset = NpyDataset(data_path, names_path, labels_path, tokenizer)

    eval_dataset = None
    if args.val_dir:
        val_data_path = f"{args.val_dir}/data.npy"
        val_names_path = f"{args.val_dir}/names.npy"
        val_labels_path = f"{args.val_dir}/labels.npy"
        eval_dataset = NpyDataset(val_data_path, val_names_path, val_labels_path, tokenizer)

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        learning_rate=args.lr,
        save_strategy='epoch',
        logging_steps=10,
        fp16=torch.cuda.is_available(),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=collate_fn,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.output_dir)

if __name__ == '__main__':
    main()
