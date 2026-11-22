# 为适配新版依赖对 Ditto 源码的修改

Ditto 发布于 2021 年，依赖 `torch==1.9`、`transformers==4.9.2`、NVIDIA Apex。本机环境为 Python 3.10 + `torch 2.11.0+cu128` + `transformers 4.57.6`，共做 4 处最小修改。

## 1. `ditto_light/ditto.py`：AdamW 导入

```python
# 原
from transformers import AutoModel, AdamW, get_linear_schedule_with_warmup

# 改
from torch.optim import AdamW
from transformers import AutoModel, get_linear_schedule_with_warmup
```

原因：`transformers` 4.57 已移除 `AdamW` 导出。

## 2. `ditto_light/ditto.py`：Apex 替换

```python
# 原
from apex import amp

# 改
class _AmpShim:
    @staticmethod
    def initialize(model, optimizer=None, opt_level=None):
        return (model, optimizer) if optimizer is not None else model

    @staticmethod
    def scale_loss(loss, optimizer):
        from contextlib import nullcontext
        return nullcontext(loss)

amp = _AmpShim()
```

原因：Apex 需要编译 CUDA 扩展，本机难以安装；shim 保持接口可用，仅放弃混合精度（不影响正确性）。

## 3. `ditto_light/summarize.py`：NLTK 按需加载

```python
# 原（import 时立刻读语料，未用 --summarize 也会报错）
from nltk.corpus import stopwords
stopwords = set(stopwords.words('english'))

# 改
from nltk.corpus import stopwords as _nltk_stopwords
_STOPWORDS = None

def _stopwords():
    global _STOPWORDS
    if _STOPWORDS is None:
        _STOPWORDS = set(_nltk_stopwords.words('english'))
    return _STOPWORDS
```

## 4. `ditto_light/knowledge.py`：spacy 可选导入

```python
# 原
import spacy

# 改
try:
    import spacy
except ImportError:
    spacy = None
```

原因：spacy 只在 `--dk` 领域知识注入时使用，未启用时不应阻塞训练。

## 依赖版本

| 包 | 版本 |
|---|---|
| Python | 3.10.22 |
| torch | 2.11.0+cu128 |
| transformers | 4.57.6（需 `<5`） |
| tensorboardX | 最新 |
| numpy | 2.2.6 |
| pandas | 2.3.3 |
| scikit-learn | 1.7.2 |

## 备注

- `requirements.txt` 中的旧版本组合（torch 1.9 + cu111 + numpy 1.19 + spacy 3.1）不可直接使用；
- 以上修改只影响运行兼容性，未改变模型结构与训练逻辑。
