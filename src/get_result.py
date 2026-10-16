import pandas as pd
import os
import re

from src.config import JAVA_PROJECTS, PROMPT_TECHNIQUES, RESULT_MODELS
from src.postprocess import excel_paths

sample_warning_c = ["bug_0432_binutils", "bug_0943_combine", "bug_0409_bash", "bug_0432_binutils", "bug_1054_gawk"]
sample_warning_java = ["bug_0002_bcel", "bug_0869_mavendp", "bug_0668_net", "bug_0001_configuration", "bug_0001_pool"]
# Map category to groups
category_group_mapping = {
        "arrayIndexOutOfBounds": "BOF", "arrayIndexOutOfBoundsCond": "BOF", "Buffer Overrun L2": "BOF", "Buffer Overrun L3": "BOF", 
        "BUFFER_OVERRUN_L1": "BOF", "BUFFER_OVERRUN_L2": "BOF", "BUFFER_OVERRUN_L3": "BOF", "BUFFER_OVERRUN_S2": "BOF", "bufferAccessOutOfBounds": "BOF", 
        "core.CallAndMessage": "NPD", "core.DivideZero": "DBZ", "core.NullDereference": "NPD", "core.UndefinedBinaryOperatorResult": "DBZ", 
        "core.uninitialized.Assign": "UVA", "core.uninitialized.Branch": "UVA", "ctuArrayIndex": "BOF", "Divide By Zero": "DBZ", 
        "memleak": "ML", "memleakOnRealloc": "ML", "negativeIndex": "BOF", "Null Dereference": "NPD", "Null Pointer Dereference": "NPD", 
        "NULL_DEREFERENCE": "NPD", "nullPointerArithmeticRedundantCheck": "NPD", "uninitdata": "UVA", "Uninitialized Value": "UVA", 
        "Uninitialized Variable": "UVA", "UNINITIALIZED_VALUE": "UVA", "uninitvar": "UVA", "unix.Malloc": "ML"
    }
# def update_consistent_column(input_excel, result_data, model, project, prompts_technique):
#     df = pd.read_excel(input_excel)
    
#     if project == "C_project": #c
#         for sample in sample_warning_c:
#             df = df[~df['File Name'].str.startswith(sample)]
#         tp_label = True
#         fp_label = False
#     else: # java
#         for sample in sample_warning_java:
#             df = df[~df['File Name'].str.startswith(sample)]
#         tp_label = "TP"
#         fp_label = "FP"

#     # 统计 TP, TN, FP, FN
#     total = 0
#     unknown = 0
#     tp = fn = fp = tn = 0

#     for _, row in df.iterrows():
#         total += 1
#         status_val = row['Status']
#         status_val = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', str(status_val))

#         if status_val == 'actionable,' or status_val == 'actionable.' or status_val == 'potentially actionable':
#             status_val = 'actionable'
#         elif status_val == 'unactionable,' or status_val == 'unactionable.':
#             status_val = 'unactionable'

#         if status_val == 'actionable' and row['final_label'] == tp_label:
#             tp += 1
#         elif status_val == 'unactionable' and row['final_label'] == fp_label:
#             tn += 1
#         elif status_val == 'actionable' and row['final_label'] == fp_label:
#             fp += 1
#         elif status_val == 'unactionable' and row['final_label'] == tp_label:
#             fn += 1
#         elif status_val == 'unknown':
#             unknown += 1
#             # 保守估计: unknown 作为错误答案
#             if row['final_label'] == tp_label:
#                 fn += 1  # 真实为 TP，未能正确检测，视为 FN
#             else:
#                 fp += 1  # 真实为 FP，未能正确检测，视为 FP
#         else:
#             print(f"Error:{status_val}:{row['final_label']}.")
#             unknown += 1
#             # 保守估计: unknown 作为错误答案
#             if row['final_label'] == tp_label:
#                 fn += 1  # 真实为 TP，未能正确检测，视为 FN
#             else:
#                 fp += 1  # 真实为 FP，未能正确检测，视为 FP


#     sum_tpfp = tp + fp
#     sum_tpfn = tp + fn
#     sum_tptn = tp + tn
    
#     # 计算 Precision, Accuracy, Recall
#     precision = tp / (tp + fp) if (tp + fp) > 0 else 0
#     recall = tp / (tp + fn) if (tp + fn) > 0 else 0
#     accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
#     f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

#     # 存储统计数据
#     result_data.append({
#         'Model': model,
#         'Project': project,
#         'Prompts Technique': prompts_technique,
#         'TP': tp,
#         'TN': tn,
#         'FP': fp,
#         'FN': fn,
#         'sum_tpfp': sum_tpfp,
#         'sum_tpfn': sum_tpfn,
#         'sum_tptn': sum_tptn,
#         'Precision': f"{precision:.2f}",
#         'Accuracy': f"{accuracy:.2f}",
#         'Recall': f"{recall:.2f}",
#         'F1 Score': f"{f1_score:.2f}",
#         'Total': total,
#         'Unknown': unknown
#     })

# def update_consistent_column_tool(input_excel, result_data, model, project, prompts_technique):
#     df = pd.read_excel(input_excel)

#     if project == "C_project": #c
#         for sample in sample_warning_c:
#             df = df[~df['File Name'].str.startswith(sample)]
#         tp_label = True
#         fp_label = False
#     else: # java
#         for sample in sample_warning_java:
#             df = df[~df['File Name'].str.startswith(sample)]
#         tp_label = "TP"
#         fp_label = "FP"

#     # 统计 TP, TN, FP, FN
#     total = 0
#     unknown = 0
#     tp = fn = fp = tn = 0
#     data_dict = {}

#     # 按照 Tool 进行分类
#     for tool_name in df["Tool"].unique():
#         df_tool = df[df["Tool"] == tool_name]

#         total_tool = 0
#         unknown_tool = 0
#         tp_tool = fn_tool = fp_tool = tn_tool = 0

#         for _, row in df_tool.iterrows():
#             total_tool += 1
#             status_val = row['Status']
#             status_val = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', str(status_val))

#             if status_val in ['actionable,', 'actionable.', 'potentially actionable']:
#                 status_val = 'actionable'
#             elif status_val in ['unactionable,', 'unactionable.']:
#                 status_val = 'unactionable'

#             if status_val == 'actionable' and row['final_label'] == tp_label:
#                 tp_tool += 1
#             elif status_val == 'unactionable' and row['final_label'] == fp_label:
#                 tn_tool += 1
#             elif status_val == 'actionable' and row['final_label'] == fp_label:
#                 fp_tool += 1
#             elif status_val == 'unactionable' and row['final_label'] == tp_label:
#                 fn_tool += 1
#             elif status_val == 'unknown':
#                 unknown_tool += 1
#                 # 保守估计: unknown 作为错误答案
#                 if row['final_label'] == tp_label:
#                     fn_tool += 1  # 真实为 TP，未能正确检测，视为 FN
#                 else:
#                     fp_tool += 1  # 真实为 FP，未能正确检测，视为 FP
#             else:
#                 print(f"Error:{status_val}:{row['final_label']}.")
#                 unknown_tool += 1
#                 # 保守估计: unknown 作为错误答案
#                 if row['final_label'] == tp_label:
#                     fn_tool += 1  # 真实为 TP，未能正确检测，视为 FN
#                 else:
#                     fp_tool += 1  # 真实为 FP，未能正确检测，视为 FP

#         # 汇总每个工具的数据
#         sum_tpfp = tp_tool + fp_tool
#         sum_tpfn = tp_tool + fn_tool
#         sum_tptn = tp_tool + tn_tool

#         # 计算 Precision, Recall, f1
#         precision_tool = tp_tool / (tp_tool + fp_tool) if (tp_tool + fp_tool) > 0 else 0
#         recall_tool = tp_tool / (tp_tool + fn_tool) if (tp_tool + fn_tool) > 0 else 0
#         f1_score_tool = (2 * precision_tool * recall_tool) / (precision_tool + recall_tool) if (precision_tool + recall_tool) > 0 else 0
        
#         # 合并数据到字典中，使用 (Model, Tool, Prompts Technique) 作为 key
#         key = (model, tool_name, prompts_technique)
#         if key not in data_dict:
#             data_dict[key] = {
#                 'TP': 0, 'TN': 0, 'FP': 0, 'FN': 0,
#                 'sum_tpfp': 0, 'sum_tpfn': 0, 'sum_tptn': 0,
#                 'precision': 0, 'accuracy': 0, 'recall': 0, 'f1_score': 0,
#                 'total': 0, 'unknown': 0
#             }
        
#         data_dict[key]['TP'] += tp_tool
#         data_dict[key]['TN'] += tn_tool
#         data_dict[key]['FP'] += fp_tool
#         data_dict[key]['FN'] += fn_tool
#         data_dict[key]['sum_tpfp'] += sum_tpfp
#         data_dict[key]['sum_tpfn'] += sum_tpfn
#         data_dict[key]['sum_tptn'] += sum_tptn
#         data_dict[key]['precision'] = (data_dict[key]['TP'] / (data_dict[key]['TP'] + data_dict[key]['FP'])) if (data_dict[key]['TP'] + data_dict[key]['FP']) > 0 else 0
#         data_dict[key]['recall'] = (data_dict[key]['TP'] / (data_dict[key]['TP'] + data_dict[key]['FN'])) if (data_dict[key]['TP'] + data_dict[key]['FN']) > 0 else 0
#         data_dict[key]['f1_score'] = (2 * data_dict[key]['precision'] * data_dict[key]['recall']) / (data_dict[key]['precision'] + data_dict[key]['recall']) if (data_dict[key]['precision'] + data_dict[key]['recall']) > 0 else 0
#         data_dict[key]['total'] += total_tool
#         data_dict[key]['unknown'] += unknown_tool

#     # 将汇总的数据转换为 result_data 格式
#     for key, values in data_dict.items():
#         model, tool_name, prompts_technique = key
#         tp = values['TP']
#         tn = values['TN']
#         fp = values['FP']
#         fn = values['FN']
#         sum_tpfp = values['sum_tpfp']
#         sum_tpfn = values['sum_tpfn']
#         sum_tptn = values['sum_tptn']
#         precision = values['precision']
#         recall = values['recall']
#         f1_score = values['f1_score']
#         total = values['total']
#         unknown = values['unknown']

#         result_data.append({
#             'Model': model,
#             'Tool': tool_name,
#             'Prompts Technique': prompts_technique,
#             'TP': tp,
#             'TN': tn,
#             'FP': fp,
#             'FN': fn,
#             'sum_tpfp': sum_tpfp,
#             'sum_tpfn': sum_tpfn,
#             'sum_tptn': sum_tptn,
#             'Precision': f"{precision:.4f}",
#             'Recall': f"{recall:.4f}",
#             'F1 Score': f"{f1_score:.4f}",
#             'Total': total,
#             'Unknown': unknown
#         })
    
# def update_consistent_column_category(input_excel, result_data, model, project, prompts_technique):
   
#     df = pd.read_excel(input_excel)

#     if project == "C_project":
#         tp_label = True
#         fp_label = False
#     else:
#         tp_label = "TP"
#         fp_label = "FP"

#     # 统计 TP, TN, FP, FN
#     total = 0
#     unknown = 0
#     tp = fn = fp = tn = 0

#     # 按照 category 进行分类
#     for category_name in df["category"].unique():
#         df_category = df[df["category"] == category_name]

#         total = 0
#         unknown = 0
#         tp = fn = fp = tn = 0

#         for _, row in df_category.iterrows():
#             total += 1
#             status_val = row['Status']
#             status_val = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', str(status_val))

#             if status_val in ['actionable,', 'actionable.', 'potentially actionable']:
#                 status_val = 'actionable'
#             elif status_val in ['unactionable,', 'unactionable.']:
#                 status_val = 'unactionable'

#             if status_val == 'actionable' and row['final_label'] == tp_label:
#                 tp += 1
#             elif status_val == 'unactionable' and row['final_label'] == fp_label:
#                 tn += 1
#             elif status_val == 'actionable' and row['final_label'] == fp_label:
#                 fp += 1
#             elif status_val == 'unactionable' and row['final_label'] == tp_label:
#                 fn += 1
#             elif status_val == 'unknown':
#                 unknown += 1
#                 # 保守估计: unknown 作为错误答案
#                 if row['final_label'] == tp_label:
#                     fn += 1  # 真实为 TP，未能正确检测，视为 FN
#                 else:
#                     fp += 1  # 真实为 FP，未能正确检测，视为 FP
#             else:
#                 print(f"Error:{status_val}:{row['final_label']}.")
#                 unknown += 1
#                 # 保守估计: unknown 作为错误答案
#                 if row['final_label'] == tp_label:
#                     fn += 1  # 真实为 TP，未能正确检测，视为 FN
#                 else:
#                     fp += 1  # 真实为 FP，未能正确检测，视为 FP

#         sum_tpfp = tp + fp
#         sum_tpfn = tp + fn
#         sum_tptn = tp + tn

#         # 计算 Precision, Accuracy, Recall
#         precision = tp / (tp + fp) if (tp + fp) > 0 else 0
#         recall = tp / (tp + fn) if (tp + fn) > 0 else 0
#         accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
#         f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

#         # 存储统计数据
#         result_data.append({
#             'Model': model,
#             'Project': project,
#             'category': category_name, 
#             'Prompts Technique': prompts_technique,
#             'TP': tp,
#             'TN': tn,
#             'FP': fp,
#             'FN': fn,
#             'sum_tpfp': sum_tpfp,
#             'sum_tpfn': sum_tpfn,
#             'sum_tptn': sum_tptn,
#             'Precision': f"{precision:.3f}",
#             'Accuracy': f"{accuracy:.3f}",
#             'Recall': f"{recall:.3f}",
#             'F1 Score': f"{f1_score:.3f}",
#             'Total': total,
#             'Unknown': unknown
#         })

# def update_consistent_column_mapcategory(input_excel, result_data, model, project, prompts_technique):
#     category_group_mapping = {
#         "arrayIndexOutOfBounds": "BOF", "arrayIndexOutOfBoundsCond": "BOF", "Buffer Overrun L2": "BOF", "Buffer Overrun L3": "BOF", 
#         "BUFFER_OVERRUN_L1": "BOF", "BUFFER_OVERRUN_L2": "BOF", "BUFFER_OVERRUN_L3": "BOF", "BUFFER_OVERRUN_S2": "BOF", "bufferAccessOutOfBounds": "BOF", 
#         "core.CallAndMessage": "NPD", "core.DivideZero": "DBZ", "core.NullDereference": "NPD", "core.UndefinedBinaryOperatorResult": "DBZ", 
#         "core.uninitialized.Assign": "UVA", "core.uninitialized.Branch": "UVA", "ctuArrayIndex": "BOF", "Divide By Zero": "DBZ", 
#         "memleak": "ML", "memleakOnRealloc": "ML", "negativeIndex": "BOF", "Null Dereference": "NPD", "Null Pointer Dereference": "NPD", 
#         "NULL_DEREFERENCE": "NPD", "nullPointerArithmeticRedundantCheck": "NPD", "uninitdata": "UVA", "Uninitialized Value": "UVA", 
#         "Uninitialized Variable": "UVA", "UNINITIALIZED_VALUE": "UVA", "uninitvar": "UVA", "unix.Malloc": "ML"
#     }
    
#     df = pd.read_excel(input_excel)

#     df["group"] = df["category"].map(category_group_mapping).fillna("Other")

#     if project == "C_project":
#         tp_label = True
#         fp_label = False
#     else:
#         tp_label = "TP"
#         fp_label = "FP"
    
#     # 统计各组别的 TP, TN, FP, FN
#     for group_name in df["group"].unique():
#         df_group = df[df["group"] == group_name]

#         total = 0
#         unknown = 0
#         tp = fn = fp = tn = 0

#         for _, row in df_group.iterrows():
#             total += 1
#             status_val = row['Status']
#             status_val = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', str(status_val))

#             if status_val in ['actionable,', 'actionable.', 'potentially actionable']:
#                 status_val = 'actionable'
#             elif status_val in ['unactionable,', 'unactionable.']:
#                 status_val = 'unactionable'

#             if status_val == 'actionable' and row['final_label'] == tp_label:
#                 tp += 1
#             elif status_val == 'unactionable' and row['final_label'] == fp_label:
#                 tn += 1
#             elif status_val == 'actionable' and row['final_label'] == fp_label:
#                 fp += 1
#             elif status_val == 'unactionable' and row['final_label'] == tp_label:
#                 fn += 1
#             elif status_val == 'unknown':
#                 unknown += 1
#                 if row['final_label'] == tp_label:
#                     fn += 1
#                 else:
#                     fp += 1
#             else:
#                 print(f"Error:{status_val}:{row['final_label']}.")
#                 unknown += 1
#                 if row['final_label'] == tp_label:
#                     fn += 1
#                 else:
#                     fp += 1

#         sum_tpfp = tp + fp
#         sum_tpfn = tp + fn
#         sum_tptn = tp + tn

#         precision = tp / sum_tpfp if sum_tpfp > 0 else 0
#         recall = tp / sum_tpfn if sum_tpfn > 0 else 0
#         accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
#         f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

#         result_data.append({
#             'Model': model,
#             'Project': project,
#             'Prompts Technique': prompts_technique,
#             'category': group_name,
#             'TP': tp,
#             'TN': tn,
#             'FP': fp,
#             'FN': fn,
#             'sum_tpfp': sum_tpfp,
#             'sum_tpfn': sum_tpfn,
#             'sum_tptn': sum_tptn,
#             'Precision': f"{precision:.3f}",
#             'Accuracy': f"{accuracy:.3f}",
#             'Recall': f"{recall:.3f}",
#             'F1 Score': f"{f1_score:.3f}",
#             'Total': total,
#             'Unknown': unknown
#         })

# Helper function to clean up status
def clean_status(status_val):
    status_val = re.sub(r'^[^a-zA-Z0-9]+|[^a-zA-Z0-9]+$', '', str(status_val))
    if status_val in ['actionable,', 'actionable.', 'potentially actionable']:
        return 'actionable'
    elif status_val in ['unactionable,', 'unactionable.']:
        return 'unactionable'
    return status_val

# Helper function to calculate TP, TN, FP, FN
def calculate_metrics(df, tp_label, fp_label):
    tp = fn = fp = tn = unknown = total = 0

    for _, row in df.iterrows():
        total += 1
        status_val = clean_status(row['Status'])

        if status_val == 'actionable' and row['final_label'] == tp_label:
            tp += 1
        elif status_val == 'unactionable' and row['final_label'] == fp_label:
            tn += 1
        elif status_val == 'actionable' and row['final_label'] == fp_label:
            fp += 1
        elif status_val == 'unactionable' and row['final_label'] == tp_label:
            fn += 1
        elif status_val == 'unknown':
            unknown += 1
            if row['final_label'] == tp_label:
                fn += 1
            else:
                fp += 1
        else:
            print(f"Error:{status_val}:{row['final_label']}.")
            unknown += 1
            if row['final_label'] == tp_label:
                fn += 1
            else:
                fp += 1

    return tp, tn, fp, fn, unknown, total

# Helper function to calculate precision, recall, accuracy, and F1 score
def calculate_metrics_values(tp, tn, fp, fn):
    sum_tpfp = tp + fp
    sum_tpfn = tp + fn
    sum_tptn = tp + tn

    precision = tp / sum_tpfp if sum_tpfp > 0 else 0
    recall = tp / sum_tpfn if sum_tpfn > 0 else 0
    f1_score = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return precision, recall, f1_score, sum_tpfp, sum_tpfn, sum_tptn


# Helper function to process the rows based on category or group
def process_rows(df, group_by_field, model, prompts_technique, result_data, tp_label, fp_label):
    data_dict = {}

    if group_by_field in (None, "None"):
        tp, tn, fp, fn, unknown, total = calculate_metrics(df, tp_label, fp_label)
        precision, recall, f1_score, sum_tpfp, sum_tpfn, sum_tptn = calculate_metrics_values(tp, tn, fp, fn)
        result_data.append({
            'Model': model,
            'Prompts Technique': prompts_technique,
            'TP': tp,
            'TN': tn,
            'FP': fp,
            'FN': fn,
            'sum_tpfp': sum_tpfp,
            'sum_tpfn': sum_tpfn,
            'sum_tptn': sum_tptn,
            'Precision': f"{precision:.4f}",
            'Recall': f"{recall:.4f}",
            'F1 Score': f"{f1_score:.4f}",
            'Total': total,
            'Unknown': unknown
        })
        return

    if group_by_field == "category" and tp_label == True:
        df['category'] = df['category'].map(category_group_mapping).fillna("Other")

    # Loop through each category/group
    for group_name in df[group_by_field].unique():
        df_group = df[df[group_by_field] == group_name]

        tp, tn, fp, fn, unknown, total = calculate_metrics(df_group, tp_label, fp_label)

        key = (model, prompts_technique, group_name)

        if key not in data_dict:
            data_dict[key] = {'TP': 0, 'TN': 0, 'FP': 0, 'FN': 0, 'Total': 0, 'Unknown': 0}

        data_dict[key]['TP'] += tp
        data_dict[key]['TN'] += tn
        data_dict[key]['FP'] += fp
        data_dict[key]['FN'] += fn
        data_dict[key]['Total'] += total
        data_dict[key]['Unknown'] += unknown

    # Calculate and store results for each aggregation
    for key, values in data_dict.items():
        tp = values['TP']
        tn = values['TN']
        fp = values['FP']
        fn = values['FN']
        total = values['Total']
        unknown = values['Unknown']

        precision, recall, f1_score, sum_tpfp, sum_tpfn, sum_tptn = calculate_metrics_values(tp, tn, fp, fn)
        result_data.append({
            'Model': model,
            'Prompts Technique': prompts_technique,
            group_by_field: key[2],  # Use the group name (e.g., Tool or category)
            'TP': tp,
            'TN': tn,
            'FP': fp,
            'FN': fn,
            'sum_tpfp': sum_tpfp,
            'sum_tpfn': sum_tpfn,
            'sum_tptn': sum_tptn,
            'Precision': f"{precision:.4f}",
            'Recall': f"{recall:.4f}",
            'F1 Score': f"{f1_score:.4f}",
            'Total': total,
            'Unknown': unknown
        })

# Helper function to process the rows based on category and group
def process_rows_double(df, group_by_field1, group_by_field2, model, prompts_technique, result_data, tp_label, fp_label):
    data_dict = {}

    if (group_by_field1 == "category" or group_by_field2 == "category") and tp_label == True:
        df['category'] = df['category'].map(category_group_mapping).fillna("Other")

    # Loop through each combination of group_by_field1 and group_by_field2
    for group_name1 in df[group_by_field1].unique():
        for group_name2 in df[group_by_field2].unique():
            df_group = df[(df[group_by_field1] == group_name1) & (df[group_by_field2] == group_name2)]

            tp, tn, fp, fn, unknown, total = calculate_metrics(df_group, tp_label, fp_label)

            key = (model, prompts_technique, group_name1, group_name2)

            if key not in data_dict:
                data_dict[key] = {'TP': 0, 'TN': 0, 'FP': 0, 'FN': 0, 'Total': 0, 'Unknown': 0}

            data_dict[key]['TP'] += tp
            data_dict[key]['TN'] += tn
            data_dict[key]['FP'] += fp
            data_dict[key]['FN'] += fn
            data_dict[key]['Total'] += total
            data_dict[key]['Unknown'] += unknown

    # Calculate and store results for each aggregation
    for key, values in data_dict.items():
        tp = values['TP']
        tn = values['TN']
        fp = values['FP']
        fn = values['FN']
        total = values['Total']
        unknown = values['Unknown']

        precision, recall, f1_score, sum_tpfp, sum_tpfn, sum_tptn = calculate_metrics_values(tp, tn, fp, fn)
        result_data.append({
            'Model': model,
            'Prompts Technique': prompts_technique,
            group_by_field1: key[2],  # Use the first group name
            group_by_field2: key[3],  # Use the second group name
            'TP': tp,
            'TN': tn,
            'FP': fp,
            'FN': fn,
            'sum_tpfp': sum_tpfp,
            'sum_tpfn': sum_tpfn,
            'sum_tptn': sum_tptn,
            'Precision': f"{precision:.4f}",
            'Recall': f"{recall:.4f}",
            'F1 Score': f"{f1_score:.4f}",
            'Total': total,
            'Unknown': unknown
        })


def update_consistent_column(input_excel, result_data, model, project, prompts_technique):
    df = pd.read_excel(input_excel)

    # Skip rows based on File Name prefixes
    if project == "C_project": #c
        for sample in sample_warning_c:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = True
        fp_label = False
    else: # java
        for sample in sample_warning_java:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = "TP"
        fp_label = "FP"

    # Process rows without grouping (whole dataset)
    process_rows(df, group_by_field="None", model=model, prompts_technique=prompts_technique, result_data=result_data, tp_label=tp_label, fp_label=fp_label)

def update_consistent_column_tool(input_excel, result_data, model, project, prompts_technique):
    df = pd.read_excel(input_excel)

    # Skip rows based on File Name prefixes
    if project == "C_project": #c
        for sample in sample_warning_c:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = True
        fp_label = False
    else: # java
        for sample in sample_warning_java:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = "TP"
        fp_label = "FP"

    # Process rows with grouping by tool
    process_rows(df, group_by_field="Tool", model=model, prompts_technique=prompts_technique, result_data=result_data, tp_label=tp_label, fp_label=fp_label)
    # print(result_data)

def update_consistent_column_category(input_excel, result_data, model, project, prompts_technique):
    df = pd.read_excel(input_excel)

    # Skip rows based on File Name prefixes
    if project == "C_project": #c
        for sample in sample_warning_c:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = True
        fp_label = False
    else: # java
        for sample in sample_warning_java:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = "TP"
        fp_label = "FP"

    # Process rows with grouping by category
    process_rows(df, group_by_field="category", model=model, prompts_technique=prompts_technique, result_data=result_data, tp_label=tp_label, fp_label=fp_label)

def update_consistent_column_double(input_excel, result_data, model, project, prompts_technique):
    df = pd.read_excel(input_excel)

    # Skip rows based on File Name prefixes
    if project == "C_project": #c
        for sample in sample_warning_c:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = True
        fp_label = False
    else: # java
        for sample in sample_warning_java:
            df = df[~df['File Name'].str.startswith(sample)]
        tp_label = "TP"
        fp_label = "FP"

    # Process rows with grouping by category
    process_rows_double(df, group_by_field1="Tool", group_by_field2="category", model=model, prompts_technique=prompts_technique, result_data=result_data, tp_label=tp_label, fp_label=fp_label)


def get_result(by_tool=False, by_category=False, pl="c", models=None, projects=None, tool=None, prompts_techniques=None):
    result_data = []
    models = models or list(RESULT_MODELS)
    prompts_techniques = prompts_techniques or list(PROMPT_TECHNIQUES)

    if pl == "java":
        tool = tool or "spotbugs"
        projects = projects or list(JAVA_PROJECTS)
    elif pl == "c":
        tool = tool or "C_project"
        projects = projects or ["C_project"]
    else:
        raise ValueError(f"unknown language: {pl}")

    for model in models:
        for project in projects:
            for prompts_technique in prompts_techniques:
                print(model, project, prompts_technique)
                _, output_excel = excel_paths(pl, model, project, prompts_technique, tool)
                if not os.path.exists(output_excel):
                    print(f"skip missing excel: {output_excel}")
                    continue
                if by_category and by_tool:
                    update_consistent_column_double(output_excel, result_data, model, project, prompts_technique)
                elif by_tool:
                    update_consistent_column_tool(output_excel, result_data, model, project, prompts_technique)
                elif by_category:
                    update_consistent_column_category(output_excel, result_data, model, project, prompts_technique)
                else:
                    update_consistent_column(output_excel, result_data, model, project, prompts_technique)

    columns = ["Model", "Prompts Technique", "TP", "TN", "FP", "FN", "sum_tpfp", "sum_tpfn", "sum_tptn", "Precision", "Recall", "F1 Score", "Total", "Unknown"]
    if by_tool:
        columns.insert(0, "Tool")  # 插入 "Tool" 列
    if by_category:
        columns.insert(0, "category")
    # 处理结果数据
    result_df = pd.DataFrame(result_data, columns=columns)

    if by_tool and by_category:
        result_file = f"{pl}_result.xlsx"
    elif by_tool:
        result_file = f"{pl}_result_tool.xlsx"
    elif by_category:
        result_file = f"{pl}_result_category.xlsx"
    else:
        result_file = f"{pl}_result_other.xlsx"

    result_df.to_excel(result_file, index=False, header=columns)

    print(f"所有统计结果已保存到 {result_file}")

if __name__ == '__main__':
    # Default matches the previous hardcoded entry: C results grouped by tool + category.
    get_result(True, True)