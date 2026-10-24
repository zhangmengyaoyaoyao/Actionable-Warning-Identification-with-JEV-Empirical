"""Run JEV Choice / Score / Noul over warning JSON files and store full results."""

import glob
import json
import os
from datetime import datetime, timezone

from src.jev.client import JevClient
from src.jev.questions import PRIMITIVE_DIRS


def jev_output_dir(primitive_dir, tool, project_name):
    """
    Output layout (one top-level directory per primitive):

    Java: response/<jev-choice|jev-score|jev-noul>/<tool>/<project>/
    C:    response/<jev-choice|jev-score|jev-noul>/C_project/
    """
    if project_name == "unknown":
        return os.path.join("response", primitive_dir, "C_project")
    return os.path.join("response", primitive_dir, tool, project_name)


def _output_paths(tool, project_name, base_name):
    paths = {}
    for primitive, primitive_dir in PRIMITIVE_DIRS.items():
        folder = jev_output_dir(primitive_dir, tool, project_name)
        os.makedirs(folder, exist_ok=True)
        paths[primitive] = os.path.join(folder, f"{base_name}.json")
    return paths


def _summarize_answer(primitive, answer):
    if not answer:
        return ""
    if primitive == "choice":
        return f"choice={answer.get('choice')} confidence={answer.get('confidence')}"
    if primitive == "score":
        return f"score={answer.get('score')} confidence={answer.get('confidence')}"
    if primitive == "noul":
        return f"noul={answer.get('noul')}"
    return ""


def process_project_files(
    client: JevClient,
    tool: str,
    project_name: str,
    project_path: str,
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

    for json_file in json_files:
        print(f"Processing file: {json_file}")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # State passed to JEV: full warning JSON as text.
        state = json.dumps(data, indent=2, ensure_ascii=False)

        base_name = os.path.splitext(os.path.basename(json_file))[0]
        out_paths = _output_paths(tool, project_name, base_name)

        if skip_existing and all(os.path.exists(path) for path in out_paths.values()):
            print(f"skip existing: {base_name} (choice/score/noul all present)")
            continue

        result = client.classify_warning(state)
        created_at = datetime.now(timezone.utc).isoformat()
        source_file = json_file.replace("\\", "/")
        request = result.get("request")
        response = result.get("response")
        answers = result.get("answers") or {}

        for primitive, out_file in out_paths.items():
            answer = answers.get(primitive)
            record = {
                "source_file": source_file,
                "warning": data,
                "created_at": created_at,
                "primitive": primitive,
                "request": request,
                "response": response,
                "answer": answer,
            }
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, ensure_ascii=False)
            summary = _summarize_answer(primitive, answer)
            print(f"store to: {out_file}" + (f" | {summary}" if summary else ""))


def run_jev_experiments(
    client: JevClient,
    lang: str,
    projects,
    tool="spotbugs",
    start=None,
    end=None,
    skip_existing=False,
    model=None,  # kept for backward-compatible callers; unused for output dirs
):
    del model  # API model lives on the client; output dirs are primitive-based.
    if lang == "c":
        project_path = os.path.join("report", "c_json")
        print("Processing C_project with JEV Choice / Score / Noul")
        process_project_files(
            client=client,
            tool="unknown",
            project_name="unknown",
            project_path=project_path,
            start=start,
            end=end,
            skip_existing=skip_existing,
        )
        return

    for project in projects:
        project_path = os.path.join("report", tool, project)
        print(f"Processing project {project} with JEV Choice / Score / Noul")
        process_project_files(
            client=client,
            tool=tool,
            project_name=project,
            project_path=project_path,
            start=start,
            end=end,
            skip_existing=skip_existing,
        )
