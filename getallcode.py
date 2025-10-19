import os

# --- 配置 ---

# 1. 指定要包含的文件后缀名
TARGET_EXTENSIONS = ['.py', '.html', '.css', '.yaml']

# 2. 指定输出的聚合文件名
OUTPUT_FILENAME = 'combined_files.txt'

# 3. 指定要排除的目录名
EXCLUDED_DIRS = ['.git', '__pycache__', 'node_modules', '.vscode', '.venv']


# --- 脚本 ---

def combine_files():
    """
    遍历当前脚本所在目录及子目录,将指定后缀的文件内容合并到一个txt文件中。
    """

    # 获取此脚本所在的目录
    # __file__ 是 Python 的一个内置变量，表示当前执行的脚本文件的路径
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError:
        # 如果在 REPL 或 notebook 中运行，__file__ 可能未定义
        script_dir = os.getcwd()
        print(f"警告: 无法获取脚本路径, 使用当前工作目录: {script_dir}")

    print(f"开始在 {script_dir} 中搜索文件...")
    print(f"将排除以下目录: {', '.join(EXCLUDED_DIRS)}")

    found_files_count = 0

    # 'w' 模式会覆盖已存在的文件。确保每次运行都是一个全新的聚合文件。
    # 使用 utf-8 编码处理各种文件内容
    try:
        with open(os.path.join(script_dir, OUTPUT_FILENAME), 'w', encoding='utf-8') as outfile:

            # os.walk 会递归遍历目录
            # root: 当前目录路径
            # dirs: 当前目录下的子目录列表
            # files: 当前目录下的文件列表
            for root, dirs, files in os.walk(script_dir):

                # *** 修改点在这里 ***
                # 通过修改 dirs 列表 (dirs[:]) 来阻止 os.walk 进一步遍历这些目录
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

                for filename in files:
                    # 检查文件后缀是否在我们的目标列表中
                    if any(filename.endswith(ext) for ext in TARGET_EXTENSIONS):

                        file_path = os.path.join(root, filename)

                        # 获取相对路径，以便在输出文件中更清晰地显示
                        relative_path = os.path.relpath(file_path, script_dir)

                        # 排除输出文件本身，防止它把自己也包含进去
                        if relative_path == OUTPUT_FILENAME:
                            continue

                        print(f"  正在添加: {relative_path}")
                        found_files_count += 1

                        # 写入文件分隔符和路径
                        outfile.write(f"\n\n{'=' * 20} Start of: {relative_path} {'=' * 20}\n\n")

                        try:
                            # 以只读 ('r') 模式打开源文件
                            # 使用 errors='ignore' 来跳过无法解码的字符
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                                content = infile.read()
                                outfile.write(content)

                        except Exception as e:
                            # 如果读取失败（例如权限问题），则记录错误
                            outfile.write(f"--- 无法读取文件: {e} ---\n")
                            print(f"  [错误] 无法读取 {relative_path}: {e}")

                        # 写入文件结束符
                        outfile.write(f"\n\n{'=' * 20} End of: {relative_path} {'=' * 20}\n\n")

        print(f"\n完成！成功聚合 {found_files_count} 个文件。")
        print(f"输出文件已保存为: {os.path.join(script_dir, OUTPUT_FILENAME)}")

    except IOError as e:
        print(f"创建输出文件时发生错误: {e}")
    except Exception as e:
        print(f"发生未知错误: {e}")


# --- 执行 ---
if __name__ == "__main__":
    combine_files()