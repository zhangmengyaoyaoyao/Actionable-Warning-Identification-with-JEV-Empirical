import argparse

from src.config import (
    JAVA_PROJECTS,
    PROMPT_TECHNIQUES,
    PROVIDERS,
    RESULT_MODELS,
    get_api_key,
    resolve_list,
)
from src.get_result import get_result
from src.llm.clients import build_client
from src.pipeline import run_experiments
from src.postprocess import export_responses_to_excel


def _add_common_experiment_args(parser):
    parser.add_argument("--lang", choices=["java", "c"], required=True, help="实验语言：java 或 c")
    parser.add_argument(
        "--projects",
        nargs="+",
        default=["all"],
        help="Java 项目名，或 all。C 实验会忽略该参数。",
    )
    parser.add_argument(
        "--techniques",
        nargs="+",
        default=["all"],
        help="提示词技术，或 all。",
    )
    parser.add_argument("--tool", default="spotbugs", help="Java 静态分析工具目录名，默认 spotbugs")
    parser.add_argument("--models", nargs="+", default=None, help="后处理使用的模型目录名")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Actionable Warning Identification 实验入口",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="调用 LLM 对警告分类，结果写入 response/")
    run.add_argument("--provider", required=True, choices=sorted(PROVIDERS.keys()))
    run.add_argument("--lang", choices=["java", "c"], required=True)
    run.add_argument("--projects", nargs="+", default=["all"])
    run.add_argument("--techniques", nargs="+", default=["all"])
    run.add_argument("--tool", default="spotbugs")
    run.add_argument("--model", default=None, help="response/ 下的模型目录名")
    run.add_argument("--model-fullname", default=None, help="实际请求 API 的模型名")
    run.add_argument("--url", default=None, help="覆盖默认 API base url")
    run.add_argument("--api-key", default=None, help="覆盖环境变量中的 API key")
    run.add_argument("--start", type=int, default=None, help="JSON 文件切片起点（含）")
    run.add_argument("--end", type=int, default=None, help="JSON 文件切片终点（不含）")
    run.add_argument("--skip-existing", action="store_true", help="已有 txt 则跳过")

    jev = sub.add_parser(
        "jev",
        help="调用 JEV (TypeSafe System One) Choice 模式分类警告，完整结果写入 response/",
    )
    jev.add_argument("--lang", choices=["java", "c"], required=True)
    jev.add_argument("--projects", nargs="+", default=["all"], help="Java 项目名，或 all")
    jev.add_argument("--tool", default="spotbugs", help="Java 静态分析工具目录名，默认 spotbugs")
    jev.add_argument(
        "--model",
        default="jev-latest",
        help="JEV 模型名，写入 response/<model>/，默认 jev-latest",
    )
    jev.add_argument("--api-key", default=None, help="覆盖 TYPESAFE_API_KEY")
    jev.add_argument("--base-url", default=None, help="覆盖 TypeSafe base URL")
    jev.add_argument("--start", type=int, default=None, help="JSON 文件切片起点（含）")
    jev.add_argument("--end", type=int, default=None, help="JSON 文件切片终点（不含）")
    jev.add_argument("--skip-existing", action="store_true", help="已有结果 json 则跳过")

    toexcel = sub.add_parser("toexcel", help="将 response/ 中的 txt 转为 excel，并链接人工标记")
    _add_common_experiment_args(toexcel)

    result = sub.add_parser("result", help="根据 excel 统计 Precision/Recall/F1")
    _add_common_experiment_args(result)
    result.add_argument("--by-tool", action="store_true")
    result.add_argument("--by-category", action="store_true")

    analysis = sub.add_parser("analysis", help="对 result excel 再按列聚合")
    analysis.add_argument("--lang", choices=["java", "c"], required=True)
    analysis.add_argument("--input", required=True, help="输入 excel，例如 c_result.xlsx")
    analysis.add_argument("--output", required=True, help="输出 excel")
    analysis.add_argument(
        "--group",
        nargs="+",
        required=True,
        help="分组列，例如: Prompts Technique  或  category Tool",
    )

    find_error = sub.add_parser("find-error", help="扫描 results/ 中 Status=error 的文件")
    find_error.add_argument("--root", default="results")

    recalc = sub.add_parser("recalculate", help="按 TP/TN/FP/FN 重算 Precision/Recall/F1")
    recalc.add_argument("--file", required=True)

    return parser


def cmd_run(args):
    spec = PROVIDERS[args.provider]
    model = args.model or spec["model"]
    model_fullname = args.model_fullname or spec["model_fullname"]
    url = args.url if args.url is not None else spec["url"]
    key = get_api_key(args.provider, args.api_key)
    client = build_client(args.provider, key, url, model_fullname)
    projects = resolve_list(args.projects, JAVA_PROJECTS)
    techniques = resolve_list(args.techniques, PROMPT_TECHNIQUES)
    run_experiments(
        client=client,
        model=model,
        lang=args.lang,
        projects=projects,
        techniques=techniques,
        tool=args.tool,
        start=args.start,
        end=args.end,
        skip_existing=args.skip_existing,
    )


def cmd_jev(args):
    from src.jev.client import JevClient
    from src.jev.pipeline import run_jev_experiments

    projects = resolve_list(args.projects, JAVA_PROJECTS)
    with JevClient(
        api_key=args.api_key,
        model=args.model,
        base_url=args.base_url,
    ) as client:
        run_jev_experiments(
            client=client,
            model=args.model,
            lang=args.lang,
            projects=projects,
            tool=args.tool,
            start=args.start,
            end=args.end,
            skip_existing=args.skip_existing,
        )


def cmd_toexcel(args):
    models = resolve_list(args.models, RESULT_MODELS) if args.models else list(RESULT_MODELS)
    projects = resolve_list(args.projects, JAVA_PROJECTS)
    techniques = resolve_list(args.techniques, PROMPT_TECHNIQUES)
    export_responses_to_excel(
        pl=args.lang,
        models=models,
        projects=None if args.lang == "c" else projects,
        prompts_techniques=techniques,
        tool=None if args.lang == "c" else args.tool,
    )


def cmd_result(args):
    models = resolve_list(args.models, RESULT_MODELS) if args.models else list(RESULT_MODELS)
    projects = resolve_list(args.projects, JAVA_PROJECTS)
    techniques = resolve_list(args.techniques, PROMPT_TECHNIQUES)
    get_result(
        by_tool=args.by_tool,
        by_category=args.by_category,
        pl=args.lang,
        models=models,
        projects=None if args.lang == "c" else projects,
        tool=None if args.lang == "c" else args.tool,
        prompts_techniques=techniques,
    )


def cmd_analysis(args):
    from src.analysis import process_category_c, process_category_java

    if args.lang == "c":
        process_category_c(args.input, args.output, args.group)
    else:
        process_category_java(args.input, args.output, args.group)


def cmd_find_error(args):
    from src.find_error import find_error_files

    find_error_files(args.root)


def cmd_recalculate(args):
    from src.analysis import recalculate_metrics

    recalculate_metrics(args.file)


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    commands = {
        "run": cmd_run,
        "jev": cmd_jev,
        "toexcel": cmd_toexcel,
        "result": cmd_result,
        "analysis": cmd_analysis,
        "find-error": cmd_find_error,
        "recalculate": cmd_recalculate,
    }
    commands[args.command](args)


def run_cli(default_provider):
    import sys

    argv = sys.argv[1:]
    subcommands = {
        "run",
        "jev",
        "toexcel",
        "result",
        "analysis",
        "find-error",
        "recalculate",
    }
    if not argv or argv[0] not in subcommands:
        argv = ["run", "--provider", default_provider, *argv]
    main(argv)


if __name__ == "__main__":
    main()
