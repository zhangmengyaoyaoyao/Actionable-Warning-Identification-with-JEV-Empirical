import os
import pandas as pd

def count_java_tp_labels(directory_path):
    """
    遍历指定目录中的所有CSV文件，统计每个文件中'final_label'列值为'TP'的行数
    
    参数:
    directory_path (str): 包含CSV文件的目录路径
    
    返回:
    None: 直接打印结果
    """
    # 检查目录是否存在
    if not os.path.exists(directory_path):
        print(f"错误: 目录 '{directory_path}' 不存在")
        return
    
    # 获取目录中所有文件
    files = os.listdir(directory_path)
    
    # 筛选出CSV文件
    csv_files = [file for file in files if file.lower().endswith('.csv')]
    
    if not csv_files:
        print(f"在目录 '{directory_path}' 中没有找到CSV文件")
        return
    
    print(f"在目录 '{directory_path}' 中找到 {len(csv_files)} 个CSV文件")
    print("-" * 50)
    
    # 遍历每个CSV文件并统计
    for csv_file in csv_files:
        file_path = os.path.join(directory_path, csv_file)
        try:
            # 读取CSV文件
            df = pd.read_csv(file_path)
            
            # 检查是否存在'final_label'列
            if 'final_label' not in df.columns:
                print(f"文件 '{csv_file}' 中没有'final_label'列")
                continue
            
            # 统计'final_label'为'TP'的行数
            tp_count = df[df['final_label'] == 'TP'].shape[0]
            
            # 打印结果
            print(f"文件名: {csv_file}, TP计数: {tp_count}")
            
        except Exception as e:
            print(f"处理文件 '{csv_file}' 时出错: {str(e)}")
    
    print("-" * 50)




def analyze_c_project_tool_stats(file_path):
    """
    分析xlsx文件中不同Project使用不同Tool的总数和final_lable分别为TRUE和FALSE的数量
    
    参数:
    file_path (str): xlsx文件路径
    
    返回:
    None: 直接打印结果
    """
    try:
        # 读取xlsx文件
        df = pd.read_excel(file_path)
        
        # 检查必要的列是否存在
        required_columns = ['Project', 'Tool', 'final_lable']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"错误: 文件缺少以下列: {', '.join(missing_columns)}")
            return
        
        print("=" * 80)
        print("数据分析结果:")
        print("=" * 80)
        
        # 统计每个Project-Tool组合的总数
        print("\n1. 每个Project使用不同Tool的总数:")
        project_tool_counts = df.groupby(['Project', 'Tool']).size().reset_index(name='总数')
        
        # 按Project分组并打印
        for project, group_data in project_tool_counts.groupby('Project'):
            print(f"\n项目: {project}")
            print("-" * 50)
            for _, row in group_data.iterrows():
                print(f"工具: {row['Tool']}, 总数: {row['总数']}")
        
        # 统计每个Project-Tool组合中final_lable为TRUE和FALSE的数量
        print("\n" + "=" * 80)
        print("\n2. 每个Project使用不同Tool的final_lable统计:")
        
        # 确保final_lable列的值是字符串类型，并转换为大写以统一比较
        df['final_lable'] = df['final_lable'].astype(str).str.upper()
        
        for project, project_data in df.groupby('Project'):
            print(f"\n项目: {project}")
            print("-" * 50)
            
            for tool, tool_data in project_data.groupby('Tool'):
                # 计算TRUE和FALSE的数量
                true_count = sum(tool_data['final_lable'] == 'TRUE')
                false_count = sum(tool_data['final_lable'] == 'FALSE')
                
                # 计算其他值的数量（既不是TRUE也不是FALSE）
                other_count = len(tool_data) - true_count - false_count
                
                print(f"工具: {tool}")
                print(f"  - TRUE数量: {true_count}")
                print(f"  - FALSE数量: {false_count}")
                
                if other_count > 0:
                    print(f"  - 其他值数量: {other_count}")
                
                print(f"  - 总数: {len(tool_data)}")
                print()
        
        # 总体统计
        print("=" * 80)
        print("\n3. 总体统计:")
        print(f"总记录数: {len(df)}")
        print(f"项目数量: {df['Project'].nunique()}")
        print(f"工具数量: {df['Tool'].nunique()}")
        
        true_total = sum(df['final_lable'] == 'TRUE')
        false_total = sum(df['final_lable'] == 'FALSE')
        other_total = len(df) - true_total - false_total
        
        print(f"TRUE总数: {true_total}")
        print(f"FALSE总数: {false_total}")
        
        if other_total > 0:
            print(f"其他值总数: {other_total}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"处理文件时出错: {str(e)}")

# 使用示例
if __name__ == "__main__":
    # directory_path = "report/spotbugs_linked"
    # count_java_tp_labels(directory_path)

    file_path = "report/c_raw/c.xlsx"
    analyze_c_project_tool_stats(file_path)