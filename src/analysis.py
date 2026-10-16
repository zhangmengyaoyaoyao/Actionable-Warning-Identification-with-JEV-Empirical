import pandas as pd
import numpy as np


def process_category_c(input_file, output_file, group_cols):
    # 读取Excel文件
    df = pd.read_excel(input_file)

    # 所有可能的分组列
    all_group_cols = ['category', 'Tool', 'Model', 'Prompts Technique']

    # 定义需要求和的列
    sum_cols = ['TP', 'TN', 'FP', 'FN', 'sum_tpfp', 'sum_tpfn', 'sum_tptn', 'Total', 'Unknown']

    # 分组并求和
    grouped = df.groupby(group_cols, as_index=False)[sum_cols].sum()

    # 对于不在分组列中的列，填充为空字符串（或可选填None）
    for col in all_group_cols:
        if col not in group_cols:
            grouped[col] = ''

    # 计算 Precision
    tp_plus_fp = grouped['TP'] + grouped['FP']
    grouped['Precision'] = np.where(tp_plus_fp == 0, np.nan, grouped['TP'] / tp_plus_fp)

    # 计算 Recall
    tp_plus_fn = grouped['TP'] + grouped['FN']
    grouped['Recall'] = np.where(tp_plus_fn == 0, np.nan, grouped['TP'] / tp_plus_fn)

    # 计算 F1 Score
    precision_plus_recall = grouped['Precision'] + grouped['Recall']
    grouped['F1 Score'] = np.where(
        precision_plus_recall == 0,
        np.nan,
        2 * (grouped['Precision'] * grouped['Recall']) / precision_plus_recall
    )

    # 保证最终列顺序一致
    final_columns = [
        'category', 'Tool', 'Model', 'Prompts Technique',
        'TP', 'TN', 'FP', 'FN',
        'sum_tpfp', 'sum_tpfn', 'sum_tptn',
        'Precision', 'Recall', 'F1 Score',
        'Total', 'Unknown'
    ]
    grouped = grouped[final_columns]

    # 保存结果
    grouped.to_excel(output_file, index=False)
    print("处理完成，结果已保存到", output_file)


def process_category_java(input_file, output_file, group_cols):
    # 读取Excel文件
    df = pd.read_excel(input_file)

    # 所有可能的分组列
    all_group_cols = ['category', 'Model', 'Prompts Technique']

    # 定义需要求和的列
    sum_cols = ['TP', 'TN', 'FP', 'FN', 'sum_tpfp', 'sum_tpfn', 'sum_tptn', 'Total', 'Unknown']

    # 分组并求和
    grouped = df.groupby(group_cols, as_index=False)[sum_cols].sum()

    # 对于不在分组列中的列，填充为空字符串（或可选填None）
    for col in all_group_cols:
        if col not in group_cols:
            grouped[col] = ''

    # 计算 Precision
    tp_plus_fp = grouped['TP'] + grouped['FP']
    grouped['Precision'] = np.where(tp_plus_fp == 0, np.nan, grouped['TP'] / tp_plus_fp)

    # 计算 Recall
    tp_plus_fn = grouped['TP'] + grouped['FN']
    grouped['Recall'] = np.where(tp_plus_fn == 0, np.nan, grouped['TP'] / tp_plus_fn)

    # 计算 F1 Score
    precision_plus_recall = grouped['Precision'] + grouped['Recall']
    grouped['F1 Score'] = np.where(
        precision_plus_recall == 0,
        np.nan,
        2 * (grouped['Precision'] * grouped['Recall']) / precision_plus_recall
    )

    # 保证最终列顺序一致
    final_columns = [
        'category', 'Model', 'Prompts Technique',
        'TP', 'TN', 'FP', 'FN',
        'sum_tpfp', 'sum_tpfn', 'sum_tptn',
        'Precision', 'Recall', 'F1 Score',
        'Total', 'Unknown'
    ]
    grouped = grouped[final_columns]

    # 保存结果
    grouped.to_excel(output_file, index=False)
    print("处理完成，结果已保存到", output_file)


def recalculate_metrics(file_path):
    # 读取Excel文件
    df = pd.read_excel(file_path)
    
    # 安全计算Precision
    tp_plus_fp = df['TP'] + df['FP']
    df['Precision'] = np.where(
        tp_plus_fp == 0,
        np.nan,
        df['TP'] / tp_plus_fp
    )
    
    # 安全计算Recall
    tp_plus_fn = df['TP'] + df['FN']
    df['Recall'] = np.where(
        tp_plus_fn == 0,
        np.nan,
        df['TP'] / tp_plus_fn
    )
    
    # 安全计算F1 Score
    precision_plus_recall = df['Precision'] + df['Recall']
    df['F1 Score'] = np.where(
        precision_plus_recall == 0,
        np.nan,
        2 * (df['Precision'] * df['Recall']) / precision_plus_recall
    )
    
    # 保存回原文件
    df.to_excel(file_path, index=False)


if __name__ == '__main__':
    # Default matches the previous hardcoded entry.
    process_category_c('c_result.xlsx', group_cols=['Prompts Technique'], output_file='c_result_analysis.xlsx')
