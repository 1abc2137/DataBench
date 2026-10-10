# 01 表格错误检测

## 方法

当前薄片实现 `missing_value_baseline`：遍历除 `__row_id` 外的单元格，将空字符串标记为缺失错误。它只检测，不修改数据。

## 数据

默认样例为 `datasets/samples/errors_demo.csv`，包含 4 行教学数据和 2 个已知空单元格。该文件为项目自建样例，不含个人或敏感信息。

## 运行

```powershell
python -m pytest modules\error_detection\test_error_detection.py -q
python tools\acceptance.py --phase 3 --module error_detection
python -m streamlit run app.py
```

## 输出

算法返回 `AlgorithmResult`，每项预测包含 `row_id`、`column`、`error_type` 和 `score`。页面运行后保存完整实验 JSON。

## 限制

当前只识别空字符串，不能识别格式异常、离群值、语义错误或跨字段约束违反；尚不满足最终版本所需的两种方法要求。
