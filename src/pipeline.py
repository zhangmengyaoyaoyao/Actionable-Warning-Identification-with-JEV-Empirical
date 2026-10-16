import glob
import json
import os
import time

from src.config import MULTI_TURN_TECHNIQUES
from src.construct_prompts import C_Constructor, Java_Constructor
from src.llm.clients import history_content


def response_output_dir(model, tool, prompts_technique, project_name):
    if project_name == "unknown":
        return os.path.join("response", model, "C_project", prompts_technique)
    return os.path.join("response", model, tool, prompts_technique, project_name)


def make_constructor(project_name):
    if project_name == "unknown":
        return C_Constructor()
    return Java_Constructor()


def process_project_files(
    client,
    model,
    tool,
    prompts_technique,
    project_name,
    project_path,
    start=None,
    end=None,
    skip_existing=False,
):
    json_files = sorted(glob.glob(os.path.join(project_path, "*.json")))
    if not json_files:
        print(f"No JSON files found for project {project_name} in {project_path}.")
        return

    if start is not None or end is not None:
        json_files = json_files[start:end]

    constructor = make_constructor(project_name)
    output_dir = response_output_dir(model, tool, prompts_technique, project_name)
    os.makedirs(output_dir, exist_ok=True)

    current_tool = tool
    current_project = project_name

    for json_file in json_files:
        print(f"Processing file: {json_file}")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        json_content = json.dumps(data, indent=2)

        if current_tool != "spotbugs":
            current_tool = data["Tool"]
            current_project = data["Project"]
        constructor.setGeneralInfo(current_tool, current_project)
        constructor.setWarning(json_content)

        base_name = os.path.splitext(os.path.basename(json_file))[0]
        txt_file = os.path.join(output_dir, f"{base_name}.txt")
        if skip_existing and os.path.exists(txt_file):
            print(f"skip existing: {txt_file}")
            continue

        flag_noResponse = True
        history_response = []
        response = None
        while flag_noResponse:
            try:
                messages = constructor.construct(prompts_technique)
            except ValueError as exc:
                print(str(exc))
                return

            if prompts_technique == "critique":
                response, history_response = client.call_with_3messages(messages)
            elif prompts_technique == "self_heuristic":
                response, history_response = client.call_with_2messages(messages)
            else:
                response = client.call_with_message(messages)

            if client.is_valid(response):
                flag_noResponse = False
            else:
                print("Error: The response or its expected structure is invalid.")
                time.sleep(client.retry_sleep)

        content = client.get_content(response)
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(content)

        if prompts_technique in MULTI_TURN_TECHNIQUES:
            history_file = os.path.join(output_dir, f"{base_name}_history.txt")
            with open(history_file, "a", encoding="utf-8") as f:
                count = 1
                for history in history_response:
                    f.write(f'response{count}:\n{history_content(history)}\n\n\n')
                    count += 1
            print(f"history store to: {output_dir}/{base_name}_history.txt")

        print(f"store to: {output_dir}/{base_name}.txt")


def run_experiments(client, model, lang, projects, techniques, tool="spotbugs", start=None, end=None, skip_existing=False):
    if lang == "c":
        project_path = os.path.join("report", "c_json")
        for prompts_technique in techniques:
            print(f"Processing C_project with {prompts_technique}")
            process_project_files(
                client=client,
                model=model,
                tool="unknown",
                prompts_technique=prompts_technique,
                project_name="unknown",
                project_path=project_path,
                start=start,
                end=end,
                skip_existing=skip_existing,
            )
        return

    for project in projects:
        project_path = os.path.join("report", tool, project)
        for prompts_technique in techniques:
            print(f"Processing project {project} with {prompts_technique}")
            process_project_files(
                client=client,
                model=model,
                tool=tool,
                prompts_technique=prompts_technique,
                project_name=project,
                project_path=project_path,
                start=start,
                end=end,
                skip_existing=skip_existing,
            )
