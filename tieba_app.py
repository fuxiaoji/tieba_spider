"""
贴吧帖子爬虫 - 桌面应用程序 (PyQt6)
支持 macOS / Windows / Linux
"""

import sys
import os
import threading
import subprocess
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QCheckBox,
    QFileDialog, QProgressBar, QFrame, QSizePolicy, QScrollArea,
    QMessageBox, QSpacerItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon, QTextCursor

# 导入爬虫核心
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tieba_crawler import TiebaCrawler, extract_tid


# ── 样式表 ────────────────────────────────────────────────
STYLESHEET = """
QMainWindow, QWidget#central {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1a1a1a, stop:1 #262626);
}

QWidget#header {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #262626, stop:1 #1a1a1a);
    border-bottom: 3px solid #FF3366;
}

QLabel#app_title {
    color: #FFFFFF;
    font-size: 26px;
    font-weight: 900;
    letter-spacing: 2px;
}

QLabel#app_subtitle {
    color: #CCCCCC;
    font-size: 14px;
    font-style: italic;
}

QWidget#card {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2b2b2b, stop:1 #222222);
    border: 2px solid #FF3366;
    border-radius: 0px;
}

QLabel#card_title {
    color: #FF3366;
    font-size: 14px;
    font-weight: 900;
    padding: 12px 14px 10px 14px;
    background: #111111;
    border-bottom: 2px solid #FF3366;
}

QLabel.field_label {
    color: #BBBBCC;
    font-size: 13px;
    font-weight: bold;
}

QLineEdit {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #111111, stop:1 #1a1a1a);
    color: #FFFFFF;
    border: 2px solid #555555;
    border-radius: 0px;
    padding: 12px;
    font-size: 14px;
    font-family: "Menlo", "Consolas", monospace;
    selection-background-color: #FF3366;
}

QLineEdit:focus {
    border: 2px solid #FF3366;
}

QLineEdit::placeholder {
    color: #666666;
}

QPushButton#btn_primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF3366, stop:1 #FF5500);
    color: white;
    border: none;
    border-radius: 0px;
    padding: 14px 32px;
    font-size: 16px;
    font-weight: 900;
}

QPushButton#btn_primary:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF5500, stop:1 #FF3366);
}

QPushButton#btn_primary:pressed {
    background: #CC2244;
}

QPushButton#btn_primary:disabled {
    background: #444444;
    color: #888888;
}

QPushButton#btn_secondary {
    background: transparent;
    color: #FF3366;
    border: 2px solid #FF3366;
    border-radius: 0px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#btn_secondary:hover {
    background: #FF3366;
    color: #FFFFFF;
}

QPushButton#btn_secondary:pressed {
    background: #CC2244;
    border-color: #CC2244;
}

QPushButton#btn_stop {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF0000, stop:1 #CC0000);
    color: white;
    border: none;
    border-radius: 0px;
    padding: 10px 20px;
    font-size: 14px;
    font-weight: 900;
}

QPushButton#btn_stop:hover {
    background: #FF3333;
}

QPushButton#btn_clear {
    background: transparent;
    color: #888888;
    border: 1px solid #888888;
    border-radius: 0px;
    padding: 4px 12px;
    font-size: 12px;
}

QPushButton#btn_clear:hover {
    color: #FFFFFF;
    background: #555555;
}

QPushButton#btn_small {
    background: #333333;
    color: #DDDDDD;
    border: 2px solid #555555;
    border-radius: 0px;
    padding: 8px 16px;
    font-size: 12px;
    font-weight: bold;
}

QPushButton#btn_small:hover {
    background: #555555;
    border-color: #FF3366;
    color: #FFFFFF;
}

QCheckBox {
    color: #DDDDDD;
    font-size: 14px;
    font-weight: bold;
    spacing: 10px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 0px;
    border: 2px solid #888888;
    background: #111111;
}

QCheckBox::indicator:checked {
    background: #FF3366;
    border-color: #FF3366;
    image: none;
}

QCheckBox::indicator:hover {
    border-color: #FF3366;
}

QTextEdit {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0a0a0a, stop:1 #111111);
    color: #00FF00;
    border: none;
    padding: 12px;
    font-size: 13px;
    font-family: "Menlo", "Consolas", monospace;
    selection-background-color: #FF3366;
}

QScrollBar:vertical {
    background: #111111;
    width: 10px;
}

QScrollBar::handle:vertical {
    background: #444444;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #FF3366;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QProgressBar {
    background: #111111;
    border: none;
    height: 8px;
    text-align: center;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF3366, stop:1 #FFCC00);
}
"""


class CrawlerWorker(QObject):
    """爬虫工作线程信号"""
    log_signal = pyqtSignal(str, str)   # (message, tag)
    finished = pyqtSignal(str)           # output_file_path
    error = pyqtSignal(str)             # error_message

    def __init__(self, url, output_dir, download_images, include_subposts):
        super().__init__()
        self.url = url
        self.output_dir = output_dir
        self.download_images = download_images
        self.include_subposts = include_subposts
        self.crawler = None
        self._running = True

    def run(self):
        def progress_cb(msg):
            if not self._running:
                return
            tag = self._classify(msg)
            self.log_signal.emit(msg, tag)

        try:
            self.crawler = TiebaCrawler(
                output_dir=self.output_dir,
                download_images=self.download_images,
                include_subposts=self.include_subposts,
                progress_callback=progress_cb,
            )
            result = self.crawler.crawl(self.url)
            if self._running:
                self.finished.emit(result)
        except Exception as e:
            if self._running:
                self.error.emit(str(e))

    def stop(self):
        self._running = False
        if self.crawler:
            self.crawler.stop()

    def _classify(self, msg):
        if any(k in msg for k in ["✅", "成功", "完成"]):
            return "success"
        if any(k in msg for k in ["❌", "失败", "错误"]):
            return "error"
        if any(k in msg for k in ["警告", "跳过", "停止"]):
            return "warning"
        if any(k in msg for k in ["下载", "获取", "处理", "开始"]):
            return "info"
        return "normal"


class TiebaSpiderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("贴吧收割机")
        self.setMinimumSize(780, 640)
        self.resize(860, 700)
        self.setStyleSheet(STYLESHEET)

        self._worker = None
        self._thread = None
        self._last_output = None
        self._is_crawling = False

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 顶部标题栏
        layout.addWidget(self._build_header())

        # 主内容区（带滚动）
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #1A1B2E; border: none; }")

        content_widget = QWidget()
        content_widget.setStyleSheet("background: #1A1B2E;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        # URL 输入卡片
        content_layout.addWidget(self._build_url_card())

        # 选项卡片
        content_layout.addWidget(self._build_options_card())

        # 日志卡片（可伸缩）
        log_card = self._build_log_card()
        log_card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(log_card, stretch=1)

        # 操作按钮栏
        content_layout.addWidget(self._build_action_bar())

        scroll.setWidget(content_widget)
        layout.addWidget(scroll, stretch=1)

    def _build_header(self):
        header = QWidget()
        header.setObjectName("header")
        header.setFixedHeight(80)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(30, 0, 20, 0)
        layout.setSpacing(15)

        title = QLabel("抓帖机器")
        title.setObjectName("app_title")
        layout.addWidget(title)
        
        layout.addSpacing(20)

        subtitle = QLabel("别废话，连图带回复全给你扒下来。")
        subtitle.setObjectName("app_subtitle")
        layout.addWidget(subtitle)
        layout.addStretch()

        return header

    def _make_card(self, title_text):
        """创建带标题的卡片"""
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        title = QLabel(title_text)
        title.setObjectName("card_title")
        card_layout.addWidget(title)

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 12, 14, 14)
        content_layout.setSpacing(8)
        card_layout.addWidget(content)

        return card, content_layout

    def _build_url_card(self):
        card, layout = self._make_card("[ 盯上哪个帖？ ]")

        hint = QLabel("喂个帖子ID或者链接给我：")
        hint.setProperty("class", "field_label")
        hint.setStyleSheet("color: #BBBBCC; font-size: 13px; font-weight: bold;")
        layout.addWidget(hint)

        url_row = QHBoxLayout()
        url_row.setSpacing(12)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("给个链接，或者直接留个纯数字ID也行")
        self.url_input.returnPressed.connect(self._start_crawl)
        url_row.addWidget(self.url_input)

        clear_btn = QPushButton("滚")
        clear_btn.setObjectName("btn_small")
        clear_btn.setFixedWidth(40)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self.url_input.clear())
        url_row.addWidget(clear_btn)

        layout.addLayout(url_row)
        layout.addSpacing(10)

        example = QLabel("比如: https://tieba.baidu.com/p/7487460366")
        example.setStyleSheet("color: #666666; font-size: 12px; font-style: italic;")
        layout.addWidget(example)

        return card

    def _build_options_card(self):
        card, layout = self._make_card("[ 还有啥要求？ ]")

        # 复选框行
        check_row = QHBoxLayout()
        check_row.setSpacing(30)

        self.cb_images = QCheckBox("连图一块顺走")
        self.cb_images.setChecked(True)
        check_row.addWidget(self.cb_images)

        self.cb_subposts = QCheckBox("楼中楼也不撒手")
        self.cb_subposts.setChecked(True)
        check_row.addWidget(self.cb_subposts)

        check_row.addStretch()
        layout.addLayout(check_row)
        layout.addSpacing(15)

        # 输出目录行
        dir_row = QHBoxLayout()
        dir_row.setSpacing(10)

        dir_label = QLabel("你想塞哪儿：")
        dir_label.setStyleSheet("color: #BBBBCC; font-size: 13px; font-weight: bold;")
        dir_row.addWidget(dir_label)

        self.dir_input = QLineEdit()
        self.dir_input.setText(os.path.expanduser("~/Desktop/tieba_output"))
        dir_row.addWidget(self.dir_input)

        browse_btn = QPushButton("换地方")
        browse_btn.setObjectName("btn_small")
        browse_btn.setFixedWidth(80)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)

        layout.addLayout(dir_row)

        return card

    def _build_log_card(self):
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # 标题栏
        title_bar = QWidget()
        title_bar.setStyleSheet("background: #111111; border-bottom: 2px solid #FF3366;")
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(14, 10, 14, 10)

        title_label = QLabel("[ 干活实况 ]")
        title_label.setStyleSheet("color: #FF3366; font-size: 14px; font-weight: 900; background: transparent;")
        title_bar_layout.addWidget(title_label)
        title_bar_layout.addStretch()

        clear_btn = QPushButton("毁尸灭迹")
        clear_btn.setObjectName("btn_clear")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_log)
        title_bar_layout.addWidget(clear_btn)

        card_layout.addWidget(title_bar)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定模式
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setVisible(False)
        card_layout.addWidget(self.progress_bar)

        # 日志文本框
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        card_layout.addWidget(self.log_text, stretch=1)

        return card

    def _build_action_bar(self):
        bar = QWidget()
        bar.setStyleSheet("background: transparent;")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(15)

        # 打开文件按钮（初始隐藏）
        self.open_file_btn = QPushButton("瞅瞅扒下来的货")
        self.open_file_btn.setObjectName("btn_secondary")
        self.open_file_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_file_btn.clicked.connect(self._open_output_file)
        self.open_file_btn.setVisible(False)
        layout.addWidget(self.open_file_btn)

        # 打开目录按钮（初始隐藏）
        self.open_dir_btn = QPushButton("直接去窝点")
        self.open_dir_btn.setObjectName("btn_secondary")
        self.open_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_dir_btn.clicked.connect(self._open_output_dir)
        self.open_dir_btn.setVisible(False)
        layout.addWidget(self.open_dir_btn)

        layout.addStretch()

        # 停止按钮（初始隐藏）
        self.stop_btn = QPushButton("认怂停手")
        self.stop_btn.setObjectName("btn_stop")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.clicked.connect(self._stop_crawl)
        self.stop_btn.setVisible(False)
        layout.addWidget(self.stop_btn)

        # 开始按钮
        self.start_btn = QPushButton("搞快点！")
        self.start_btn.setObjectName("btn_primary")
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self._start_crawl)
        self.start_btn.setFixedHeight(50)
        layout.addWidget(self.start_btn)

        return bar

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "挑个地儿存",
            self.dir_input.text() or os.path.expanduser("~")
        )
        if d:
            self.dir_input.setText(d)

    def _clear_log(self):
        self.log_text.clear()

    def _log(self, msg: str, tag: str = "normal"):
        """向日志框写入带颜色的消息"""
        colors = {
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800",
            "info": "#5A9EF5",
            "normal": "#C8C8E8",
        }
        time_color = "#555570"
        msg_color = colors.get(tag, colors["normal"])

        time_str = datetime.now().strftime("%H:%M:%S")
        html = (
            f'<span style="color:{time_color};">[{time_str}]</span> '
            f'<span style="color:{msg_color};">{self._escape_html(msg)}</span>'
        )
        self.log_text.append(html)
        # 滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)

    def _escape_html(self, text):
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def _start_crawl(self):
        if self._is_crawling:
            return

        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "喂喂喂", "没链接你让我爬空气？")
            return

        try:
            tid = extract_tid(url)
        except ValueError as e:
            QMessageBox.critical(self, "炸了", str(e))
            return

        output_dir = self.dir_input.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "提示", "塞哪儿你倒是说啊？")
            return

        # 更新UI
        self._is_crawling = True
        self._last_output = None
        self.start_btn.setEnabled(False)
        self.start_btn.setText("疯狂薅羊毛中...")
        self.stop_btn.setVisible(True)
        self.open_file_btn.setVisible(False)
        self.open_dir_btn.setVisible(False)
        self.progress_bar.setVisible(True)

        self._log(f"开干: {url}", "info")
        self._log(f"塞到这: {output_dir}", "info")

        # 启动后台线程
        self._worker = CrawlerWorker(
            url=url,
            output_dir=output_dir,
            download_images=self.cb_images.isChecked(),
            include_subposts=self.cb_subposts.isChecked(),
        )
        self._worker.log_signal.connect(self._log)
        self._worker.finished.connect(self._on_success)
        self._worker.error.connect(self._on_error)

        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _stop_crawl(self):
        if self._worker:
            self._worker.stop()
        self._log("停就停，怂啥。", "warning")
        self._reset_ui()

    def _on_success(self, output_file):
        self._last_output = output_file
        self._log(f"搞定！全扒下来了！", "success")
        self._log(f"货在这儿: {output_file}", "success")
        self._reset_ui()
        self.open_file_btn.setVisible(True)
        self.open_dir_btn.setVisible(True)
        if self._thread:
            self._thread.quit()

    def _on_error(self, error_msg):
        self._log(f"翻车啦: {error_msg}", "error")
        self._reset_ui()
        if self._thread:
            self._thread.quit()

    def _reset_ui(self):
        self._is_crawling = False
        self.start_btn.setEnabled(True)
        self.start_btn.setText("搞快点！")
        self.stop_btn.setVisible(False)
        self.progress_bar.setVisible(False)

    def _open_output_file(self):
        if self._last_output and os.path.exists(self._last_output):
            if sys.platform == "darwin":
                subprocess.run(["open", self._last_output])
            elif sys.platform == "win32":
                os.startfile(self._last_output)
            else:
                subprocess.run(["xdg-open", self._last_output])
        else:
            QMessageBox.information(self, "别闹", "货不见了，你再爬一次吧")

    def _open_output_dir(self):
        d = self.dir_input.text()
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        if sys.platform == "darwin":
            subprocess.run(["open", d])
        elif sys.platform == "win32":
            subprocess.run(["explorer", d])
        else:
            subprocess.run(["xdg-open", d])

    def closeEvent(self, event):
        if self._is_crawling and self._worker:
            self._worker.stop()
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        event.accept()


def main():
    # 设置高DPI支持（必须在创建QApplication之前调用）
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("贴吧收割机")
    app.setOrganizationName("TiebaReaper")

    window = TiebaSpiderApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
