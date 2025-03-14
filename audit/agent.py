# 初始化LLM
from typing import List

import networkx as nx
from openai import OpenAI, AsyncOpenAI
import os
import json
import ssl
import httpx
import warnings
import urllib3
import asyncio
import random
from loguru import logger

from config import C
from models import SourceFile, CodeUnit
from prompt import PROMPT_AGENT_1, PROMPT_AGENT_2
from utils import parse_code_uint, gen_graph_by_codeunits
from utils.persistence import save_agent1_result, save_agent2_result, get_agent1_result_by_source

# 屏蔽不安全请求的警告
warnings.filterwarnings('ignore', message='Unverified HTTPS request')
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 创建忽略SSL验证的httpx客户端
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

http_client = httpx.AsyncClient(
    verify=False,  # 禁用SSL验证
    timeout=180.0   # 增加到3分钟
)

llm = AsyncOpenAI(
    base_url=C.openai.base_url,
    api_key=C.openai.api_key,
    http_client=http_client,  # 使用自定义的http客户端
)

async def chat_completion_text(text: str, prompt: str):
    messages = []
    messages.append({
        "role": "system",
        "content": prompt
    })
    messages.append({
        "role": "user",
        "content": text
    })
    res = await chat_completion_messages(messages)
    return res

async def chat_completion_messages(messages: []) -> str:
    """带有强大重试机制的API调用函数"""
    max_retries = 5  # 最大重试次数
    initial_retry_delay = 3  # 初始延迟3秒
    
    for attempt in range(max_retries):
        try:
            response = await llm.chat.completions.create(
                model=C.openai.model,
                messages=messages
            )
            if response.choices:
                content = response.choices[0].message.content
                return content
            else:
                raise Exception("No response from OpenAI")
                
        except Exception as e:
            # 计算指数退避延迟（带随机抖动）
            delay = initial_retry_delay * (2 ** attempt) + random.uniform(0, 1)
            
            if attempt < max_retries - 1:
                logger.warning(f"API请求失败 (尝试 {attempt+1}/{max_retries}): {str(e)}")
                logger.info(f"等待 {delay:.2f} 秒后重试...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"在 {max_retries} 次尝试后API请求仍然失败: {str(e)}")
                raise  # 最后一次尝试后仍然失败，抛出异常
    
    raise Exception("超过最大重试次数")

# 负责解析项目依赖，生成项目依赖图谱
async def agent_1(sourceFile: SourceFile) -> List[nx.Graph]:
    """
    使用语言模型解析代码中的依赖关系。

    :param sourceFile:
    :param code: 输入的 Python 代码字符串
    :return: 解析后的依赖关系描述字符串
    """
    # 首先检查是否有缓存结果
    cached_result = get_agent1_result_by_source(sourceFile.source_code)
    if cached_result:
        # 使用缓存的AI响应结果
        response = cached_result["ai_response"]
    else:
        # 没有缓存，调用API获取结果
        response = await chat_completion_text(sourceFile.source_code, PROMPT_AGENT_1)
        # 保存结果到持久化存储
        save_agent1_result(sourceFile.path, sourceFile.source_code, response)
    
    # 解析为对象数据
    res = parse_code_uint(code=sourceFile.source_code, path=sourceFile.path, name=sourceFile.name, input_text=response)
    return res

async def agent_2(text: str) -> str:
    # 调用API获取结果
    response = await chat_completion_text(text, PROMPT_AGENT_2)
    # 保存结果到持久化存储
    save_agent2_result(text, response)
    # 解析为对象数据
    return response