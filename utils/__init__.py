import hashlib
import re
import sys
from typing import List
from loguru import logger
import networkx as nx
import tiktoken
from matplotlib import pyplot as plt

from config import C
from models import CodeUnit


def is_cmd_mode():
    """
    尝试判断脚本是否从命令行运行。
    这种方法并不是100%可靠，但对于大多数情况应该足够。
    """
    # 检查是否有命令行参数（除了脚本名称本身）
    if len(sys.argv) > 1:
        return True
    # 检查是否从交互式解释器运行
    if hasattr(sys, 'ps1'):
        return False
    # 检查是否从IDLE或其他IDE运行
    if 'idlelib.run' in sys.modules:
        return False
    # 默认认为是从命令行运行
    return True

def count_text_tokens(text: str) -> int:
    encoding = tiktoken.encoding_for_model(C.openai.model)
    tokens = encoding.encode(text)
    return len(tokens)


def count_message_tokens(messages: list) -> int:
    encoding = tiktoken.encoding_for_model(C.openai.model)
    total_tokens = 0
    for message in messages:
        text = f"{message['role']}: {message['content']}"
        tokens = encoding.encode(text)
        total_tokens += len(tokens)
    return total_tokens


def gen_line_code(text):
    """
    为输入的多行文本自动编制行号。

    :param text: 输入的多行文本字符串
    :return: 添加了行号的多行文本字符串
    """
    lines = text.splitlines()  # 将输入文本按行分割成列表
    max_line_number_length = len(str(len(lines)))  # 计算最大行号长度，用于对齐

    result = []
    for i, line in enumerate(lines, start=1):
        # 使用右对齐确保行号宽度一致
        formatted_line_number = str(i).rjust(max_line_number_length)
        result.append(f"{formatted_line_number}: {line}")

    return "\n".join(result)


def get_code_by_line(text: str, start_line: int, end_line: int) -> str:
    """
    根据指定的起始行和结束行从多行文本中提取内容。

    :param text: 输入的多行文本字符串
    :param start_line: 起始行号（从1开始）
    :param end_line: 结束行号（包含）
    :return: 提取的多行文本字符串
    """
    lines = text.splitlines()  # 将输入文本按行分割成列表

    # 检查起始行和结束行的有效性
    if start_line < 1 or end_line > len(lines) or start_line > end_line:
        logger.error("无效的起始行或结束行",start_line,end_line)
        end_line=start_line+1

    # 提取指定范围的行
    extracted_lines = lines[start_line - 1:end_line]

    # 将提取的行重新组合成一个字符串
    return "\n".join(extracted_lines)


def parse_code_uint(code,path,name,input_text):
    """
    从输入文本中提取并解析 <输出单元> 标签内的内容。

    :param input_text: 包含 <输出单元> 标签的输入文本
    :return: 解析后的内容列表，每个元素是一个字典
    """
    if input_text.replace("\n","").strip().find("未发现数据")!=-1:
        return None
    # 使用正则表达式提取 <输出单元> 标签内的内容
    match = re.search(r'<输出单元>\n(.*?)\n<输出单元>', input_text, re.DOTALL)
    if not match:
        raise ValueError("未找到 <输出单元> 标签或标签格式不正确",input_text)
    content = match.group(1)
    if content=="" or content==None:
        return None
    # 按行分割内容
    lines = content.strip().split('\n')
    parsed_data = []
    for line in lines:
        parts = line.split('<SEP>')
        if len(parts) != 4:
            raise ValueError(f"行 '{line}' 的格式不正确，应包含四个部分",parts)

        line_list=parts[3].strip().split("-")
        if len(line_list) != 2:
            raise Exception("解析行号错误",line_list,line)
        parsed_data.append(CodeUnit(
            source_name=parts[0].strip(),
            target_name=parts[1].strip(),
            source_desc=parts[2].strip(),
            start_code_line=int(line_list[0]),
            end_code_line=int(line_list[1]),
            source_code=get_code_by_line(code,start_line=int(line_list[0]),end_line=int(line_list[1])),
            path=path,
            name=name
        ))

    return parsed_data


def gen_graph_by_codeunits(codeunits: List[CodeUnit]):
    """
    根据 CodeUnitList 生成知识图谱。

    :param codeunits: 包含多个 CodeUnit 对象的列表
    :return: 返回生成的知识图谱 (networkx 图)
    """
    # 创建一个有向图
    G = nx.DiGraph()
    # 添加节点和边
    for unit in codeunits:
        source_name = unit.name+"|"+unit.source_name
        target_name = unit.name+"|"+unit.target_name
        # 添加节点
        G.add_node(source_name,source_code=unit.source_code,target_name=unit.target_name,source_name=unit.source_name, desc=unit.source_desc, start_code_line=unit.start_code_line, end_code_line=unit.end_code_line,name=unit.name,path=unit.path)

        if not G.has_node(target_name):
            G.add_node(target_name,source_code=unit.source_code,source_name=unit.source_name, target_name=unit.target_name,desc=unit.source_desc, start_code_line=unit.start_code_line, end_code_line=unit.end_code_line,name=unit.name,path=unit.path)
        # 添加边
        G.add_edge(source_name, target_name)
    return G

# 可视化图
def visualize_graph(G, layout=nx.spring_layout, node_size=700, node_color="lightblue", font_size=10, arrowsize=20):
    """
    使用 Matplotlib 可视化知识图谱，并允许选择不同的布局方法。

    :param G: 知识图谱 (networkx 图)
    :param layout: 布局函数，默认为 spring_layout，可以是任何 NetworkX 布局函数
    :param node_size: 节点大小
    :param node_color: 节点颜色
    :param font_size: 字体大小
    :param arrowsize: 箭头大小
    """
    # 应用指定的布局方法
    pos = layout(G)

    # 绘制节点
    node_labels = {node: node for node in G.nodes()}
    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color=node_color)
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=font_size, font_family="sans-serif")

    # 绘制边
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), arrowstyle='->', arrowsize=arrowsize)
    plt.show()


def calculate_md5(text):
    """
    计算给定文本的MD5哈希值。

    参数:
    text (str): 要计算哈希值的文本。

    返回:
    str: 给定文本的MD5哈希值。
    """
    # 创建一个md5哈希对象
    hash_object = hashlib.md5()

    # 更新哈希对象，使用encode()方法将字符串转换为字节类型
    hash_object.update(text.encode())

    # 获取十六进制表示的哈希值
    md5_hash = hash_object.hexdigest()

    return md5_hash


def find_all_paths(graph):
    """
    从图中所有入度为0的节点开始，找到并返回所有可能的路径，直到出度为0的节点。

    参数:
    graph: NetworkX有向图对象

    返回:
    所有可能路径的列表，每条路径表示为节点列表。
    """

    def dfs(current_node, path):
        """
        深度优先搜索(DFS)递归函数，用于查找所有路径。

        参数:
        current_node: 当前正在处理的节点
        path: 当前路径上的节点列表
        """
        # 如果当前节点没有邻居，则是一条完整路径（出度为0）
        if graph.out_degree(current_node) == 0:
            paths.append(path.copy())
            return

        for neighbor in graph.successors(current_node):
            if neighbor not in path:  # 防止环路
                path.append(neighbor)
                dfs(neighbor, path)
                path.pop()  # 回溯

    # 计算每个节点的入度
    in_degrees = {node: degree for node, degree in graph.in_degree()}

    # 找出入度为0的节点
    nodes_with_zero_indegree = [node for node, degree in in_degrees.items() if degree == 0]

    # 存储所有找到的路径
    paths = []

    # 对于每个入度为0的节点，找到所有路径
    for node in nodes_with_zero_indegree:
        if graph.out_degree(node) > 0:  # 只考虑有后续节点的节点
            dfs(node, [node])
        else:
            # 如果入度为0且出度也为0，直接将其视为一条完整的路径
            paths.append([node])

    return paths

#写入文件
def write_file(file,text):
    with open(file,"w",encoding="utf-8") as f:
        f.write(text)