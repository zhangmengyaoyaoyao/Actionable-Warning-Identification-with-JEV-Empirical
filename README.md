# Actionable Warning Identification with JEV

用 JEV（TypeSafe System One）的 Choice 模式判断静态分析警告是否可处理。每条警告三选一：`actionable`、`unactionable`、`unknown`。完整调用结果先落成 JSON，再导出 Excel，并对照人工标记写出 `groundtruth` 与 `comparison`。

以下命令都在项目根目录、已激活虚拟环境后执行。

# 1 目录与代码

| 路径 | 说明 |
| --- | --- |
| `report/spotbugs/<project>/` | Java 警告 JSON。文件名 `bug_0001_dbcp.json` 对应人工标记 CSV 的第 1 行 |
| `report/spotbugs_linked/` | Java 人工标记，`<project>_linked.csv` 的 `final_label` 为 `TP` 或 `FP` |
| `report/c_json/` | C/C++ 警告 JSON |
| `report/c_raw/c.xlsx` | C/C++ 人工标记。导出 C 结果的 Excel 时需要此文件 |
| `response/<model>/spotbugs/<project>/` | Java 的 JEV 结果，每条警告一个 JSON |
| `response/<model>/C_project/` | C/C++ 的 JEV 结果 |
| `results/jev/` | 导出的 Excel |
| `src/cli.py` | 命令入口：`jev`、`jev-excel` |
| `src/jev/questions.py` | Choice 的 `instructions` 与 `criteria` |
| `src/jev/client.py` | TypeSafe 客户端 |
| `src/jev/pipeline.py` | 扫描警告 JSON、调用 JEV、写入 `response/` |
| `src/jev/export.py` | 把已有结果导出为 Excel，并计算 `comparison` |
| `.env` | `TYPESAFE_API_KEY`。可从 `.env.example` 复制 |

Java 项目及警告条数：

| 项目 | 条数 | 项目 | 条数 |
| --- | ---: | --- | ---: |
| dbcp | 165 | fileupload | 568 |
| bcel | 625 | collections | 645 |
| digester | 650 | codec | 665 |
| net | 718 | mavendp | 918 |
| pool | 2281 | configuration | 2905 |

C/C++ 警告在 `report/c_json/`，共 1904 条。小批量验证用 **dbcp**。

人工标记：`TP` 表示警告真实可处理，`FP` 表示静态分析误报。

# 2 准备环境

已有虚拟环境 `.venv`（Python 3.12）。在 PowerShell 中：

```powershell
cd "F:\STUDY\ise\Agent based AWI\Actionable Warning Identification with JEV-Empirical"
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

若激活脚本被执行策略拦住，先在当前窗口执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

依赖为 `python-dotenv`、`typesafe-sdk`、`pandas`、`openpyxl`。

# 3 配置 API key

把 `.env.example` 复制为 `.env`，填写：

```
TYPESAFE_API_KEY=你的key
```

程序启动时会读取 `.env`。也可以只在当前窗口设置：

```powershell
$env:TYPESAFE_API_KEY="你的key"
```

# 4 调用 JEV

Choice 定义在 `src/jev/questions.py`。默认模型名 `jev-latest`，写入 `response/jev-latest/`。`--end` 不含终点，`--start 0 --end 10` 是排序后的前 10 条。

## 4.1 小批量验证（dbcp，前 10 条）

```powershell
python -m src.cli jev --lang java --projects dbcp --start 0 --end 10
```

等价入口：

```powershell
python -m src.jev --lang java --projects dbcp --start 0 --end 10
```

结果：`response/jev-latest/spotbugs/dbcp/bug_0001_dbcp.json` 起，每条一个 JSON，内含 request、response、`choice`、`confidence`、`probabilities`。

## 4.2 跑完 dbcp

已有 JSON 会跳过：

```json
{
  "source_file": "report/spotbugs/bcel/bug_0001_bcel.json",
  "warning": { "...原始警告..." },
  "created_at": "2026-...",
  "request": {
    "model": "jev-latest",
    "question_id": "actionability",
    "state": "...",
    "questions": {
      "actionability": {
        "type": "choice",
        "instructions": "...",
        "criteria": {
          "actionable": "...",
          "unactionable": "...",
          "unknown": "..."
        }
      }
    }
  },
  "response": {
    "model": "jev-1.13.0",
    "answers": {
      "actionability": {
        "type": "choice",
        "choice": "actionable",
        "confidence": 0.9,
        "probabilities": {
          "actionable": 0.9,
          "unactionable": 0.05,
          "unknown": 0.05
        }
      }
    },
    "usage": { "input_tokens": 0, "output_tokens": 0 }
  },
  "answer": {
    "type": "choice",
    "choice": "actionable",
    "confidence": 0.9,
    "probabilities": { "...": "..." }
  }
}
```

## 4.3 跑其他 Java 项目或全部项目

```powershell
python -m src.cli jev --lang java --projects bcel codec --skip-existing
python -m src.cli jev --lang java --projects all --skip-existing
```

可选项目：`bcel`、`codec`、`collections`、`configuration`、`dbcp`、`digester`、`fileupload`、`mavendp`、`net`、`pool`。

指定模型名（同时决定输出目录 `response/<model>/`）：

```powershell
python -m src.cli jev --lang java --projects dbcp --model jev-latest --skip-existing
```

## 4.4 跑 C/C++

先验证前 10 条，再续跑全部：

```powershell
python -m src.cli jev --lang c --start 0 --end 10
python -m src.cli jev --lang c --skip-existing
```

结果目录：`response/jev-latest/C_project/`。

# 5 导出 Excel

读取已经落盘的 JSON，按文件名序号对齐人工标记。`bug_0004_dbcp.json` 对 `dbcp_linked.csv` 的第 4 行，不使用 CSV 里的 `no` 列。只导出 `response/` 中已有的结果。

dbcp：

```powershell
python -m src.cli jev-excel --lang java --projects dbcp
```

全部已跑过的 Java 项目：

```powershell
python -m src.cli jev-excel --lang java --projects all
```

C/C++（需要 `report/c_raw/c.xlsx`）：

```powershell
python -m src.cli jev-excel --lang c
```

默认输出：

```
results/jev/java_jev-latest.xlsx
results/jev/c_jev-latest.xlsx
```

指定路径：

```powershell
python -m src.cli jev-excel --lang java --projects dbcp --output results/jev/dbcp.xlsx
```

每条警告一行。主要列：`file_name`、`project`、`category`、`vtype`、`choice`、`confidence`、三项概率、`groundtruth`、`comparison`。

`comparison` 的对照规则：

| choice | groundtruth | comparison |
| --- | --- | --- |
| actionable | TP | TP |
| unactionable | FP | TN |
| actionable | FP | FP |
| unactionable | TP | FN |
| unknown | TP 或 FP | unknown |

C/C++ 人工标记里的 `True` 视作可处理，`False` 视作误报，对照规则相同。
