import os
import sys
import time
import warnings
import pandas as pd
import utils.language as lg

from utils.logger import logger
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore    import Qt, QThread, pyqtSignal
from PyQt6.QtGui     import QIcon
from PyQt6.QtWidgets import QProgressBar

class FileLoadThread(QThread):
    # 信号：传递加载的数据和进度
    data_loaded = pyqtSignal(list)
    progress_updated = pyqtSignal(int)

    def __init__(self, file_path, chunk_size=300):
        super().__init__()
        self.file_path = file_path
        self.chunk_size = chunk_size

    def run(self):
        """ 线程运行的方法，逐块读取文件并更新进度 """
        chunk_iterator = pd.read_csv(self.file_path, sep="\t", chunksize=self.chunk_size, dtype=str)  # 添加 dtype=str
        df_chunks = []
        total_chunks = 0

        # 先计算总块数，以便后续更新进度
        for _ in chunk_iterator:
            total_chunks += 1

        chunk_iterator = pd.read_csv(self.file_path, sep="\t", chunksize=self.chunk_size, dtype=str)  # 重置迭代器

        current_chunk = 0
        for chunk in chunk_iterator:
            df_chunks.append(chunk)
            current_chunk += 1

            # 更新进度条：将文件读取进度和UI渲染进度加权计算
            progress = int((current_chunk / total_chunks) * 50)  # 50% 的进度来自文件读取
            self.progress_updated.emit(progress)  # 文件读取进度

            # 模拟渲染时间，更新 UI 渲染进度
            for row in range(chunk.shape[0]):
                # 每渲染一行就更新一下进度条（这里假设每行渲染花费时间相等）
                progress += int(50 / total_chunks / chunk.shape[0])  # UI 渲染进度（占50%）
                self.progress_updated.emit(progress)

        # 发射数据加载完成信号
        self.data_loaded.emit(df_chunks)

class TableApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(lg.EXE_TITLE)
        icon = QIcon("static/cokeserver.ico")
        if not icon.isNull():
            logger.info("Icon loaded successfully")
        else:
            logger.info("Failed to load icon")

        self.setWindowIcon(QIcon("static/cokeserver.ico"))
        self.setGeometry(200, 200, 900, 600)

        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

        # 添加进度条显示
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        # 文件操作按钮
        file_layout = QHBoxLayout()
        self.upload_btn = QPushButton(lg.EXE_BUTTON_UPLOAD)
        self.upload_btn.clicked.connect(self.load_file)
        file_layout.addWidget(self.upload_btn)

        self.save_btn = QPushButton(lg.EXE_BUTTON_SAVE)
        self.save_btn.clicked.connect(self.save_file)
        self.save_btn.setEnabled(False)  # 初始禁用
        file_layout.addWidget(self.save_btn)
        layout.addLayout(file_layout)

        # 搜索框
        search_layout = QHBoxLayout()
        self.search_label = QLabel(lg.EXE_INPUT_LABEL)
        search_layout.addWidget(self.search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(lg.EXE_INPUT_PLACEHOLDER)
        self.search_input.textChanged.connect(self.search_table)
        search_layout.addWidget(self.search_input)

        layout.addLayout(search_layout)

        # 表格控件
        self.table = QTableWidget()
        layout.addWidget(self.table)

        self.central_widget.setLayout(layout)

        self.df = None              # 数据存储
        self.file_path = None       # 记录当前文件路径
        self.change_file_name = ''  # 记录修改的文件名
        self.df_chunks = []         # 存储分块的数据
        self.current_chunk_index = 0  # 当前显示的数据块索引

        # 连接单元格修改信号
        self.table.cellChanged.connect(self.cell_changed)

        # 添加显示文件状态标签
        self.file_label = QLabel(lg.EXE_OPEN_FILE_STATUS_COMMON)  # 初始显示
        layout.addWidget(self.file_label)     # 添加到界面顶部

        # 分页按钮
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self.show_prev_chunk)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self.show_next_chunk)
        layout.addWidget(self.next_btn)

        # 显示当前页数和总页数
        self.page_label = QLabel("当前页: 1 / 总页数: 1")  # 显示第一页
        layout.addWidget(self.page_label)

        # 跳转到指定页数
        self.page_input = QLineEdit()
        self.page_input.setPlaceholderText("输入页数")
        layout.addWidget(self.page_input)

        self.go_btn = QPushButton("跳转")
        self.go_btn.clicked.connect(self.go_to_page)
        layout.addWidget(self.go_btn)

    def load_file(self):
        """ 加载 TXT 文件（使用后台线程避免卡死）"""
        file_path, _ = QFileDialog.getOpenFileName(self, lg.EXE_BUTTON_UPLOAD, "", "Text Files (*.txt)")
        if file_path:
            self.file_path = file_path

            # 创建并启动后台线程
            self.thread = FileLoadThread(file_path)
            self.thread.data_loaded.connect(self.on_data_loaded)  # 绑定信号
            self.thread.progress_updated.connect(self.update_progress)  # 绑定进度更新信号
            self.thread.start()

            # 禁用文件加载按钮，防止重复点击
            self.upload_btn.setEnabled(False)

            # 初始化进度条
            self.progress_bar.setValue(0)  # 重置进度条

    def update_progress(self, progress):
        """ 更新进度条 """
        self.progress_bar.setValue(progress)

    def on_data_loaded(self, df_chunks):
        """ 数据加载完成后，更新 UI """
        self.df_chunks = df_chunks
        self.df_chunks = [chunk.fillna('') for chunk in self.df_chunks]
        
        # 如果文件有数据，显示第一块数据
        if self.df_chunks:
            self.df = self.df_chunks[0]
            self.current_chunk_index = 0  # 重置为第 1 页
            self.display_table()  # 显示第一页

            # 启用保存按钮
            self.save_btn.setEnabled(True)

            file_name = os.path.basename(self.file_path)
            logger.info(f'Open txt file successfully: {self.file_path}')
            
            self.change_file_name = file_name
            self.setWindowTitle(f"{lg.EXE_TITLE} - {file_name}")
            self.file_label.setText(lg.EXE_OPEN_FILE_STATUS_ACTIVE % file_name)  # 在界面上显示文件名

            # 启用加载按钮
            self.upload_btn.setEnabled(True)

            # 进度条完成
            self.progress_bar.setValue(100)

    def display_table(self):
        """ 显示数据到表格 """
        chunk_data = self.df  # 当前页数据
        self.table.setRowCount(chunk_data.shape[0])
        self.table.setColumnCount(chunk_data.shape[1])
        self.table.setHorizontalHeaderLabels(chunk_data.columns)

        # 设置表头字体颜色（红色）
        header = self.table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { color: red; font-weight: bold; }")

        # 填充表格
        for row in range(chunk_data.shape[0]):
            for col in range(chunk_data.shape[1]):
                value = "" if pd.isna(chunk_data.iat[row, col]) else str(chunk_data.iat[row, col])  # 处理 NaN
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

        # 获取总页数
        total_pages = len(self.df_chunks)
        # 更新当前页数标签：当前页 / 总页数
        self.page_label.setText(f"当前页: {self.current_chunk_index + 1} / 总页数: {total_pages}")

    def save_file(self):
        """ 保存整个文件，而不仅仅是当前页的数据 """
        if self.df_chunks:
            # 合并所有分块的数据
            full_data = pd.concat(self.df_chunks, ignore_index=True)

            # 将所有数据转换为字符串类型
            full_data = full_data.astype(str)
            full_data = full_data.fillna('')

            # 保存整个文件
            save_path, _ = QFileDialog.getSaveFileName(self, lg.EXE_SAVE_FILE, self.change_file_name, "Text Files (*.txt)")
            if save_path:
                full_data.to_csv(save_path, sep="\t", index=False)  # 保存为整个文件
                logger.info(f'Save txt file successfully: {save_path}')
                QMessageBox.information(self, lg.EXE_SAVE_FILE_SUCC, lg.EXE_SAVE_FILE_PATH % save_path)

    def search_table(self):
        """ 搜索表格内容 """
        if self.df is None:
            return

        keyword = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            row_hidden = True
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and keyword in item.text().lower():
                    row_hidden = False
                    break
            self.table.setRowHidden(row, row_hidden)

    def cell_changed(self, row, col):
        """ 当单元格内容发生变化时，同步到 self.df """
        item = self.table.item(row, col)
        if item:
            # 将修改的内容同步到当前数据块 self.df
            self.df.iat[row, col] = item.text()  # 更新当前页数据块

            # 如果你想同步修改到所有数据块（可选）
            self.df_chunks[self.current_chunk_index].iat[row, col] = item.text()

    def show_next_chunk(self):
        """ 显示下一块数据 """
        if self.current_chunk_index + 1 < len(self.df_chunks):
            self.current_chunk_index += 1
            self.df = self.df_chunks[self.current_chunk_index]  # 获取下一块数据
            self.display_table()

    def show_prev_chunk(self):
        """ 显示上一块数据 """
        if self.current_chunk_index - 1 >= 0:
            self.current_chunk_index -= 1
            self.df = self.df_chunks[self.current_chunk_index]  # 获取上一块数据
            self.display_table()

    def go_to_page(self):
        """ 跳转到指定页数 """
        try:
            target_page = int(self.page_input.text()) - 1  # 页数从 1 开始，所以减去 1
            total_pages = len(self.df_chunks)
            if 0 <= target_page < total_pages:
                self.current_chunk_index = target_page
                self.df = self.df_chunks[self.current_chunk_index]  # 获取目标页的数据
                self.display_table()
            else:
                QMessageBox.warning(self, "无效页数", f"请输入有效页数 (1-{total_pages})")
        except ValueError:
            QMessageBox.warning(self, "输入无效", "请输入有效的数字页数。")

if __name__ == "__main__":
    sys.dont_write_bytecode = True
    warnings.filterwarnings('ignore')
    try:
        logger.info(f'The editor launch at {int(time.time())}')
        app = QApplication(sys.argv)
        window = TableApp()
        window.show()
        sys.exit(app.exec())
    except Exception as err:
        logger.error(err)
