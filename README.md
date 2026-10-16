# 1 项目说明
## 1.1 目录结构
文件夹       | 说明
----------- | -----
prompts  | 存放提示词
report  | 原始数据。spotbugs_linked是完整的警告（包含手工标记结果），spotbugs/是最终的json格式Java项目警告；c_json/是json格式C/C++项目警告。
response  | LLMs返回的回答，子文件夹名称代表“LLM/prompt_technique/project_name”
src  | 核心代码
src/llm  | 从不同平台调用不同LLMs
test  | 临时测试，暂时没有用处

## 1.2 核心代码
文件       | 说明
----------- | -----
src/cli.py  | 统一命令入口（run / jev / toexcel / result / analysis）
src/pipeline.py  | 处理警告 JSON、调用 LLM、写入 response/
src/jev/  | JEV (TypeSafe System One) Choice 模式：调用、落盘完整结果
src/jev/questions.py  | Choice 问题定义（actionable / unactionable / unknown）
src/jev/client.py  | TypeSafeClient 封装
src/jev/pipeline.py  | 扫描警告 JSON、调用 JEV、写入 response/
src/config.py  | 模型平台、项目列表、提示词技术等配置
src/construct_prompts.py  | 根据采用的提示词技术合成提示词
src/postprocess.py  | 将 LLM 回答转 excel 并链接人工标记
src/find_function.py  | 目前采用提取C函数的代码
src/toexcel_and_comp.py  | 后处理入口（默认 Java）
src/response2excel.py  | 将LLM的回答存储到excel中
src/get_result.py  | 根据 excel 统计指标
src/judge_consistent.py  | 判断LLM的结论与手工标记结果的一致性
report/csv2json_java.py  | 将Java项目警告转换为json格式
report/csv2json_c.py  | 将C/C++项目警告转为json格式

# 2 如何上手（调用LLM分类警告）
## 2.1 获取API-KEY
### 2.1.1 Llama3.1-70B-Instruct
阿里云百炼：https://bailian.console.aliyun.com/#/model-market

NVIDIA(推荐-速度快，免费token多):https://build.nvidia.com/meta/llama-3_1-70b-instruct

OpenRouter: https://openrouter.ai/meta-llama/llama-3.1-70b-instruct:free

### 2.1.2 GLM
BigModel: https://bigmodel.cn/pricing

将 key 写入 `.env`（可复制 `.env.example`），或设置对应环境变量。不要把 key 写进源码。

```
AIHUBMIX_API_KEY=...
NVIDIA_API_KEY=...
GLM_API_KEY=...
OPENROUTER_API_KEY=...
DASHSCOPE_API_KEY=...
LLM_API_KEY=...
TYPESAFE_API_KEY=...   # JEV / TypeSafe
```

## 2.2 运行 LLM
在项目根目录执行。`--provider` 可选：`gpt` / `glm` / `nvidia` / `openrouter` / `aihubmix` / `deepseek` / `aliyun` / `ollama`。

```
python -m src.cli run --provider nvidia --lang java --projects codec --techniques zero_shot
python -m src.cli run --provider gpt --lang java --projects all --techniques all
python -m src.cli run --provider deepseek --lang c --techniques critique
```

也可继续用各平台入口（需同样带上 `--lang` 等参数）：

```
python -m src.llm.chat_gpt --lang java --projects digester --techniques zero_shot
python -m src.llm.chat_llama_nvidia --lang java --projects codec --techniques all
```

## 2.3 运行 JEV（Choice 模式）
使用 TypeSafe System One / JEV，对每条警告做三选一分类：`actionable` / `unactionable` / `unknown`。  
当前只负责调用与完整结果落盘，不做 excel / 指标后处理。

安装依赖：

```
pip install -r requirements.txt
```

设置 key（或写入 `.env`）：

```
# PowerShell
$env:TYPESAFE_API_KEY="你的key"
```

运行示例：

```
# 单个 Java 项目，先跑前 2 条验证通路
python -m src.cli jev --lang java --projects bcel --start 0 --end 2

# 全部 Java 项目
python -m src.cli jev --lang java --projects all

# C/C++ 警告
python -m src.cli jev --lang c

# 指定模型名、断点续跑
python -m src.cli jev --lang java --projects codec --model jev-latest --skip-existing

# 等价入口
python -m src.jev --lang java --projects bcel --end 1
```

结果写入（每条警告一个完整 JSON，含 request + response + choice/probabilities/confidence/usage）：

```
response/<model>/spotbugs/<project>/<bug_xxxx>.json   # Java
response/<model>/C_project/<bug_xxxx>.json            # C
```

单条结果结构示意：

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

可在 `src/jev/questions.py` 中修改 Choice 的 `instructions` / `criteria`。

## 2.4 数据后处理（LLM 结果）
将 txt 回复转为 excel，并导入手工标记：

```
python -m src.cli toexcel --lang java
python -m src.cli toexcel --lang c
```

兼容旧入口（默认 Java）：

```
python -m src.toexcel_and_comp
```

根据 final_label 和 status 统计指标：

```
python -m src.cli result --lang java
python -m src.cli result --lang c --by-tool --by-category
```

兼容旧入口（默认 C，且按 tool+category 分组）：

```
python -m src.get_result
```

# 3 实验方法

## 3.1 数据集处理
### 3.1.1 Java
#### 预处理-格式转换
report/link.py: 在报告中加入rank和priority

report/csv2json_java.py: 转换为json格式

转换后的数据

csv格式：report/spotbugs_report

json格式：report/spotbugs_json

例子：

``` json
{
    "category": "MALICIOUS_CODE",
    "vtype": "MS_PKGPROTECT",
    "priority": "2",
    "rank": "18",
    "project": "bcel",
    "warning_line": "@Deprecated\npublic static final String[] SHORT_TYPE_NAMES = { ILLEGAL_TYPE, ILLEGAL_TYPE, ILLEGAL_TYPE, ILLEGAL_TYPE, \"Z\", \"C\", \"F\", \"D\", \"B\", \"S\", \"I\", \"J\", \"V\", ILLEGAL_TYPE, ILLEGAL_TYPE, ILLEGAL_TYPE };",
    "warning_method": "@Deprecated\npublic static final String[] SHORT_TYPE_NAMES = { ILLEGAL_TYPE, ILLEGAL_TYPE, ILLEGAL_TYPE, ILLEGAL_TYPE, \"Z\", \"C\", \"F\", \"D\", \"B\", \"S\", \"I\", \"J\", \"V\", ILLEGAL_TYPE, ILLEGAL_TYPE, ILLEGAL_TYPE };"
}
``` 

### 3.1.2 C/C++
#### 提取函数上下文
因为原警告所在函数提取结果存在错误，我们重新提取警告所在函数作为警告上下文。同时，为了控制token数量，我们规定若函数长度超过100行，以警告上下100行代码作为警告上下文。

具体方法见：
https://github.com/zhangmengyaoyaoyao/Extract-Function-Snippet-From-C-Projects

#### 预处理-格式转换
report/csv2json_c.py: 转换为json格式

### 后处理
提取结果

部分例子手动处理



# 结果分析
将txt回复转换为excel，并将手工标记导入：`python3 -m src.toexcel_and_comp`

toexcel_and_comp中critique情况：发现gpt有很多回答是"No changes needed"，因此碰到这种情况时尝试从第二次、第一次的回答中寻找答案。

根据final_label（groundtruth）和status，统计各个指标的结果。`python3 -m src.get_result`

有一些status还是error，会有"potentially actionable" "Investigate the potential null pointer dereference and ensure `dev` is not null before use"之类的回答。这种情况全部归为unknown。