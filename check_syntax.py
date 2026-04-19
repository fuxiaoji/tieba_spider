import ast
import sys

files = ['tieba_app.py', 'tieba_crawler.py']
for fname in files:
    with open(fname, 'r') as f:
        source = f.read()
    try:
        ast.parse(source)
        print(f'[OK] {fname} 语法检查通过')
    except SyntaxError as e:
        print(f'[ERROR] {fname} 语法错误: {e}')
        sys.exit(1)

try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QThread, pyqtSignal, QObject
    print('[OK] PyQt6 导入成功')
except ImportError as e:
    print(f'[ERROR] PyQt6 导入失败: {e}')
    sys.exit(1)

from tieba_crawler import TiebaCrawler, extract_tid
print('[OK] tieba_crawler 导入成功')
print('所有检查通过！')
