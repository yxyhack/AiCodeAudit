import os
import json
import fcntl
import time
import hashlib
from typing import Dict, Any, Optional, List
from config import C

# 全局变量存储输出目录
_OUTPUT_DIR = "./output"

def set_output_dir(output_dir):
    """设置全局输出目录"""
    global _OUTPUT_DIR
    _OUTPUT_DIR = output_dir

# 确保存储目录存在
def ensure_storage_dir(base_dir=None):
    """确保存储目录存在"""
    # 使用指定的base_dir或全局输出目录
    if base_dir is None:
        base_dir = os.path.join(_OUTPUT_DIR, "storage")
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    # 创建子目录
    for subdir in ["agent1", "agent2", "graph"]:
        path = os.path.join(base_dir, subdir)
        if not os.path.exists(path):
            os.makedirs(path)
    
    return base_dir

# 生成文件名的辅助函数
def generate_filename(content: str, prefix: str) -> str:
    """根据内容生成唯一文件名"""
    content_hash = hashlib.md5(content.encode()).hexdigest()
    return f"{prefix}_{content_hash}.json"

# 线程安全的文件写入
def safe_write_json(file_path: str, data: Dict[str, Any]) -> None:
    """以线程安全方式写入JSON文件"""
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    # 重试机制，避免文件锁冲突
    max_retries = 3
    retry_delay = 0.5
    
    for i in range(max_retries):
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                # 获取排他性文件锁
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                try:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                finally:
                    # 释放文件锁
                    fcntl.flock(f, fcntl.LOCK_UN)
            return
        except (IOError, BlockingIOError):
            # 如果锁定失败，等待然后重试
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

# 线程安全的文件读取
def safe_read_json(file_path: str) -> Optional[Dict[str, Any]]:
    """以线程安全方式读取JSON文件"""
    if not os.path.exists(file_path):
        return None
        
    max_retries = 3
    retry_delay = 0.5
    
    for i in range(max_retries):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # 获取共享文件锁
                fcntl.flock(f, fcntl.LOCK_SH | fcntl.LOCK_NB)
                try:
                    return json.load(f)
                finally:
                    # 释放文件锁
                    fcntl.flock(f, fcntl.LOCK_UN)
        except (IOError, BlockingIOError):
            # 如果锁定失败，等待然后重试
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise

# 保存Agent1分析结果
def save_agent1_result(source_file_path: str, source_code: str, ai_response: str) -> str:
    """保存Agent1的AI分析结果"""
    storage_dir = ensure_storage_dir()
    filename = generate_filename(source_code, "agent1")
    file_path = os.path.join(storage_dir, "agent1", filename)
    
    data = {
        "source_file_path": source_file_path,
        "source_code": source_code,
        "ai_response": ai_response,
        "timestamp": time.time()
    }
    
    safe_write_json(file_path, data)
    return file_path

# 保存Agent2分析结果
def save_agent2_result(input_text: str, ai_response: str) -> str:
    """保存Agent2的AI分析结果"""
    storage_dir = ensure_storage_dir()
    filename = generate_filename(input_text, "agent2")
    file_path = os.path.join(storage_dir, "agent2", filename)
    
    data = {
        "input_text": input_text,
        "ai_response": ai_response,
        "timestamp": time.time()
    }
    
    safe_write_json(file_path, data)
    return file_path

# 保存依赖图结果
def save_graph_result(graph_id: str, graph_data: Dict) -> str:
    """保存依赖图结果"""
    storage_dir = ensure_storage_dir()
    file_path = os.path.join(storage_dir, "graph", f"{graph_id}.json")
    
    safe_write_json(file_path, graph_data)
    return file_path

# 获取所有持久化的Agent1结果
def get_all_agent1_results() -> Dict[str, Dict]:
    """获取所有已保存的Agent1分析结果"""
    storage_dir = ensure_storage_dir()
    agent1_dir = os.path.join(storage_dir, "agent1")
    
    results = {}
    if os.path.exists(agent1_dir):
        for filename in os.listdir(agent1_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(agent1_dir, filename)
                result = safe_read_json(file_path)
                if result:
                    results[filename] = result
    
    return results

# 根据源代码获取已存在的Agent1结果
def get_agent1_result_by_source(source_code: str) -> Optional[Dict]:
    """根据源代码获取之前保存的Agent1分析结果"""
    filename = generate_filename(source_code, "agent1")
    storage_dir = ensure_storage_dir()
    file_path = os.path.join(storage_dir, "agent1", filename)
    
    return safe_read_json(file_path)

# 程序执行状态常量
EXECUTION_STATUS = {
    "NOT_STARTED": "not_started",
    "AGENT1_COMPLETE": "agent1_complete",
    "GRAPH_BUILT": "graph_built",
    "AGENT2_COMPLETE": "agent2_complete",
    "COMPLETED": "completed"
}

# 保存程序执行状态
def save_execution_status(project_md5: str, status: str, graph_file: str = None, result_file: str = None) -> None:
    """保存程序执行状态"""
    storage_dir = ensure_storage_dir()
    status_file = os.path.join(storage_dir, f"execution_status_{project_md5}.json")
    
    data = {
        "status": status,
        "timestamp": time.time(),
        "project_md5": project_md5
    }
    
    if graph_file:
        data["graph_file"] = graph_file
    
    if result_file:
        data["result_file"] = result_file
    
    safe_write_json(status_file, data)

# 获取程序执行状态
def get_execution_status(project_md5: str) -> Dict:
    """获取程序执行状态"""
    storage_dir = ensure_storage_dir()
    status_file = os.path.join(storage_dir, f"execution_status_{project_md5}.json")
    
    status = safe_read_json(status_file)
    if not status:
        return {"status": EXECUTION_STATUS["NOT_STARTED"]}
    
    return status

# 保存代码单元列表，用于断点续传
def save_code_units(project_md5: str, code_units: List) -> None:
    """保存代码单元列表"""
    storage_dir = ensure_storage_dir()
    units_file = os.path.join(storage_dir, f"code_units_{project_md5}.json")
    
    # 将CodeUnit对象序列化为可JSON化的字典
    serialized_units = []
    for unit in code_units:
        if unit is None:
            continue
        try:
            serialized_unit = {
                "name": unit.name,
                "path": unit.path,
                "source_name": unit.source_name,
                "target_name": unit.target_name,
                "source_desc": unit.source_desc,
                "source_code": unit.source_code,
                "start_code_line": unit.start_code_line,
                "end_code_line": unit.end_code_line
            }
            serialized_units.append(serialized_unit)
        except AttributeError:
            continue
    
    data = {
        "project_md5": project_md5,
        "timestamp": time.time(),
        "code_units": serialized_units
    }
    
    safe_write_json(units_file, data)

# 获取保存的代码单元列表
def get_code_units(project_md5: str) -> List:
    """获取保存的代码单元列表"""
    from models import CodeUnit
    
    storage_dir = ensure_storage_dir()
    units_file = os.path.join(storage_dir, f"code_units_{project_md5}.json")
    
    data = safe_read_json(units_file)
    if not data or "code_units" not in data:
        return []
    
    # 将序列化的字典转换回CodeUnit对象
    code_units = []
    for unit_dict in data["code_units"]:
        try:
            unit = CodeUnit(
                name=unit_dict["name"],
                path=unit_dict["path"],
                source_name=unit_dict["source_name"],
                target_name=unit_dict["target_name"],
                source_desc=unit_dict["source_desc"],
                source_code=unit_dict["source_code"],
                start_code_line=unit_dict["start_code_line"],
                end_code_line=unit_dict["end_code_line"]
            )
            code_units.append(unit)
        except KeyError:
            continue
    
    return code_units 