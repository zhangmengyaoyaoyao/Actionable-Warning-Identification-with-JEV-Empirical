from src.postprocess import export_responses_to_excel

# 默认与原先脚本一致：处理 Java 实验回答。
pl = "java"


if __name__ == "__main__":
    export_responses_to_excel(pl=pl)
