# AI Code Audit

基于AI的智能代码审计工具，通过深度学习和自然语言处理技术，自动化识别代码中的安全漏洞和潜在问题。

## 功能特点

- 智能代码分析：利用AI技术自动分析代码结构和依赖关系
- 并发处理：支持多任务并行处理，提高审计效率
- 可视化输出：生成直观的审计报告和依赖关系图
- 跨语言支持：可以分析多种编程语言的源代码

## 安装说明

1. 克隆项目到本地：
```bash
git clone https://github.com/yxyhack/AiCodeAudit.git
cd AiCodeAudit
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

### 命令行参数

```bash
python main.py -d <target_dir> -o <output_dir> -b <batch_size>
```

参数说明：
- `-d`：目标项目目录路径（默认："./演示项目/openssh-9.9p1"）
- `-o`：输出文件目录（默认："./output"）
- `-b`：并发处理数量（默认：100）

### 示例

```bash
# 使用默认参数审计示例项目
python main.py

# 指定目标目录和输出目录
python main.py -d ./your-project -o ./audit-results

# 调整并发数量
python main.py -d ./your-project -b 50
```

## 输出结果

审计完成后，在输出目录中会生成以下文件：
- `<project_md5>.graphml`：项目依赖关系图
- `<project_md5>_审计结果.log`：详细的审计报告

## 配置文件

项目配置在`config.yaml`文件中，可以根据需要调整相关参数。

## 许可证

[MIT License](LICENSE)

## 贡献指南

欢迎提交Issue和Pull Request来帮助改进项目。

