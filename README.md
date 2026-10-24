# Actionable Warning Identification with JEV：实证研究

基于 [TypeSafe System One / JEV](https://docs.typesafe.ai/introduction.md) 的可行动静态分析警告识别（Actionable Warning Identification, AWI）实证研究。

研究问题：在相同语义定义下，JEV 的三种原语 **Choice**、**Score**、**Noul** 对警告是否可处理（actionable / unactionable）的判别效果如何差异。

数据范围：**全部 Java（SpotBugs）警告** 与 **全部 C/C++ 警告**。

---

## 1. 实验设计

### 1.1 三种原语

每种原语的 API 形状见官方文档：[Choice](https://docs.typesafe.ai/primitives/choice.md)、[Score](https://docs.typesafe.ai/primitives/score.md)、[Noul](https://docs.typesafe.ai/primitives/noul.md)；结构化 criteria 见 [Advanced: structure](https://docs.typesafe.ai/primitives/advanced.md)。

| 原语 | 问题形态 | criteria（均为两条） | 二分类规则 |
| --- | --- | --- | --- |
| Choice | 从固定选项中选一 | `actionable` / `unactionable` | `choice == "actionable"` → 正类 |
| Score | 有序量表 | `[unactionable, actionable]`（level 0 / 1） | `score >= 0.5` → 正类 |
| Noul | 是否可处理（yes/no） | `true`=actionable，`false`=unactionable | `noul >= 0.5` → 正类 |

标签空间只有 **actionable** 与 **unactionable**，不含 `unknown`。

### 1.2 提示词一致性

三种原语共用同一套定义（`src/jev/questions.py`）：

- **actionable**：真实缺陷或风险，值得开发者关注并修改代码。
- **unactionable**：误报、有意模式、或无需修复的噪声。

`instructions` 统一以专家角色开头，再接同一判断任务，仅按原语语法微调：

```
You are an expert in static analysis warning classification.
```

### 1.3 调用与落盘

每条警告 **一次** `system_one` 请求，并行提问三个原语（官方推荐多问同呼）。API 模型名默认 `jev-latest`；结果按原语分顶层目录，互不覆盖：

```
response/jev-choice/...
response/jev-score/...
response/jev-noul/...
```

旧的试跑目录 `response/jev-latest/`（曾含 `unknown`）保留，正式实验不写入该目录。

### 1.4 评价指标

正类 = 人工标记为可处理（Java：`TP`；C：`True`）。

| prediction | groundtruth | comparison |
| --- | --- | --- |
| actionable | TP / True | TP |
| unactionable | FP / False | TN |
| actionable | FP / False | FP |
| unactionable | TP / True | FN |

Precision = TP / (TP + FP)，Recall = TP / (TP + FN)，F1 为二者调和平均。

---

## 2. 数据集

| 数据 | 路径 | 说明 |
| --- | --- | --- |
| Java 警告 | `report/spotbugs/<project>/` | 每条警告一个 JSON |
| Java 人工标记 | `report/spotbugs_linked/<project>_linked.csv` | `final_label`：`TP` / `FP` |
| C/C++ 警告 | `report/c_json/` | 全部项目混在同一目录，按全局序号排序 |
| C/C++ 人工标记 | `report/c_raw/c.xlsx` | `final_label`：`True` / `False` |

对齐规则：`bug_0004_xxx.json` 对应人工标记表的 **第 4 行**（按生成顺序），不使用 CSV 中的 `no` 列。

### Java 项目规模

| 项目 | 条数 | 项目 | 条数 |
| --- | ---: | --- | ---: |
| dbcp | 165 | fileupload | 568 |
| bcel | 625 | collections | 645 |
| digester | 650 | codec | 665 |
| net | 718 | mavendp | 918 |
| pool | 2281 | configuration | 2905 |

### C/C++ 项目规模（合计 1904）

| 项目 | 条数 | 项目 | 条数 |
| --- | ---: | --- | ---: |
| trueprint | 15 | sed | 21 |
| grep | 33 | combine | 49 |
| diffutils | 61 | apr | 65 |
| RIOT | 81 | tiff | 109 |
| Zephyr | 222 | bash | 354 |
| gawk | 373 | binutils | 521 |

---

## 3. 代码结构

| 路径 | 说明 |
| --- | --- |
| `src/cli.py` | 入口：`jev`、`jev-excel` |
| `src/jev/questions.py` | Choice / Score / Noul 的 instructions 与 criteria |
| `src/jev/client.py` | TypeSafe 客户端，一次请求三问 |
| `src/jev/pipeline.py` | 扫描警告、调用 JEV、写入三个结果目录 |
| `src/jev/export.py` | 导出 Excel，统一二分类并计算 `comparison` |
| `results/jev/` | 导出的指标明细表 |
| `.env` | `TYPESAFE_API_KEY` |

---

## 4. 环境准备

在项目根目录、PowerShell：

```powershell
cd "F:\STUDY\ise\Agent based AWI\Actionable Warning Identification with JEV-Empirical"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

若激活被执行策略拦住：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

依赖：`python-dotenv`、`typesafe-sdk`、`pandas`、`openpyxl`。

配置 API key：复制 `.env.example` 为 `.env`，填写：

```
TYPESAFE_API_KEY=你的key
```

或当前窗口临时设置：

```powershell
$env:TYPESAFE_API_KEY="你的key"
```

---

## 5. 运行实验

所有命令在项目根目录执行。`--end` 为不含终点的切片；`--skip-existing` 仅当 **choice / score / noul 三个结果文件都已存在** 时跳过该条。`--model` 在 `jev` 子命令中只表示 TypeSafe API 模型名，不决定输出目录。

### 5.1 小批量验证

```powershell
# Java：dbcp 前 10 条
python -m src.cli jev --lang java --projects dbcp --start 0 --end 10

# C：apr（文件序号 0–65，共 65 条）
python -m src.cli jev --lang c --start 0 --end 65
```

每条警告写出三个 JSON，例如：

```
response/jev-choice/spotbugs/dbcp/bug_0001_dbcp.json
response/jev-score/spotbugs/dbcp/bug_0001_dbcp.json
response/jev-noul/spotbugs/dbcp/bug_0001_dbcp.json
```

C 对应：

```
response/jev-choice/C_project/
response/jev-score/C_project/
response/jev-noul/C_project/
```

### 5.2 正式全量：Java

全部 10 个项目、全部警告：

```powershell
python -m src.cli jev --lang java --projects all --skip-existing
```

指定部分项目：

```powershell
python -m src.cli jev --lang java --projects dbcp bcel --skip-existing
```

可选项目名：`bcel`、`codec`、`collections`、`configuration`、`dbcp`、`digester`、`fileupload`、`mavendp`、`net`、`pool`。

### 5.3 正式全量：C/C++

```powershell
python -m src.cli jev --lang c --skip-existing
```

---

## 6. 结果导出

读取已落盘 JSON，对齐人工标记，写出带 `groundtruth` 与 `comparison` 的 Excel。

导出某一种原语：

```powershell
python -m src.cli jev-excel --lang java --projects all --model jev-choice
python -m src.cli jev-excel --lang java --projects all --model jev-score
python -m src.cli jev-excel --lang java --projects all --model jev-noul
python -m src.cli jev-excel --lang c --model jev-choice
```

一次导出三种（默认 `--model all`）：

```powershell
python -m src.cli jev-excel --lang java --projects all
python -m src.cli jev-excel --lang c
```

默认输出：

```
results/jev/java_jev-choice.xlsx
results/jev/java_jev-score.xlsx
results/jev/java_jev-noul.xlsx
results/jev/c_jev-choice.xlsx
results/jev/c_jev-score.xlsx
results/jev/c_jev-noul.xlsx
```

每行一条警告。主要列：`file_name`、`project`、`primitive`、`prediction`、原语原始字段（`choice` / `score` / `noul`）、`confidence`、概率、`groundtruth`、`comparison`。

---

## 7. 推荐实验流程

1. 配置 `.env` 中的 `TYPESAFE_API_KEY`，安装依赖。
2. 小批量验证通路（如 dbcp 前 10 条）。
3. 全量 Java：`python -m src.cli jev --lang java --projects all --skip-existing`
4. 全量 C：`python -m src.cli jev --lang c --skip-existing`
5. 导出：`python -m src.cli jev-excel --lang java --projects all` 与 `python -m src.cli jev-excel --lang c`
6. 在 Excel 中按 `comparison` 统计各原语的 Precision / Recall / F1，对比 Choice、Score、Noul。

修改提示词或 criteria 时，编辑 `src/jev/questions.py` 后重新跑批（可用新输出目录或清空对应 `response/jev-*` 后重跑）。
