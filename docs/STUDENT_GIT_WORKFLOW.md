# DataBench 学生 GitHub 提交与合并流程

## 1. 协作方式

DataBench 采用 `Fork + 功能分支 + Pull Request` 的方式协作。学生不加入主仓库协作者，也不能直接向主仓库 `main` 分支推送代码。

```text
          主仓库
            ↑
      Pull Request
            ↑
学生小组的 Fork 仓库
            ↑
       功能分支开发
```

学生可以在自己的 Fork 中频繁提交和推送，用于保存进度和组内协作；当本组功能大致完成、自查通过后，再向主仓库提交 Pull Request。提交 PR 不等于立即合并，维护者会先审核代码并提出修改意见，确认后才合并。

主仓库地址：

```text
https://github.com/37517968/DataBench.git
```

## 2. 第一次准备仓库

### 2.1 Fork 主仓库

1. 登录 GitHub。
2. 打开 DataBench 主仓库。
3. 点击右上角 `Fork`。
4. 将仓库 Fork 到自己的 GitHub 账号。

每组建议由一名同学创建小组使用的 Fork，并在这个 Fork 中邀请另一名组员协作。这里添加的是学生自己 Fork 仓库的协作者，不会获得 DataBench 主仓库的直接写入权限。

### 2.2 克隆本组 Fork

把下面地址中的 `<你的GitHub用户名>` 替换成实际用户名：

```powershell
git clone https://github.com/<你的GitHub用户名>/DataBench.git
cd DataBench
```

### 2.3 添加主仓库为 upstream

克隆后，`origin` 指向学生自己的 Fork。还需要把正式主仓库添加为 `upstream`：

```powershell
git remote add upstream https://github.com/37517968/DataBench.git
git remote -v
```

正常情况下应看到：

```text
origin    学生自己的 Fork
upstream  教师或研究生维护的主仓库
```

不要把 `origin` 改成主仓库地址，否则学生没有推送权限。

## 3. 创建本组功能分支

开始开发前先同步主仓库：

```powershell
git switch main
git fetch upstream
git pull --ff-only upstream main
git push origin main
```

然后创建功能分支。分支名称建议使用 `g组号/功能名称`：

```powershell
git switch -c g01/error-detection
```

其他示例：

```text
g02/data-repair
g03/quality-impact
g04/dependency-discovery
g05/truth-discovery
g06/entity-matching
g07/table-discovery
g08/query-analysis
```

两名组员也可以在小组 Fork 中建立更细的分支，例如：

```text
g01/rule-detector
g01/iqr-detector
g01/interactive-page
g01/metrics-and-tests
```

组内应提前约定文件分工，尽量按 `algorithms/<algorithm_id>/` 分配算法，避免同时修改同一段 `page.py` 或测试代码。

## 4. 学生可以修改哪些文件

每组主要修改自己的模块目录：

```text
modules/<module_id>/
```

本组小型样例可以放在：

```text
datasets/samples/<module_id>/
```

未经维护者同意，不要直接修改：

```text
app.py
core/
core/registry.py
tools/acceptance.py
其他小组目录
公共测试
```

如果确实需要修改公共接口，应先在主仓库创建 Issue，说明修改原因、预期接口、影响模块和兼容方案，得到确认后再开发。

不要提交以下内容：

- 任意位置的 `.venv/`；
- `.algorithm_envs/` 和 `runs/`；
- `__pycache__/` 和 `.pytest_cache/`；
- `experiments/` 和 `reports/` 中的临时运行结果；
- 大型原始数据和模型权重；
- 密码、数据库连接串、密钥或 `.env`；
- 与本组任务无关的编辑器配置和临时文件。

## 5. 开发期间如何保存进度

“大致开发完成后再提交合并”不等于开发期间不提交代码。学生应当频繁提交到自己的功能分支，并推送到自己的 Fork，避免电脑故障导致代码丢失。

查看修改：

```powershell
git status
git diff
```

提交一项相对完整的修改：

```powershell
git add modules/error_detection
git add datasets/samples/error_detection
git commit -m "feat(error-detection): add rule-based detector"
```

推送到自己的 Fork：

```powershell
git push -u origin g01/error-detection
```

后续继续开发时可以重复：

```powershell
git add <本次修改的文件>
git commit -m "说明本次完成的内容"
git push
```

提交信息建议使用以下格式：

```text
feat(error-detection): add IQR detector
test(error-detection): add metric cases
docs(error-detection): document dataset source
fix(error-detection): reject empty input
```

不要把几周工作全部压成一个含义不清楚的 `update` 提交。即使最终只创建一次 PR，开发期间仍应保留清楚的提交记录。

## 6. 两名组员如何同步

如果两名组员共同使用一个小组 Fork，开始当天工作前先同步远程分支：

```powershell
git switch g01/error-detection
git pull --rebase origin g01/error-detection
```

完成一项修改后及时提交并推送：

```powershell
git push origin g01/error-detection
```

如果两个人使用不同功能分支，应先在小组 Fork 中完成组内合并和页面联调，确认模块能够整体运行，再向 DataBench 主仓库提交一个完整 PR。

遇到冲突时不要删除对方代码或使用强制推送覆盖远程记录。先停止操作，保存报错信息和 `git status` 输出，再联系同组同学或研究生处理。

## 7. 什么时候可以提交 Pull Request

建议本组主要功能大致完成后再向主仓库提交 PR。至少应满足：

- 两种方法或实验策略已经接入；
- `AlgorithmResult` 输出结构明确；
- Streamlit 页面能够上传或选择数据、选择方法、设置参数、运行并展示结果；
- 小型样例和数据说明已经准备；
- `acceptance.py` 能真实运行本组方法并保存实验记录；
- 正常、异常、合同、实验保存和指标测试已经编写；
- 模块 README 已说明方法、数据、运行和限制；
- `DATASET_CARD.md` 已记录数据来源、许可、格式和真值；
- 本组代码中没有密钥、大文件、缓存或临时实验结果；
- 已按照 `docs/SUBMISSION_CHECKLIST.md` 完成自查。

不要求所有研究拓展都完成后才能提交。第一学期约定以外的复杂模型、完整论文复现和大规模数据实验，可以在基础模块合并后继续开发。

## 8. 提交 PR 前同步主仓库

其他小组或维护者可能已经更新 `main`。提交 PR 前应把最新主仓库内容合入自己的功能分支：

```powershell
git fetch upstream
git switch g01/error-detection
git merge upstream/main
```

如果出现冲突，不要直接删除冲突标记后提交。应确认公共代码和本组代码都被正确保留；无法判断时联系维护者。

同步后，将更新推送到自己的 Fork：

```powershell
git push origin g01/error-detection
```

## 9. 创建 Pull Request

1. 打开自己 Fork 的 GitHub 页面。
2. 点击 `Compare & pull request`。
3. 确认目标仓库是 `37517968/DataBench`。
4. 确认目标分支是 `main`。
5. 确认来源是本组 Fork 的功能分支。

PR 标题建议：

```text
[第1组] 完成表格错误检测基础模块
```

PR 说明至少包含：

```markdown
## 完成内容

- 实现了哪些方法
- 完成了哪些页面交互
- 使用了什么数据和指标

## 修改范围

- 列出主要修改文件
- 说明是否修改公共文件

## 复现方法

- 安装和运行命令
- 页面操作步骤
- 使用的示例数据
- 预期输出

## 自查结果

- 本组测试结果
- 全量测试结果
- acceptance 检查结果

## 已知限制

- 当前不支持的输入
- 指标适用条件
- 失败案例或性能限制

## 组内分工

- 学生A完成的内容
- 学生B完成的内容
```

学生只负责提交 PR，不要点击或要求获得直接合并主仓库的权限。

## 10. 如何处理审核意见

维护者可能在 PR 中提出修改意见，例如：

- 输出字段不符合约定；
- 页面没有真实调用算法；
- 缺少错误输入测试；
- 数据来源或真值说明不清；
- 指标计算错误；
- 修改了不属于本组的文件。

学生继续在原功能分支修改即可：

```powershell
git switch g01/error-detection
git add <修改的文件>
git commit -m "fix(error-detection): address review comments"
git push
```

GitHub 会自动把新提交加入原来的 PR，不需要关闭旧 PR或重新创建 PR。

修改后在 PR 中说明：

- 解决了哪些意见；
- 哪些文件发生变化；
- 如何验证；
- 是否还有未解决问题。

## 11. 合并以后学生要做什么

维护者确认代码和页面后，会将 PR 合并到主仓库。学生随后同步自己的 `main`：

```powershell
git switch main
git fetch upstream
git pull --ff-only upstream main
git push origin main
```

确认本组修改已经进入主仓库后，可以删除已经完成的本地分支：

```powershell
git branch -d g01/error-detection
```

后续新功能应重新从最新 `main` 创建新分支，不要继续使用已经合并的旧分支。

## 12. 学生需要记住的原则

1. 开发代码保存在自己的 Fork，不需要主仓库写权限。
2. 开发期间频繁 commit 和 push，基本完成后再向主仓库提交 PR。
3. 每个 PR 只修改本组模块和本组数据，公共修改必须提前申请。
4. PR 是审核入口，不是提交后自动合并。
5. 审核意见在原分支修改并继续 push，不要重复创建 PR。
6. 合并由教师或研究生完成，学生不能直接操作主仓库 `main`。
7. 不提交大型数据、运行缓存、实验临时文件和任何凭据。

