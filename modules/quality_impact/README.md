# 03 数据质量影响评测

研究「同样的数据错误对下游分类任务的影响」。对同一份数据先按固定种子划分训练/测试集，只污染与清洗训练集，再在同一分类器上对比**原始干净 / 污染后（不清洗）/ 四种清洗策略**共六个条件，输出数据质量指标与下游指标（F1 优先）。

## 目标与边界

模块 ID `quality_impact`，代码目录 `modules/quality_impact/`。系统比较数据质量问题与清洗策略对下游分类任务的影响，不建设通用自动清洗平台。

## 方法

借鉴 CleanML（ICDE 2021）的「错误类型 × 清洗策略」矩阵，把三类常见数据错误各配四种清洗策略（两种基础策略 + 两种复杂策略）：

| 错误类型（算法） | 扰动方式 | 策略一（简单） | 策略二（统计） | 策略三（复杂） | 策略四（复杂） |
| --- | --- | --- | --- | --- | --- |
| 缺失值 `missing_baseline` | 每列按比例注入 NaN | 删除含缺失的行 | 数值列中位数 / 类别列众数插补 | K 近邻插补（k=3，数值列） | 迭代回归插补（MICE 简化，10 轮） |
| 离群值 `outlier_impact` | 数值列注入 mean±5σ 极端值 | 删除超出 [Q1−1.5IQR, Q3+1.5IQR] 的行 | Winsorize 截断到该边界 | 孤立森林（100 棵树）检出离群行后截断到 IQR 边界 | 迭代 IQR 截断（最多 5 轮，直到不再变化） |
| 重复记录 `duplicate_impact` | 随机复制比例行（连同标签）追加到末尾 | 删除完全重复的特征行 | 重复行聚合（数值取均值、类别取首条） | 聚合 + 一致性投票（类别与标签取众数） | 每个重复组保留缺失最少的一行 |

策略编号按 `common.CLEANERS` 中的顺序生成（`strategy1` ~ `strategy4`），页面会把编号替换为带具体策略名的中文标签。

下游分类器为 Logistic Regression（带 `StandardScaler` 与 `class_weight='balanced'`）和 Random Forest（50 棵树，`class_weight='balanced'`），用同一数据划分与随机种子公平对比。

关键约束（任务书「不做事项」）：

- 只污染/清洗**训练集**，测试集全程干净；
- 插补/截断的统计量（中位数/众数/分位数）**只用训练集拟合**，不泄漏测试集信息；
- 先 `train_test_split`（`stratify` 按标签分层）再扰动。

## 数据

内置三份二分类数据集（数据卡见 `DATASET_CARD.md`），也可上传 CSV（≤10MB）覆盖：

| 数据集 | 规模 | 来源 | 是否入库 |
| --- | --- | --- | --- |
| `quality_demo.csv` | 400 行 × 5 特征 | 项目自建合成样例 | 是 |
| `breast_cancer.csv` | 569 行 × 30 特征 | UCI Breast Cancer Wisconsin（sklearn 离线生成） | 是 |
| `adult.csv` | 30,162 行 × 14 特征 | UCI Adult 人口收入（已剔除 `?` 行、`income`→`label` 0/1） | 否 |

`adult.csv` 较大，不提交仓库，用 `modules/quality_impact/prepare_datasets.py` 重新生成（幂等，已存在则跳过）。

## 运行

```powershell
# 本组测试
uv run python -m pytest modules\quality_impact\test_quality_impact.py -q
# 全量回归测试
uv run python -m pytest -q
# 验收自查
uv run python tools\acceptance.py --profile development --module quality_impact
# 页面
uv run python -m streamlit run app.py
```

## 输出与指标

算法通过 `algorithms/<algorithm_id>/algorithm.json` 注册为 `builtin`，由统一 executor 运行并返回 `AlgorithmResult`，`predictions` 含四部分：

- `quality_metrics`：扰动比例、原始/污染后行数、各策略清洗后的行数、缺失率 / 重复率；
- `downstream_metrics`：六个条件各自的 `clean_f1` / `polluted_f1` / `strategy1_f1` ~ `strategy4_f1`；
- `comparisons`：六个条件各自的 `accuracy` / `precision` / `recall` / `f1`；
- `strategies`：本次运行的策略清单（`key` / `label` / `condition`），页面据此生成中文标签。

`metrics` 与 `downstream_metrics` 保持一致，便于直接比较。`metadata` 记录目标列、错误类型、扰动比例、随机种子、分类器和四种清洗策略名。页面运行后通过 `save_experiment` 保存完整实验 JSON（配置、指标、元数据、预测结果），样例结果见 `EXPERIMENTS.md`。

清洗后训练样本不足（少于 5 行）或只剩单一类别时，该策略的指标为 `null`，页面显示 `—`，不会中断整次运行。

## 复现实验

运行以下脚本可复现 `EXPERIMENTS.md` 中的数值：

```python
from core.datasets import load_csv
from modules.quality_impact.common import run_quality_experiment

df = load_csv('datasets/samples/quality_demo.csv')
for error_type in ('missing', 'outlier', 'duplicate'):
    for rate in (0.1, 0.3, 0.5):
        r = run_quality_experiment(df, 'label', error_type, rate, seed=0, classifier='logreg')
        print(error_type, rate, r['downstream_metrics'])
```

## 失败案例

任务书要求覆盖的健壮性场景在 `test_quality_impact.py` 中均有对应测试：

- 目标列不存在 → `ValueError`（`test_missing_target_raises`）；
- 标签单一类别 / 样本过少无法划分 → 抛出异常（`test_single_class_raises`、`test_too_few_samples_raises`）；
- 结果不可 JSON 序列化（如塞入模型对象）→ `AlgorithmResult.validate()` 报 `TypeError`（`test_contract_rejects_unserializable_result`）；
- 高扰动比例下简单删行策略删到样本不足 → 该条件指标为 `null`，其余条件照常返回。

## 限制

- 目前一次运行只使用一个随机种子；换种子会改变数据划分与扰动位置，页面可手动切换，但尚未提供多种子均值 ± 波动的自动汇总。
- 统计检验（如配对 t 检验）暂未实现，结论为描述性对比，不宣称某清洗方法普遍最优。
- `polluted` 条件对缺失值用 0 填充仅为让模型可运行，不视为规范清洗。
- 简单删行策略在高扰动比例下会删掉过多行导致无法训练，该条件指标为空。
- K 近邻插补与迭代回归插补在 `adult.csv`（3 万行）上开销明显高于其他策略，页面「扰动比例 → F1 曲线」会对 0~0.5 共 11 个比例各跑一次，选大数据集时耗时较长。
- 类别列用整数编码（`factorize`），高基数类别列（如 Adult 的 `occupation`）编码质量有限。
