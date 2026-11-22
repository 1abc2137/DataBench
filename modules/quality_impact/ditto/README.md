# Ditto 实体匹配实验产物

本目录保存“用 Ditto 做重复检测”这一扩展实验的**可复现产物**。模型权重（约 796MB）不提交，只保留结果与说明。

## 这是什么

CleanML 论文的重复检测器是键碰撞和 ZeroER。我们额外引入 Ditto（BERT 系实体匹配模型）作为更强的检测器，比较它对下游分类任务的影响。

- 数据：`datasets/samples/restaurant.csv`（CleanML Restaurant，12,007 行）
- 正样本定义：同一 `telephone` 的两条记录
- 输入文本字段：`name / streetAddress / city / state / categories`（**不含 telephone**，避免标签泄漏）
- 模型：`distilbert-base-uncased`，3 epochs，GPU（RTX 5060 8GB）
- 匹配阈值：0.5

## 文件

| 文件 | 说明 |
|---|---|
| `groups.json` | 1,327 个重复组，每组是原始行号列表（0-based，对应 `restaurant.csv` 行序） |
| `results.md` | 训练指标、推理统计、下游 F1 对比 |
| `patches.md` | 为适配新版依赖对 Ditto 源码做的 4 处修改 |

## 复现步骤

```powershell
# 1. 克隆并安装环境（详见 patches.md）
git clone https://github.com/megagonlabs/ditto.git

# 2. 生成配对数据（2,232 / 279 / 279）
python make_ditto_pairs.py

# 3. 训练
python train_ditto.py --task Restaurant/cleanml --lm distilbert --n_epochs 3 --batch_size 8 --max_len 128 --save_model

# 4. 推理并合并重复组
python score_pairs.py
```

## 注意

- `groups.json` 的行号基于 CleanML 原始 `raw.csv` 的行序，与 `restaurant.csv` 一致（只删了列，未改行序）；
- 模型文件、训练日志、`ditto/.venv` 都不提交；
- 该实验属于本组扩展，不是 CleanML 原文方法。
