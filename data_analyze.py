import numpy as np
import os
from collections import Counter, defaultdict

def analyze_single_class(label_dir, pred_dir, key, valid_classes=None):
    """
    通用单标签分类混淆矩阵分析。
    key: 属性名
    valid_classes: 类别列表
    """
    label_path = os.path.join(label_dir, "labels.npy")
    pred_path = os.path.join(pred_dir, "labels.npy")
    labels = np.load(label_path, allow_pickle=True)
    preds = np.load(pred_path, allow_pickle=True)
    assert len(labels) == len(preds), "标签和预测数量不一致"
    if valid_classes is None:
        # 自动收集所有出现过的类别
        valid_classes = set()
        for label, pred in zip(labels, preds):
            valid_classes.add(label.get(key, ["Normal"])[0])
            valid_classes.add(pred.get(key, ["Normal"])[0])
        valid_classes = sorted(list(valid_classes))
    conf_matrix = defaultdict(lambda: defaultdict(int))
    correct = 0
    total = 0
    for label, pred in zip(labels, preds):
        label_val = label.get(key, ["Normal"])
        pred_val = pred.get(key, ["Normal"])
        label_cls = label_val[0] if label_val else "Normal"
        pred_cls = pred_val[0] if pred_val else "Normal"
        # if key == 'best_atk_spd' and label_cls == 'Fast' and pred_cls == 'Normal':
        #     print(f"Discrepancy found: id = {total}")
        if key == 'slow_eff' and label_cls == 'Resist' and pred_cls == 'Normal':
            print(f"Discrepancy found: id = {total}")
        if label_cls not in valid_classes:
            label_cls = valid_classes[0]
        if pred_cls not in valid_classes:
            pred_cls = valid_classes[0]
        conf_matrix[label_cls][pred_cls] += 1
        if label_cls == pred_cls:
            correct += 1
        total += 1
    print(f"Confusion Matrix for {key}:")
    col_width = max(len(x) for x in (["label/pred"] + valid_classes)) + 2
    header = "label/pred".ljust(col_width) + "".join(pred_cls.ljust(col_width) for pred_cls in valid_classes)
    print(header)
    for label_cls in valid_classes:
        row = label_cls.ljust(col_width)
        row += "".join(str(conf_matrix[label_cls][pred_cls]).ljust(col_width) for pred_cls in valid_classes)
        print(row)
    acc = correct / total if total > 0 else 0
    print(f"Accuracy: {acc:.4f} ({correct}/{total})\n")

    # 统计每个label的TP, FP, FN, TN, 正确率
    print(f"Per-class stats for {key}:")
    for cls in valid_classes:
        TP = conf_matrix[cls][cls]
        FP = sum(conf_matrix[other][cls] for other in valid_classes if other != cls)
        FN = sum(conf_matrix[cls][other] for other in valid_classes if other != cls)
        TN = sum(conf_matrix[other1][other2] for other1 in valid_classes for other2 in valid_classes if other1 != cls and other2 != cls)
        total_cls = TP + FP + FN + TN
        acc_cls = (TP + TN) / total_cls if total_cls > 0 else 0
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        print(f"{cls}: TP={TP}, FP={FP}, FN={FN}, TN={TN}, Acc={acc_cls:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
    print()

def analyze_multilabel(label_dir, pred_dir, key, valid_elements):
    """
    多标签属性分析，统计每个元素的TP/FP/FN/TN。
    key: 属性名
    valid_elements: 所有可能的元素
    """
    label_path = os.path.join(label_dir, "labels.npy")
    pred_path = os.path.join(pred_dir, "labels.npy")
    labels = np.load(label_path, allow_pickle=True)
    preds = np.load(pred_path, allow_pickle=True)
    assert len(labels) == len(preds), "标签和预测数量不一致"
    print(f"Element-wise confusion for {key}:")
    for elem in valid_elements:
        TP = FP = FN = TN = 0
        for label, pred in zip(labels, preds):
            label_set = set(label.get(key, []))
            pred_set = set(pred.get(key, []))
            if elem in label_set and elem in pred_set:
                TP += 1
            elif elem not in label_set and elem in pred_set:
                FP += 1
            elif elem in label_set and elem not in pred_set:
                FN += 1
            else:
                TN += 1
        total_elem = TP + FP + FN + TN
        acc_elem = (TP + TN) / total_elem if total_elem > 0 else 0
        precision = TP / (TP + FP) if (TP + FP) > 0 else 0
        recall = TP / (TP + FN) if (TP + FN) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        print(f"{elem}: TP={TP}, FP={FP}, FN={FN}, TN={TN}, Acc={acc_elem:.4f}, Precision={precision:.4f}, Recall={recall:.4f}, F1={f1:.4f}")
    print()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--label_dir", type=str, required=True, help="标准答案labels.npy所在文件夹")
    parser.add_argument("--pred_dir", type=str, required=True, help="模型预测labels.npy所在文件夹")
    args = parser.parse_args()

    # 单标签属性
    analyze_single_class(args.label_dir, args.pred_dir, "best_atk_spd", ["Fast", "Normal", "Slow"])
    analyze_single_class(args.label_dir, args.pred_dir, "slow_eff", ["Resist", "Normal", "Weak"])
    analyze_single_class(args.label_dir, args.pred_dir, "occurrence", ["Single", "Double", "Triple", "Sparse", "Dense"])

    # 多标签属性
    elements = ["Fire", "Ice", "Poison", "Blunt", "Lightning"]
    analyze_multilabel(args.label_dir, args.pred_dir, "weak", elements)
    analyze_multilabel(args.label_dir, args.pred_dir, "resist", elements)
    analyze_multilabel(args.label_dir, args.pred_dir, "special_eff", elements)

# e.g python data_analyze.py --label_dir data/game/val --pred_dir data/game/lora-4B
# python data_analyze.py --label_dir predict_1128_0008 --pred_dir predict_1128_0019
