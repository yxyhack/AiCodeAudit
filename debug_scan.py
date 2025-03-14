import os
from audit import scan_project_struct, print_source_dir
from config import C
import sys

def debug_is_excluded_dir(dir_path):
    dir_name = os.path.basename(dir_path)
    for exclude in C.project.exclude_dir:
        if dir_name == exclude:
            print(f"排除目录: {dir_path}, 匹配规则: {exclude}")
            return True
    return False

def debug_is_source_file(ext):
    result = ext in C.project.source_file_ext
    if result:
        print(f"源文件扩展名: {ext}")
    return result

def debug_is_config_file(ext):
    result = ext in C.project.config_file_ext
    if result:
        print(f"配置文件扩展名: {ext}")
    return result

def debug_scan_dir(dir_path, parent_dir, level=0):
    try:
        entries = os.scandir(dir_path)
    except OSError as e:
        print(f"读取目录失败 {dir_path}: {e}")
        return
    
    indent = "  " * level
    print(f"{indent}扫描目录: {dir_path}")
    
    for entry in entries:
        entry_path = os.path.join(dir_path, entry.name)
        
        if debug_is_excluded_dir(entry_path):
            continue
            
        print(f"{indent}发现: {entry.name}")
        
        if entry.is_dir():
            print(f"{indent}是目录: {entry.name}")
            sub_dir = parent_dir.__class__(path=entry_path, name=entry.name)
            debug_scan_dir(entry_path, sub_dir, level + 1)
            parent_dir.source_dirs.append(sub_dir)
            print(f"{indent}添加子目录: {entry.name} 到 {parent_dir.name}")
        else:
            ext = os.path.splitext(entry.name)[1].lower()  # 转换为小写
            print(f"{indent}文件: {entry.name}, 扩展名: {ext}")
            
            if debug_is_source_file(ext) or debug_is_config_file(ext):
                file_info = entry.stat()
                size_mb = file_info.st_size / (1024 * 1024)
                print(f"{indent}文件大小: {size_mb:.2f}MB, 最大允许大小: {C.project.exclude_max_file_size}MB")
                
                if size_mb > C.project.exclude_max_file_size:
                    print(f"{indent}排除过大文件: {entry.name}")
                    continue
                    
                try:
                    with open(entry_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    print(f"{indent}成功读取文件: {entry.name}")
                    from models import SourceFile
                    source_file = SourceFile(
                        path=entry_path,
                        name=entry.name,
                        source_code=content,
                        extension=ext
                    )
                    parent_dir.source_files.append(source_file)
                    print(f"{indent}添加文件: {entry.name} 到 {parent_dir.name}")
                except Exception as e:
                    print(f"{indent}读取文件失败 {entry_path}: {e}")

def debug_scan_project(project_dir):
    print("配置信息:")
    print(f"源文件扩展名: {C.project.source_file_ext}")
    print(f"配置文件扩展名: {C.project.config_file_ext}")
    print(f"排除目录: {C.project.exclude_dir}")
    print(f"最大文件大小: {C.project.exclude_max_file_size}MB")
    
    abs_path = os.path.abspath(project_dir)
    dir_name = os.path.basename(abs_path)
    root_dir = scan_project_struct(project_dir).__class__(path=abs_path, name=dir_name)
    
    debug_scan_dir(abs_path, root_dir)
    
    count_files = sum(len(d.source_files) for d in [root_dir] + root_dir.source_dirs)
    count_dirs = len(root_dir.source_dirs)
    
    print("\n结果统计:")
    print(f"源文件数量: {count_files}")
    print(f"子目录数量: {count_dirs}")
    
    print("\n目录结构:")
    print(print_source_dir(root_dir))
    
    return root_dir

if __name__ == "__main__":
    project_dir = sys.argv[1] if len(sys.argv) > 1 else "../Desktop/solana.plugin-test/"
    debug_scan_project(project_dir) 