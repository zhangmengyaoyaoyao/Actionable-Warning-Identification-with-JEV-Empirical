import os

from src.config import JAVA_PROJECTS, PROMPT_TECHNIQUES, RESULT_MODELS
from src.response2excel import (
    link_excel,
    process_txt_files,
    process_txt_files_with_2history,
    process_txt_files_with_3history,
)


def excel_paths(pl, model, project, prompts_technique, tool="spotbugs"):
    if pl == "java":
        folder_path = f"response/{model}/{tool}/{prompts_technique}/{project}"
        output_excel = f"results/{pl}/{project}/{model}/{pl}_{prompts_technique}_{project}_{model}.xlsx"
    elif pl == "c":
        folder_path = f"response/{model}/{tool}/{prompts_technique}"
        output_excel = f"results/{pl}/{model}/{pl}_{prompts_technique}_{model}.xlsx"
    else:
        raise ValueError(f"unknown language: {pl}")
    return folder_path, output_excel


def export_responses_to_excel(
    pl="java",
    models=None,
    projects=None,
    prompts_techniques=None,
    tool=None,
):
    models = models or list(RESULT_MODELS)
    prompts_techniques = prompts_techniques or list(PROMPT_TECHNIQUES)

    if pl == "c":
        tool = tool or "C_project"
        projects = projects or ["C_project"]
        link_excel_path = "report/c_raw"
    elif pl == "java":
        tool = tool or "spotbugs"
        projects = projects or list(JAVA_PROJECTS)
        link_excel_path = "report/spotbugs_linked"
    else:
        raise ValueError(f"unknown language: {pl}")

    for model in models:
        for project in projects:
            for prompts_technique in prompts_techniques:
                print(prompts_technique)
                folder_path, output_excel = excel_paths(pl, model, project, prompts_technique, tool)
                if not os.path.isdir(folder_path):
                    print(f"skip missing folder: {folder_path}")
                    continue

                output_dir = os.path.dirname(output_excel)
                os.makedirs(output_dir, exist_ok=True)

                if prompts_technique == "critique":
                    process_txt_files_with_3history(folder_path, output_excel)
                elif prompts_technique == "self_heuristic":
                    process_txt_files_with_2history(folder_path, output_excel)
                else:
                    process_txt_files(folder_path, output_excel)

                if pl == "c":
                    link_excel(os.path.join(link_excel_path, "c.xlsx"), output_excel)
                elif pl == "java":
                    link_excel(os.path.join(link_excel_path, f"{project}_linked.csv"), output_excel)
