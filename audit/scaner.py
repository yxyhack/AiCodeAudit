import os

from config import C
from models import SourceDir, SourceFile, Config
from utils import gen_line_code


def scan_project_struct(project_dir):
    abs_path = os.path.abspath(project_dir)
    dir_name = os.path.basename(abs_path)
    root_dir = SourceDir(path=abs_path, name=dir_name)
    scan_dir(abs_path, root_dir)
    return root_dir


def scan_dir(dir_path, parent_dir):
    try:
        entries = os.scandir(dir_path)
    except OSError as e:
        print(f"Failed to read directory {dir_path}: {e}")
        return
    for entry in entries:
        entry_path = os.path.join(dir_path, entry.name)

        if is_excluded_dir(entry_path):
            continue
        if entry.is_dir():
            sub_dir = SourceDir(path=entry_path, name=entry.name)
            scan_dir(entry_path, sub_dir)
            parent_dir.source_dirs.append(sub_dir)
        else:
            ext = os.path.splitext(entry.name)[1]
            if is_source_file(ext) or is_config_file(ext):
                file_info = entry.stat()
                if file_info.st_size / (1024 * 1024) > C.project.exclude_max_file_size:
                    continue
                content = read_source_file(entry_path)
                if content is not None:
                    parent_dir.source_files.append(SourceFile(
                        path=entry_path,
                        name=entry.name,
                        source_code=gen_line_code(content),
                        extension=ext
                    ))


def is_source_file(ext):
    return ext in C.project.source_file_ext


def is_config_file(ext):
    return ext in C.project.config_file_ext


def is_excluded_dir(dir_path):
    return any(exclude in dir_path for exclude in C.project.exclude_dir)


def read_source_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read file {file_path}: {e}")
        return None

def build_tree_string(dir_obj, last=False, tree=[]):
    indent = ""
    for i, is_last in enumerate(tree):
        if i < len(tree) - 1:
            indent += "   " if is_last else "│  "
        else:
            indent += "└─ " if last else "├─ "

    result = f"{indent}{dir_obj.name}\n"

    for i, file in enumerate(dir_obj.source_files):
        is_last_file = i == len(dir_obj.source_files) - 1 and len(dir_obj.source_dirs) == 0
        file_indent = indent + ("└─ " if is_last_file else "├─ ")
        result += f"{file_indent}{file.name} ({file.extension})\n"

    for i, sub_dir in enumerate(dir_obj.source_dirs):
        new_tree = tree + [i == len(dir_obj.source_dirs) - 1]
        result += build_tree_string(sub_dir, i == len(dir_obj.source_dirs) - 1, new_tree)

    return result

def print_source_dir(dir_obj):
    return build_tree_string(dir_obj, True, [])


def traverse_source_dir_bfs(root):
    text = []
    queue = [root]

    while queue:
        current = queue.pop(0)
        for file in current.source_files:
            file_info = f"</代码单元>\n//{file.path}\n{file.source_code}</代码单元>"
            text.append(file_info)
        for sub_dir in current.source_dirs:
            queue.append(sub_dir)
    return text


def get_all_source_files_bfs(root_dir):
    """
    使用广度优先搜索获取SourceDir对象中的所有SourceFile。

    :param root_dir: SourceDir对象
    :return: 包含所有SourceFile的列表
    """
    queue = [root_dir]
    all_files = []
    while queue:
        current_dir = queue.pop(0)
        all_files.extend(current_dir.source_files)  # 添加当前目录下的所有文件
        queue.extend(current_dir.source_dirs)  # 将当前目录下的所有子目录加入队列
    return all_files