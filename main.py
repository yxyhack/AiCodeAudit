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
    parser.add_argument('-d', type=str, help='目标项目目录路径', default="./演示项目/RuoYi-Vue-master/ruoyi-admin")
    parser.add_argument('-o', type=str, default="./output", help="输出文件目录，默认是./output")
    parser.add_argument('-b', type=int, default=10, help="并发数量，默认是10")

    # 解析命令行参数
    args = parser.parse_args()
    logger.info(f"当前项目目录:{args.d}")
    logger.info(f"当前输出文件:{args.o}")
    if not os.path.exists(args.o):
        os.makedirs(args.o)
    return args
#
async def async_run_agent_1(source_file_list:List[SourceFile],out_file,batch_size=10):
    logger.info(f"当前batch_size:{batch_size}")
    batches = [source_file_list[i:i + batch_size] for i in range(0, len(source_file_list), batch_size)]
    res_list=[]
    logger.debug(source_file_list)
    for batch in tqdm(batches,total=len(batches),desc="异步并发执行中..."):
        tasks = [asyncio.create_task(agent_1(s)) for s in batch]
        r_list=await asyncio.gather(*tasks)
        for r in r_list:
            res_list.extend(r)
            logger.debug(r)
    g=gen_graph_by_codeunits(res_list)
    #输出结果至临时目录
    nx.write_graphml(g, out_file)
    logger.info(f"Agent_1计算完毕，输出文件:{out_file}")

async def async_run_agent_2(g:nx.Graph,out_file,batch_size=10):
    all_paths=find_all_paths(g)
    text_list=[]
    for path in all_paths:
        text=gen_text_from_path(g,path)
        text_list.append(text)
    logger.info(f"当前batch_size:{batch_size}")
    logger.info(f"数据大小:{len(text_list)}")
    logger.debug(text_list)
    batches = [text_list[i:i + batch_size] for i in range(0, len(text_list), batch_size)]
    res=""
    for batch in tqdm(batches, total=len(batches), desc="异步并发执行中..."):
        tasks = [asyncio.create_task(agent_2(s)) for s in batch]
        r_list = await asyncio.gather(*tasks)
        for r in r_list:
            res+=r+"\n--------------------------------\n"
            logger.debug(r)
        write_file(out_file,res)
    logger.info(f"Agent_2计算完毕，输出文件:{out_file}")


def main():
    args = init()
    root_dir = scan_project_struct(args.d)
    md5=calculate_md5(print_source_dir(root_dir))
    logger.info("解析目录结构如下\n"+print_source_dir(root_dir))
    logger.info(f"项目MD5:{md5}")
    out_graph_file=f"{args.o}/{md5}.graphml"
    if not os.path.exists(out_graph_file):
        source_file_lis=get_all_source_files_bfs(root_dir)
        logger.info("调用异步处理Agent_1...")
        asyncio.run(async_run_agent_1(source_file_lis,out_file=out_graph_file,batch_size=args.b))
    else:
        logger.info("项目依赖解析文件存在，直接跳过")
    logger.info("调用异步处理Agent_2...")
    g = nx.read_graphml(out_graph_file)
    asyncio.run(async_run_agent_2(g,out_file=f"{args.o}/{md5}_审计结果.log",batch_size=args.b))
    logger.success(f"输出成功,请在目录:{args.o}查看")
if __name__=="__main__":
    main()