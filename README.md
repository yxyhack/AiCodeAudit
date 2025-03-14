# AiCodeAudit

[English Version](#english-version) | [中文版本](#chinese-version)

<a id="english-version"></a>
# English Version

## Introduction

AiCodeAudit is an AI-powered code audit tool designed to help developers automatically detect potential issues, security vulnerabilities, and quality defects in code.

## Features

- Automated code auditing
- Security vulnerability detection
- Code quality assessment
- Multi-language support
- Flexible configuration

## System Architecture

AiCodeAudit consists of the following core components:

1. **Code Parser** - Responsible for reading and parsing source code files in different languages
2. **AI Analysis Engine** - Based on OpenAI API for intelligent code analysis
3. **Vulnerability Detection Module** - Focuses on identifying security vulnerabilities
4. **Quality Assessment Module** - Evaluates code quality and maintainability
5. **Report Generator** - Generates detailed audit reports

## Installation

### Prerequisites

- Python 3.8+
- Git
- OpenAI API key

### Installation Steps

```bash
git clone https://github.com/yxyhack/AiCodeAudit.git
cd AiCodeAudit
pip install -r requirements.txt
```

## Usage

### Basic Usage

1. Configure your OpenAI API key in `config.yaml`:

```yaml
api:
  openai_api_key: "your-api-key-here"
```

2. Run the audit:

```bash
python main.py --path /path/to/your/code --output ./audit_report
```

### Command Line Arguments

```bash
python main.py [options]

Options:
  --path PATH          Path to the code directory to audit (required)
  --output PATH        Output directory for audit reports (default: ./output)
  --config PATH        Path to custom config file (default: ./config.yaml)
  --language LANG      Specify programming language (default: auto-detect)
  --depth N            Maximum directory depth to scan (default: 3)
  --exclude PATTERN    Exclude files/directories matching pattern
  --verbose           Enable verbose output
```

### Configuration Examples

1. Basic configuration (`config.yaml`):
```yaml
api:
  openai_api_key: "your-api-key-here"
  model: "gpt-4"

scan:
  max_depth: 3
  exclude_patterns:
    - "*.pyc"
    - "__pycache__"
    - ".git"

output:
  format: "html"
  detail_level: "medium"
```

2. Advanced configuration:
```yaml
api:
  openai_api_key: "your-api-key-here"
  model: "gpt-4"
  temperature: 0.7

scan:
  max_depth: 5
  exclude_patterns:
    - "*.pyc"
    - "__pycache__"
    - ".git"
    - "node_modules"
  include_patterns:
    - "*.py"
    - "*.js"
    - "*.java"

output:
  format: "html,json"
  detail_level: "high"
  report_path: "./audit_reports"

analysis:
  security:
    enabled: true
    risk_level: "medium"
  quality:
    enabled: true
    metrics:
      - "complexity"
      - "duplication"
      - "maintainability"
```

### Common Use Cases

1. Quick scan of a Python project:
```bash
python main.py --path ./my_python_project --language python
```

2. Detailed audit with custom configuration:
```bash
python main.py --path ./project --config ./custom_config.yaml --verbose
```

3. Scan specific directories with exclusions:
```bash
python main.py --path ./project --exclude "tests/*,docs/*" --depth 4
```

4. Generate multiple format reports:
```bash
python main.py --path ./project --output ./reports --config config.yaml
```

<a id="chinese-version"></a>
# 中文版本

## 简介

AiCodeAudit是一个基于AI的代码审计工具，旨在帮助开发者自动检测代码中的潜在问题、安全漏洞和质量缺陷。

## 功能特点

- 自动代码审计
- 安全漏洞检测
- 代码质量评估
- 多语言支持
- 配置灵活

## 系统架构

AiCodeAudit由以下几个核心组件构成：

1. **代码解析器** - 负责读取和解析不同语言的源代码文件
2. **AI分析引擎** - 基于OpenAI API，对代码进行智能分析
3. **漏洞检测模块** - 专注于识别安全漏洞
4. **质量评估模块** - 评估代码质量和可维护性
5. **报告生成器** - 生成详细的审计报告

## 安装

### 前置条件

- Python 3.8+
- Git
- OpenAI API密钥

### 安装步骤

```bash
git clone https://github.com/yxyhack/AiCodeAudit.git
cd AiCodeAudit
pip install -r requirements.txt
```

## 使用说明

### 基本使用

1. 在`config.yaml`中配置OpenAI API密钥：

```yaml
api:
  openai_api_key: "你的API密钥"
```

2. 运行审计：

```bash
python main.py --path /path/to/your/code --output ./audit_report
```

### 命令行参数

```bash
python main.py [选项]

选项：
  --path PATH          要审计的代码目录路径（必需）
  --output PATH        审计报告输出目录（默认：./output）
  --config PATH        自定义配置文件路径（默认：./config.yaml）
  --language LANG      指定编程语言（默认：自动检测）
  --depth N            最大扫描目录深度（默认：3）
  --exclude PATTERN    排除匹配模式的文件/目录
  --verbose           启用详细输出
```

### 配置示例

1. 基本配置（`config.yaml`）：
```yaml
api:
  openai_api_key: "你的API密钥"
  model: "gpt-4"

scan:
  max_depth: 3
  exclude_patterns:
    - "*.pyc"
    - "__pycache__"
    - ".git"

output:
  format: "html"
  detail_level: "medium"
```

2. 高级配置：
```yaml
api:
  openai_api_key: "你的API密钥"
  model: "gpt-4"
  temperature: 0.7

scan:
  max_depth: 5
  exclude_patterns:
    - "*.pyc"
    - "__pycache__"
    - ".git"
    - "node_modules"
  include_patterns:
    - "*.py"
    - "*.js"
    - "*.java"

output:
  format: "html,json"
  detail_level: "high"
  report_path: "./audit_reports"

analysis:
  security:
    enabled: true
    risk_level: "medium"
  quality:
    enabled: true
    metrics:
      - "complexity"
      - "duplication"
      - "maintainability"
```

### 常见使用场景

1. 快速扫描Python项目：
```bash
python main.py --path ./my_python_project --language python
```

2. 使用自定义配置进行详细审计：
```bash
python main.py --path ./project --config ./custom_config.yaml --verbose
```

3. 扫描特定目录并排除部分内容：
```bash
python main.py --path ./project --exclude "tests/*,docs/*" --depth 4
```

4. 生成多种格式的报告：
```bash
python main.py --path ./project --output ./reports --config config.yaml
```
