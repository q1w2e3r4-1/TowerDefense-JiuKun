import argparse
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments

class NpyDataset(Dataset):
    def __init__(self, data_path, names_path, labels_path, tokenizer):
        self.data = np.load(data_path, allow_pickle=True)  # List[str]
        self.names = np.load(names_path, allow_pickle=True)  # List[str]
        self.labels = np.load(labels_path, allow_pickle=True)  # List[str]
        assert len(self.data) == len(self.labels) == len(self.names)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # data, names, labels均为字符串，全部编码后拼接
        data_ids = self.tokenizer.encode(str(self.data[idx]), add_special_tokens=False)
        names_ids = self.tokenizer.encode(str(self.names[idx]), add_special_tokens=False)
        input_ids = data_ids + names_ids
        label_ids = self.tokenizer.encode(str(self.labels[idx]), add_special_tokens=False)
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
    final_labels = torch.nn.utils.rnn.pad_sequence(final_labels, batch_first=True, padding_value=-100)
    # attention_mask也补齐
    attention_mask = torch.nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0)
    # input_ids也补齐（拼接output部分）
    final_input_ids = []
    for inp, lab in zip(input_ids, labels):
        final_input_ids.append(torch.cat([inp, lab]))
    final_input_ids = torch.nn.utils.rnn.pad_sequence(final_input_ids, batch_first=True, padding_value=0)
    return {
        'input_ids': final_input_ids,
        'attention_mask': attention_mask,
        'labels': final_labels,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_dir', type=str, required=True, help='Parent directory containing data.npy, names.npy, labels.npy')
    parser.add_argument('--model_name_or_path', type=str, required=True, help='Pretrained model name or path')
    parser.add_argument('--output_dir', type=str, default='./output', help='Output directory')
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--lr', type=float, default=5e-5)
    args = parser.parse_args()

    data_path = f"{args.data_dir}/data.npy"
    names_path = f"{args.data_dir}/names.npy"
    labels_path = f"{args.data_dir}/labels.npy"

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path)

    dataset = NpyDataset(data_path, names_path, labels_path, tokenizer)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_fn)

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
        train_dataset=dataset,
        data_collator=collate_fn,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.output_dir)

if __name__ == '__main__':
    main()
