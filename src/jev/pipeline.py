"""Run JEV Choice classification over warning JSON files and store full results."""

import glob
import json
import os
from datetime import datetime, timezone

from src.jev.client import JevClient


def jev_output_dir(model, tool, project_name):
    """
    Output layout (no prompt-technique layer; JEV uses a fixed Choice question):

    Java: response/<model>/<tool>/<project>/
    C:    response/<model>/C_project/
    """
    if project_name == "unknown":
        return os.path.join("response", model, "C_project")
    return os.path.join("response", model, tool, project_name)


def process_project_files(
    client: JevClient,
    model: str,
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

    output_dir = jev_output_dir(model, tool, project_name)
    os.makedirs(output_dir, exist_ok=True)

    for json_file in json_files:
        print(f"Processing file: {json_file}")
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # State passed to JEV: full warning JSON as text (same content used for LLMs).
        state = json.dumps(data, indent=2, ensure_ascii=False)

        base_name = os.path.splitext(os.path.basename(json_file))[0]
        out_file = os.path.join(output_dir, f"{base_name}.json")
        if skip_existing and os.path.exists(out_file):
            print(f"skip existing: {out_file}")
            continue

        result = client.classify_warning(state)
        record = {
            "source_file": json_file.replace("\\", "/"),
            "warning": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
            **result,
        }

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        answer = record.get("answer") or {}
        choice = answer.get("choice")
        confidence = answer.get("confidence")
        print(
            f"store to: {out_file}"
            + (f" | choice={choice} confidence={confidence}" if choice is not None else "")
        )


def run_jev_experiments(
    client: JevClient,
    model: str,
    lang: str,
    projects,
    tool="spotbugs",
    start=None,
    end=None,
    skip_existing=False,
):
    if lang == "c":
        project_path = os.path.join("report", "c_json")
        print("Processing C_project with JEV Choice")
        process_project_files(
            client=client,
            model=model,
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
        print(f"Processing project {project} with JEV Choice")
        process_project_files(
            client=client,
            model=model,
            tool=tool,
            project_name=project,
            project_path=project_path,
            start=start,
            end=end,
            skip_existing=skip_existing,
        )
