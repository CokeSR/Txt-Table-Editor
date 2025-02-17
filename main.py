import os
import sys
import time
import warnings
import pandas as pd
import utils.language as lg

from utils.logger    import logger
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QTableWidget, QTableWidgetItem,
    QPushButton, QVBoxLayout, QWidget, QHBoxLayout, QLineEdit, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QIcon

class TableApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(lg.EXE_TITLE)
        self.setWindowIcon(QIcon("static/cokeserver.ico"))
        self.setGeometry(200, 200, 900, 600)

        # 主窗口布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()

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

        # 连接单元格修改信号
        self.table.cellChanged.connect(self.cell_changed)

        self.file_label = QLabel(lg.EXE_OPEN_FILE_STATUS_COMMON)  # 初始显示
        layout.addWidget(self.file_label)     # 添加到界面顶部

    def load_file(self):
        """ 加载 TXT 文件 """
        file_path, _ = QFileDialog.getOpenFileName(self, lg.EXE_BUTTON_UPLOAD, "", "Text Files (*.txt)")
        if file_path:
            self.file_path = file_path
            self.df = pd.read_csv(file_path, sep="\t")  # 读取制表符分隔的文件
            self.display_table()
            self.save_btn.setEnabled(True)  # 启用保存按钮

            file_name = os.path.basename(file_path)
            logger.info(f'Open txt file successfully: {file_path}')
            
            self.change_file_name = file_name
            self.setWindowTitle(f"{lg.EXE_TITLE} - {file_name}")
            self.file_label.setText(lg.EXE_OPEN_FILE_STATUS_ACTIVE % file_name)  # 在界面上显示文件名

    
    def display_table(self):
        """ 显示数据到表格 """
        self.table.setRowCount(self.df.shape[0])
        self.table.setColumnCount(self.df.shape[1])
        self.table.setHorizontalHeaderLabels(self.df.columns)

        # 设置表头字体颜色（红色）
        header = self.table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { color: red; font-weight: bold; }")

        # 填充表格
        for row in range(self.df.shape[0]):
            for col in range(self.df.shape[1]):
                value = "" if pd.isna(self.df.iat[row, col]) else str(self.df.iat[row, col])  # 处理 NaN
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, col, item)

    def save_file(self):
        """ 保存修改后的文件 """
        if self.df is not None:
            for row in range(self.df.shape[0]):
                for col in range(self.df.shape[1]):
                    self.df.iat[row, col] = self.table.item(row, col).text()

            save_path, _ = QFileDialog.getSaveFileName(self, lg.EXE_SAVE_FILE, self.change_file_name, "Text Files (*.txt)")
            if save_path:
                self.df.to_csv(save_path, sep="\t", index=False)
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
        """ 仅当单元格内容真的发生变化时，才修改颜色 """
        item = self.table.item(row, col)
        text = str(self.df.iat[row, col])
        if item and item.text() != text:  # 确保修改后才变绿
            logger.info(f'Reload data: {text} => {item.data}|{item.text()}')
            item.setForeground(QBrush(QColor("green")))         # 文字变绿色

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
