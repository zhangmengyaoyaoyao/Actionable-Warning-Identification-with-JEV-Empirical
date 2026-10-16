import os
import re
import pandas as pd

def extract_status_from_lines(lines):

    if lines:  # 确保文件不为空
        # 先尝试匹配最后一行
        last_line = lines[-1].strip()
        match = re.search(r"@@ (.*?) @@", last_line)
        if match:
            result = match.group(1)
            if len(result) < 25:
                # 去除结果末尾的点号（如果存在）
                if result.endswith("."):
                    result = result[:-1]
                return result
            else :
                match = re.search(r"warning is (.*?).", result)
                if match:
                    return match.group(1)
                match = re.search(r"warning is (.*?),", result)
                if match:
                    return match.group(1)
                match = re.search(r"warning is (.*?) ", result)
                if match:
                    return match.group(1)

        # 如果最后一行无匹配，检查倒数第二行是否以@@结尾且第二行以任意字符+" @@"开头
        if len(lines) >= 2:  # 确保至少有两行
            second_last_line = lines[-2].strip()
            second_line = lines[1].strip() if len(lines) > 1 else ""
            
            if second_last_line.endswith("@@") and re.match(r".* @@", second_line):
                # 尝试从这两行中构建完整的匹配
                combined_pattern = second_last_line + " " + second_line
                match = re.search(r"@@ (.*?) @@", combined_pattern)
                if match:
                    result = match.group(1)
                    # 去除结果末尾的点号（如果存在）
                    if result.endswith("."):
                        result = result[:-1]
                    return result
                
        # 如果最后一行无匹配，再尝试匹配第一行
        first_line = lines[0].strip()
        match = re.search(r"@@ (.*?) @@", first_line)
        if match:
            result = match.group(1)
            # 去除结果末尾的点号（如果存在）
            if result.endswith("."):
                result = result[:-1]
            return result

        # 如果第一行和最后一行都无匹配，则遍历全文查找
        for line in lines:
            match = re.search(r"@@ (.*?) @@", line.strip())
            if match:
                result = match.group(1)
                # 去除结果末尾的点号（如果存在）
                if result.endswith("."):
                    result = result[:-1]
                return result
            else:
                match = re.search(r"warning is (.*?) ", line.strip())
                if match:
                    return match.group(1)
                match = re.search(r"warning is (.*?).", line.strip())
                if match:
                    return match.group(1)

    return 'error'  # 若全文无匹配，则返回 None

def process_txt_files(folder_path, output_excel):
    data = []  # 用于存储文件名、完整内容和提取的信息

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt"):  # 只处理 .txt 文件
            file_path = os.path.join(folder_path, filename)
            
            # 打开文件并读取内容
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
                full_content = "".join(lines).strip()  # 获取完整内容
                
                status = extract_status_from_lines(lines)
                
                # 提取文件名去除扩展名
                file_name_without_ext = os.path.splitext(filename)[0]
                # 将文件名、完整内容和状态加入数据
                data.append({
                    "File Name": file_name_without_ext,
                    "Content": full_content,
                    "Status": status
                })
    
    # 将数据保存到Excel文件
    df = pd.DataFrame(data)
    df.to_excel(output_excel, index=False)
    print(f"数据已保存到 {output_excel}")


def process_txt_files_with_3history(folder_path, output_excel):
    data = []  # 用于存储文件名、完整内容和提取的信息

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt") and ("_history" not in filename):  # 只处理 .txt 文件
            file_path = os.path.join(folder_path, filename)
            
            # 打开文件并读取内容
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
                full_content = "".join(lines).strip()  # 获取完整内容
                status = extract_status_from_lines(lines)

                # 提取文件名去除扩展名
                file_name_without_ext = os.path.splitext(filename)[0]
                try:
                    history_file_path=os.path.join(folder_path, file_name_without_ext+"_history.txt")
                    with open(history_file_path, "r", encoding="utf-8") as history_file:
                        history_lines = history_file.readlines()
                        history_full_content = "".join(history_lines)
                        # 分割文件内容，按三个换行符分成三部分
                        history_parts = history_full_content.split("\n\n\n")
                        response1 = history_parts[0].strip() if len(history_parts) > 0 else ""
                        response2 = history_parts[1].strip() if len(history_parts) > 1 else ""
                        response3 = history_parts[2].strip() if len(history_parts) > 2 else ""

                        if status == 'error' or status == 'No changes needed':
                            status = extract_status_from_lines(response2.split("\n"))  # 从第二个回答中提取状态
                        if status == 'error' or status == 'No changes needed':
                            status = extract_status_from_lines(response1.split("\n"))

                        # 将这三部分数据保存到没有 '_history' 的文件对应的 Excel 行
                        data.append({
                            "File Name": file_name_without_ext,
                            "Response 1": response1,
                            "Response 2": response2,
                            "Response 3": response3,
                            "Content": full_content,
                            "Status": status
                        })
                except FileNotFoundError:
                    print("FileNotFoundError:" + file_name_without_ext+"_history.txt")
                    response1 = ""
                    response2 = ""
                    response3 = ""
                    data.append({
                        "File Name": file_name_without_ext,
                        "Response 1": response1,
                        "Response 2": response2,
                        "Response 3": response3,
                        "Content": full_content,
                        "Status": status
                    })
    # 将数据保存到Excel文件
    df = pd.DataFrame(data)
    df.to_excel(output_excel, index=False)
    print(f"数据已保存到 {output_excel}")


def process_txt_files_with_2history(folder_path, output_excel):
    data = []  # 用于存储文件名、完整内容和提取的信息

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        if filename.endswith(".txt") and ("_history" not in filename):  # 只处理 .txt 文件
            file_path = os.path.join(folder_path, filename)
            
            # 打开文件并读取内容
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()
                full_content = "".join(lines).strip()  # 获取完整内容

                status = extract_status_from_lines(lines)

                # 提取文件名去除扩展名
                file_name_without_ext = os.path.splitext(filename)[0]
                try:
                    history_file_path=os.path.join(folder_path, file_name_without_ext+"_history.txt")
                    with open(history_file_path, "r", encoding="utf-8") as history_file:
                        history_lines = history_file.readlines()
                        history_full_content = "".join(history_lines)
                        # 分割文件内容，按三个换行符分成2部分
                        history_parts = history_full_content.split("\n\n\n")
                        response1 = history_parts[0].strip() if len(history_parts) > 0 else ""
                        response2 = history_parts[1].strip() if len(history_parts) > 1 else ""
                        # 将这2部分数据保存到没有 '_history' 的文件对应的 Excel 行
                        data.append({
                            "File Name": file_name_without_ext,
                            "Response 1": response1,
                            "Response 2": response2,
                            "Content": full_content,
                            "Status": status
                        })
                except FileNotFoundError:
                    print("FileNotFoundError:" + file_name_without_ext+"_history.txt")
                    response1 = ""
                    response2 = ""
                    data.append({
                        "File Name": file_name_without_ext,
                        "Response 1": response1,
                        "Response 2": response2,
                        "Content": full_content,
                        "Status": status
                    })
    # 将数据保存到Excel文件
    df = pd.DataFrame(data)
    df.to_excel(output_excel, index=False)
    print(f"数据已保存到 {output_excel}")



def link_excel(file1, file2):
    """
    将 file1 中的所有列粘贴到 file2 中的最后，并保存为新的 Excel 文件。
    """
    try:
        # 根据文件扩展名判断读取方式
        if file1.endswith('.csv'):
            df1 = pd.read_csv(file1)
        elif file1.endswith('.xlsx'):
            df1 = pd.read_excel(file1)
        else:
            raise ValueError("file1 必须是 CSV 或 Excel 文件")
    except Exception as e:
        print(f"Problematic file: {file1}")
        raise
    try:
        if file2.endswith('.csv'):
            df2 = pd.read_csv(file2)
        elif file2.endswith('.xlsx'):
            df2 = pd.read_excel(file2)
        else:
            raise ValueError("file2 必须是 CSV 或 Excel 文件")
    except Exception as e:
        print(f"Problematic file: {file2}")
        raise

    # 检查行数是否一致
    if len(df1) != len(df2):
        print(f"Warning: The number of rows in {file1} and {file2} do not match.")
    # 按照 'no' 列升序排序 file1
    df1_sorted = df1.sort_values(by='no', ascending=True).reset_index(drop=True)

    # 按照 'File Name' 列升序排序 file2
    df2_sorted = df2.sort_values(by='File Name', ascending=True).reset_index(drop=True)

    # 将 file1 中的所有列添加到 file2 中的最后
    merged_df = pd.concat([df2_sorted, df1_sorted], axis=1)


    # 一行一行地粘贴 file1 的数据到 file2
    # for index, row in df1_sorted.iterrows():
    #     # 将每一行添加到 file2 的最后
    #     df2_sorted.loc[index, df1_sorted.columns] = row

    # 保存到 file2 中
    merged_df.to_excel(file2, index=False)
