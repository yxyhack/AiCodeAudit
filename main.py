import argparse
import os
from typing import List

import asyncio

import networkx as nx
from accelerate.commands.config.update import description
from loguru import logger
from tqdm import tqdm

from audit import scan_project_struct, print_source_dir, traverse_source_dir_bfs, get_all_source_files_bfs
from audit.agent import agent_1, agent_2
from audit.tool import gen_text_from_path
from config import C
from models import SourceFile
from utils import is_cmd_mode, gen_line_code, get_code_by_line, visualize_graph, gen_graph_by_codeunits, calculate_md5, \
    find_all_paths, write_file
from utils.persistence import get_all_agent1_results, set_output_dir, safe_read_json, get_execution_status, save_execution_status, EXECUTION_STATUS, get_code_units


def init():
    #初始化日志打印
    logger.add(sink="app.log", rotation="50 MB", format="{time} | {level} | {message}")
    #初始化参数配置
    logger.info("加载配置文件config.yaml")
    logger.info(C.dict())
    #判断执行模式
    logger.info("当前命令行模式:"+str(is_cmd_mode()))
    # 创建ArgumentParser对象
    parser = argparse.ArgumentParser(description="脚本说明")
    # 添加命令行参数
    # parser.add_argument('-d', type=str, help='目标项目目录路径', required=True)
    parser.add_argument('-d', type=str, help='目标项目目录路径', default="./演示项目/openssh-9.9p1")
    parser.add_argument('-o', type=str, default="./output", help="输出文件目录，默认是./output")
    parser.add_argument('-b', type=int, default=100, help="并发数量，默认是10")
    parser.add_argument("--resume", action="store_true", help="从上次中断点恢复执行")

    # 解析命令行参数
    args = parser.parse_args()
    logger.info(f"当前项目目录:{args.d}")
    logger.info(f"当前输出文件:{args.o}")
    if not os.path.exists(args.o):
        os.makedirs(args.o)
        
    # 设置持久化存储的输出目录
    set_output_dir(args.o)
    
    return args

async def async_run_agent_1(source_file_list:List[SourceFile], out_file, batch_size=10):
    logger.info(f"当前batch_size:{batch_size}")
    
    # 移除批处理大小降低逻辑，直接使用用户指定的batch_size
    batches = [source_file_list[i:i + batch_size] for i in range(0, len(source_file_list), batch_size)]
    res_list = []
    logger.debug(source_file_list)
    
    for batch_idx, batch in enumerate(tqdm(batches, total=len(batches), desc="异步并发执行中...")):
        try:
            tasks = [asyncio.create_task(agent_1(s)) for s in batch]
            r_list = await asyncio.gather(*tasks)
            
            for r in r_list:
                if r is None:
                    continue
                res_list.extend(r)
                logger.debug(r)
        except Exception as e:
            logger.error(f"处理批次 {batch_idx+1}/{len(batches)} 时发生错误: {str(e)}")
            logger.info("跳过此批次并继续执行...")
            continue
    
    g = gen_graph_by_codeunits(res_list)
    # 输出结果至临时目录
    nx.write_graphml(g, out_file)
    logger.info(f"Agent_1计算完毕，输出文件:{out_file}")
    
    # 返回代码单元列表，用于断点续传
    return res_list

async def async_run_agent_2(g:nx.Graph, out_file, batch_size=10):
    all_paths = find_all_paths(g)
    text_list = []
    for path in all_paths:
        text = gen_text_from_path(g, path)
        text_list.append(text)
    
    # 移除批处理大小降低逻辑
    logger.info(f"批处理大小:{batch_size}")
    logger.info(f"数据大小:{len(text_list)}")
    logger.debug(text_list)
    
    batches = [text_list[i:i + batch_size] for i in range(0, len(text_list), batch_size)]
    res = ""
    
    for batch_idx, batch in enumerate(tqdm(batches, total=len(batches), desc="异步并发执行中...")):
        tasks = [asyncio.create_task(agent_2(s)) for s in batch]
        r_list = await asyncio.gather(*tasks)
        
        for r in r_list:
            if r is None:
                continue
            res += r + "\n--------------------------------\n"
            logger.debug(r)
        
        write_file(out_file, res)
        
        # 保留批次间延迟，因为这有助于降低API请求频率
        if batch_idx < len(batches) - 1:
            delay = 5.0  # 延迟5秒
            logger.info(f"降低请求频率，等待 {delay} 秒...")
            await asyncio.sleep(delay)
    
    logger.info(f"Agent_2计算完毕，输出文件:{out_file}")

async def resume_from_checkpoint(args):
    """完整的断点续传功能"""
    from audit.agent import agent_1
    from utils import parse_code_uint
    
    # 扫描目录结构并计算MD5
    root_dir = scan_project_struct(args.d)
    md5 = calculate_md5(print_source_dir(root_dir))
    logger.info(f"项目MD5:{md5}")
    
    # 获取执行状态
    execution_status = get_execution_status(md5)
    status = execution_status.get("status", EXECUTION_STATUS["NOT_STARTED"])
    
    # 设置输出文件路径
    out_graph_file = execution_status.get("graph_file", f"{args.o}/{md5}.graphml")
    out_result_file = execution_status.get("result_file", f"{args.o}/{md5}_审计结果.log")
    
    logger.info(f"从状态 {status} 恢复执行")
    
    if status == EXECUTION_STATUS["NOT_STARTED"]:
        logger.info("没有找到之前的执行状态，将从头开始执行")
        # 从头开始执行
        source_file_lis=get_all_source_files_bfs(root_dir,chunk_token_size=C.openai.max_per_tokens)
        logger.info("调用异步处理Agent_1...")
        res_list = await async_run_agent_1(source_file_lis, out_file=out_graph_file, batch_size=args.b)
        
        # 保存代码单元列表和执行状态
        from utils.persistence import save_code_units, save_execution_status
        save_code_units(md5, res_list)
        save_execution_status(md5, EXECUTION_STATUS["AGENT1_COMPLETE"], out_graph_file)
        
        status = EXECUTION_STATUS["AGENT1_COMPLETE"]
    
    if status == EXECUTION_STATUS["AGENT1_COMPLETE"]:
        logger.info("从已完成Agent1分析的状态恢复")
        
        # 获取已保存的代码单元列表
        code_units = get_code_units(md5)
        
        if not code_units:
            # 如果没有保存的代码单元，重新获取
            logger.warning("未找到保存的代码单元列表，重新处理源文件")
            source_file_lis = get_all_source_files_bfs(root_dir, chunk_token_size=C.openai.max_per_tokens)
            
            # 重新获取AI分析结果（会使用缓存）
            all_code_units = []
            for source_file in tqdm(source_file_lis, desc="处理缓存的AI分析结果"):
                units = await agent_1(source_file)
                if units:
                    all_code_units.extend(units)
            
            code_units = all_code_units
        
        # 构建依赖图并保存
        g = gen_graph_by_codeunits(code_units)
        nx.write_graphml(g, out_graph_file)
        logger.info(f"依赖图构建完成，保存到 {out_graph_file}")
        
        # 更新执行状态
        save_execution_status(md5, EXECUTION_STATUS["GRAPH_BUILT"], out_graph_file)
        
        status = EXECUTION_STATUS["GRAPH_BUILT"]
    
    if status == EXECUTION_STATUS["GRAPH_BUILT"] or status == EXECUTION_STATUS["AGENT2_COMPLETE"]:
        logger.info("从已构建依赖图的状态恢复，继续进行安全分析")
        
        # 加载依赖图
        g = nx.read_graphml(out_graph_file)
        
        # 执行安全分析
        await async_run_agent_2(g, out_file=out_result_file, batch_size=args.b)
        
        # 更新执行状态为完成
        save_execution_status(md5, EXECUTION_STATUS["COMPLETED"], out_graph_file, out_result_file)
        
        logger.success(f"恢复执行完成，输出结果保存在 {args.o}")
    
    elif status == EXECUTION_STATUS["COMPLETED"]:
        logger.success(f"项目已完成分析，结果在目录:{args.o}")

def main():
    args = init()
    if args.resume:
        asyncio.run(resume_from_checkpoint(args))
    else:
        root_dir = scan_project_struct(args.d)
        md5 = calculate_md5(print_source_dir(root_dir))
        logger.info("解析目录结构如下\n"+print_source_dir(root_dir))
        logger.info(f"项目MD5:{md5}")
        out_graph_file=f"{args.o}/{md5}.graphml"
        out_result_file=f"{args.o}/{md5}_审计结果.log"
        
        # 获取执行状态
        execution_status = get_execution_status(md5)
        status = execution_status.get("status", EXECUTION_STATUS["NOT_STARTED"])
        
        # 根据执行状态决定从哪里开始
        if status == EXECUTION_STATUS["NOT_STARTED"] or status == EXECUTION_STATUS["AGENT1_COMPLETE"]:
            if not os.path.exists(out_graph_file) or status == EXECUTION_STATUS["NOT_STARTED"]:
                source_file_lis=get_all_source_files_bfs(root_dir,chunk_token_size=C.openai.max_per_tokens)
                logger.info("调用异步处理Agent_1...")
                res_list = asyncio.run(async_run_agent_1(source_file_lis,out_file=out_graph_file,batch_size=args.b))
                
                # 保存代码单元列表和执行状态
                from utils.persistence import save_code_units, save_execution_status
                save_code_units(md5, res_list)
                save_execution_status(md5, EXECUTION_STATUS["AGENT1_COMPLETE"], out_graph_file)
            else:
                logger.info("项目依赖解析文件存在，直接跳过Agent_1步骤")
        
        if status != EXECUTION_STATUS["COMPLETED"]:
            logger.info("调用异步处理Agent_2...")
            g = nx.read_graphml(out_graph_file)
            
            # 更新执行状态
            save_execution_status(md5, EXECUTION_STATUS["GRAPH_BUILT"], out_graph_file)
            
            asyncio.run(async_run_agent_2(g, out_file=out_result_file, batch_size=args.b))
            
            # 完成所有步骤，更新状态
            save_execution_status(md5, EXECUTION_STATUS["COMPLETED"], out_graph_file, out_result_file)
            
            logger.success(f"输出成功,请在目录:{args.o}查看")
        else:
            logger.success(f"项目已完成分析，结果在目录:{args.o}")

if __name__=="__main__":
    main()