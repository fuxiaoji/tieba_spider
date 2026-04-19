#!/bin/bash
# 贴吧帖子爬虫启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 检查Python3
if ! command -v python3 &>/dev/null; then
    echo "错误: 未找到 python3，请先安装 Python 3"
    exit 1
fi

# 检查PyQt6
if ! python3 -c "from PyQt6.QtWidgets import QApplication" 2>/dev/null; then
    echo "正在安装 PyQt6..."
    pip3 install PyQt6 --quiet
fi

# 启动应用
python3 tieba_app.py "$@"
