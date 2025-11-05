import argparse
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModelForCausalLM, Trainer, TrainingArguments

class NpyDataset(Dataset):
    def __init__(self, npy_path):
        self.data = np.load(npy_path, allow_pickle=True)
    def __len__(self):
        return len(self.data)
    def __getitem__(self, idx):
        return self.data[idx]

def collate_fn(batch):
    # 假设每个样本是dict，包含 'input_ids', 'attention_mask', 'labels' 等
    input_ids = [torch.tensor(item['input_ids']) for item in batch]
    attention_mask = [torch.tensor(item['attention_mask']) for item in batch]
    labels = [torch.tensor(item['labels']) for item in batch]
    return {
        'input_ids': torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True, padding_value=0),
        'attention_mask': torch.nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0),
        'labels': torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--npy_path', type=str, required=True, help='Path to npy file')
    parser.add_argument('--model_name_or_path', type=str, required=True, help='Pretrained model name or path')
    parser.add_argument('--output_dir', type=str, default='./output', help='Output directory')
    parser.add_argument('--batch_size', type=int, default=4)
    parser.add_argument('--epochs', type=int, default=3)
    parser.add_argument('--lr', type=float, default=5e-5)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model_name_or_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(args.model_name_or_path)

    dataset = NpyDataset(args.npy_path)
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
