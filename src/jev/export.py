"""Export JEV Choice / Score / Noul results to Excel and compare with manual labels."""

import csv
import json
import os
import re

from src.jev.questions import PRIMITIVE_DIRS

BUG_INDEX = re.compile(r"bug_(\d+)_")
SCORE_ACTIONABLE_THRESHOLD = 0.5
NOUL_ACTIONABLE_THRESHOLD = 0.5


def compare_prediction(prediction, groundtruth):
    """Map a binary prediction and a manual label onto a confusion-matrix cell.

    Manual labels follow the existing Java/C datasets:
    TP / True  = actionable warning
    FP / False = unactionable warning (analyzer false positive)
    """
    prediction = str(prediction or "").strip().lower()
    label = str(groundtruth or "").strip()
    positive = label in {"TP", "True", "true"}
    negative = label in {"FP", "False", "false"}

    if prediction not in {"actionable", "unactionable"} or not (positive or negative):
        return "error"
    if prediction == "actionable" and positive:
        return "TP"
    if prediction == "unactionable" and negative:
        return "TN"
    if prediction == "actionable" and negative:
        return "FP"
    return "FN"


# Backward-compatible alias used by older call sites / notebooks.
compare_choice = compare_prediction


def prediction_from_answer(primitive, answer):
    """Map a primitive answer onto actionable / unactionable."""
    answer = answer or {}
    primitive = str(primitive or answer.get("type") or "").strip().lower()

    if primitive == "choice":
        choice = str(answer.get("choice") or "").strip().lower()
        if choice in {"actionable", "unactionable"}:
            return choice
        return None

    if primitive == "score":
        try:
            score = float(answer.get("score"))
        except (TypeError, ValueError):
            return None
        return "actionable" if score >= SCORE_ACTIONABLE_THRESHOLD else "unactionable"

    if primitive == "noul":
        try:
            noul = float(answer.get("noul"))
        except (TypeError, ValueError):
            return None
        return "actionable" if noul >= NOUL_ACTIONABLE_THRESHOLD else "unactionable"

    return None


def _bug_index(file_name):
    match = BUG_INDEX.search(file_name)
    if not match:
        raise ValueError(f"无法从文件名解析警告序号: {file_name}")
    return int(match.group(1))


def _load_java_labels(project):
    path = os.path.join("report", "spotbugs_linked", f"{project}_linked.csv")
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_c_labels():
    path = os.path.join("report", "c_raw", "c.xlsx")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"未找到 C 人工标记文件: {path}")
    import pandas as pd

    frame = pd.read_excel(path)
    return frame.to_dict(orient="records")


def _label_for(labels, index):
    if index < 1 or index > len(labels):
        raise IndexError(f"警告序号 {index} 超出人工标记行数 {len(labels)}")
    row = labels[index - 1]
    for key in ("final_label", "Final Label", "label", "Label"):
        if key in row and str(row[key]) not in {"", "nan", "None"}:
            return row[key]
    raise KeyError("人工标记中没有 final_label 列")


def _detect_primitive(model, record):
    if record.get("primitive") in PRIMITIVE_DIRS:
        return record["primitive"]
    for primitive, directory in PRIMITIVE_DIRS.items():
        if model == directory:
            return primitive
    answer = record.get("answer") or {}
    answer_type = str(answer.get("type") or "").strip().lower()
    if answer_type in PRIMITIVE_DIRS:
        return answer_type
    if "choice" in answer:
        return "choice"
    if "score" in answer:
        return "score"
    if "noul" in answer:
        return "noul"
    return "choice"


def _answer_fields(primitive, answer):
    answer = answer or {}
    probabilities = answer.get("probabilities") or {}
    fields = {
        "primitive": primitive,
        "prediction": prediction_from_answer(primitive, answer),
        "choice": answer.get("choice"),
        "score": answer.get("score"),
        "noul": answer.get("noul"),
        "confidence": answer.get("confidence"),
        "prob_actionable": probabilities.get("actionable"),
        "prob_unactionable": probabilities.get("unactionable"),
        "prob_score_0": probabilities.get("0") if "0" in probabilities else probabilities.get(0),
        "prob_score_1": probabilities.get("1") if "1" in probabilities else probabilities.get(1),
    }
    return fields


def _iter_result_files(model, lang, projects, tool):
    if lang == "c":
        folder = os.path.join("response", model, "C_project")
        if os.path.isdir(folder):
            for name in sorted(os.listdir(folder)):
                if name.endswith(".json"):
                    yield "c", "C_project", os.path.join(folder, name)
        return

    root = os.path.join("response", model, tool)
    if not os.path.isdir(root):
        return
    selected = set(projects) if projects else None
    for project in sorted(os.listdir(root)):
        project_dir = os.path.join(root, project)
        if not os.path.isdir(project_dir):
            continue
        if selected is not None and project not in selected:
            continue
        for name in sorted(os.listdir(project_dir)):
            if name.endswith(".json"):
                yield lang, project, os.path.join(project_dir, name)


def export_jev_results(model, lang, projects=None, tool="spotbugs", output_excel=None):
    """Write one row per JEV result JSON that already exists on disk."""
    import pandas as pd

    if output_excel is None:
        output_excel = os.path.join("results", "jev", f"{lang}_{model}.xlsx")

    label_cache = {}
    rows = []
    for lang_name, project, path in _iter_result_files(model, lang, projects, tool):
        with open(path, "r", encoding="utf-8") as handle:
            record = json.load(handle)
        warning = record.get("warning") or {}
        file_name = os.path.splitext(os.path.basename(path))[0]
        if project not in label_cache:
            label_cache[project] = _load_c_labels() if lang_name == "c" else _load_java_labels(project)
        groundtruth = _label_for(label_cache[project], _bug_index(file_name))
        primitive = _detect_primitive(model, record)
        fields = _answer_fields(primitive, record.get("answer") or {})
        rows.append(
            {
                "file_name": file_name,
                "project": warning.get("project") or warning.get("Project") or project,
                "category": warning.get("category"),
                "vtype": warning.get("vtype"),
                "priority": warning.get("priority"),
                "rank": warning.get("rank"),
                "primitive": fields["primitive"],
                "prediction": fields["prediction"],
                "choice": fields["choice"],
                "score": fields["score"],
                "noul": fields["noul"],
                "confidence": fields["confidence"],
                "prob_actionable": fields["prob_actionable"],
                "prob_unactionable": fields["prob_unactionable"],
                "prob_score_0": fields["prob_score_0"],
                "prob_score_1": fields["prob_score_1"],
                "groundtruth": groundtruth,
                "comparison": compare_prediction(fields["prediction"], groundtruth),
            }
        )

    os.makedirs(os.path.dirname(output_excel) or ".", exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_excel(output_excel, index=False)
    print(f"已写入 {len(frame)} 行到 {output_excel}")
    return output_excel


def export_all_primitives(lang, projects=None, tool="spotbugs", output_dir=None):
    """Export Choice / Score / Noul result directories into separate Excel files."""
    output_dir = output_dir or os.path.join("results", "jev")
    written = []
    for primitive, directory in PRIMITIVE_DIRS.items():
        output_excel = os.path.join(output_dir, f"{lang}_{directory}.xlsx")
        path = export_jev_results(
            model=directory,
            lang=lang,
            projects=projects,
            tool=tool,
            output_excel=output_excel,
        )
        written.append((primitive, path))
    return written
