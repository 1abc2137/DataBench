# 数据卡

本模块使用三份二分类数据集，统一约定目标列名为 `label`、取值 0/1。来源或许可不明者不进入发布包。

## quality_demo.csv（质量演示数据，合成）

- 数据集名称：quality_demo（质量演示数据）
- 本地版本号：`quality_demo_v1`
- 对应模块：`quality_impact`
- 获取或生成日期：2026-10-19
- 维护人：第 3 组 quality_impact（陈宏波）

- 原始来源：项目自建合成样例，无外部来源。
- 下载链接或生成脚本：直接提交 CSV，无生成脚本。
- 许可证或使用条款：项目内教学用，无敏感信息，允许提交仓库。

| 文件 | 角色 | 行数 | 列数 | 大小 | 主键 |
| --- | --- | ---: | ---: | ---: | --- |
| `quality_demo.csv` | 小规模快速运行样例 | 400 | 7 | 8.9 KB | 无（加载时生成 `__row_id`） |

| 字段 | 类型 | 含义 | 允许缺失 | 示例 |
| --- | --- | --- | --- | --- |
| `age` | 数值 | 年龄 | 否 | 22 |
| `income` | 数值 | 收入 | 否 | 151 |
| `score` | 数值（浮点） | 得分 | 否 | -1.149 |
| `edu` | 类别 | 学历（high/mid/low） | 否 | low |
| `region` | 类别 | 地区（A/B/C） | 否 | A |
| `label` | 二分类 | 目标标签 | 否 | 0 |

- 标签定义：0/1 二分类，分布 0→240（60%）、1→160（40%）。
- 训练/测试划分：运行时 `train_test_split(test_size=0.25, stratify=label)`，随机种子可调。

## breast_cancer.csv（UCI Breast Cancer Wisconsin）

- 数据集名称：Breast Cancer Wisconsin (Diagnostic)
- 本地版本号：`breast_cancer_v1`
- 对应模块：`quality_impact`
- 获取或生成日期：2026-10-22
- 维护人：第 3 组 quality_impact（陈宏波）

- 原始来源：UCI Breast Cancer Wisconsin (Diagnostic)，经 scikit-learn `load_breast_cancer()` 离线导出。
- 原作者或机构：Dr. William H. Wolberg 等，University of Wisconsin。
- 下载链接或生成脚本：`modules/quality_impact/prepare_datasets.py`（`prepare_breast_cancer`，完全离线、幂等）。
- 许可证或使用条款：随 scikit-learn 分发（BSD-3-Clause）；UCI 原始数据可教学使用。
- 是否允许重新分发：允许（121 KB，随仓库提交）。

| 文件 | 角色 | 行数 | 列数 | 大小 | 主键 |
| --- | --- | ---: | ---: | ---: | --- |
| `breast_cancer.csv` | 公开二分类数据 | 569 | 31 | 122 KB | 无 |

- 字段：30 个数值特征（mean/texture/perimeter/area 等的 mean/error/worst 三组），加 `label`。
- 标签定义：0=恶性（malignant）、1=良性（benign）。

## adult.csv（UCI Adult 人口收入）

- 数据集名称：Adult（Census Income，人口普查收入预测）
- 本地版本号：`adult_v1`
- 对应模块：`quality_impact`
- 获取或生成日期：2026-10-22
- 维护人：第 3 组 quality_impact（陈宏波）

- 原始来源：UCI Adult。
- 下载链接或生成脚本：`modules/quality_impact/prepare_datasets.py`（`prepare_adult`），URL `https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data`。
- 原作者或机构：Ronny Kohavi 与 Barry Becker，1996。
- 许可证或使用条款：UCI 公开数据集，可教学使用。
- 是否允许重新分发：**否**（3.1 MB，已加入 `.gitignore`，组员用脚本重新生成）。

| 文件 | 角色 | 行数 | 列数 | 大小 | 主键 |
| --- | --- | ---: | ---: | ---: | --- |
| `adult.csv` | 公开二分类数据 | 30,162 | 15 | 3.1 MB | 无 |

- 字段：14 个特征（`age`、`workclass`、`fnlwgt`、`education`、`education-num`、`marital-status`、`occupation`、`relationship`、`race`、`sex`、`capital-gain`、`capital-loss`、`hours-per-week`、`native-country`）加 `label`。
- 标签定义：0=收入 ≤50K、1=收入 >50K（由 `income` 映射）。
- 预处理：跳过 `?` 缺失行、去首尾空白、`income` 映射为 0/1，原始 32,561 行 → 30,162 行。

## 通用说明

- 加载后由 `core.datasets.load_csv` 统一注入 `__row_id`，模型与页面均不使用该列。
- 三份数据均为二分类、无冲突标签；不含个人身份信息（Adult 已匿名化）。
- 复现命令：`uv run python modules/quality_impact/prepare_datasets.py`（幂等，已存在则跳过）。
