import sys
import os
import json
import subprocess
import webbrowser
import time
import logging
from datetime import datetime, timedelta
from functools import partial
from collections import defaultdict, Counter
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTreeWidget, QTreeWidgetItem, QLabel, QPushButton, QLineEdit,
    QComboBox, QTextEdit, QFileDialog, QMessageBox, QDialog,
    QFormLayout, QSpinBox, QColorDialog, QMenu, QMenuBar,
    QSplitter, QStackedWidget, QFrame, QInputDialog,
    QTabWidget, QTextBrowser, QScrollArea, QGridLayout, QGroupBox,
    QCheckBox, QSlider, QProgressBar, QListWidget, QListWidgetItem,
    QToolButton, QStatusBar, QToolBar, QDockWidget, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QStyleFactory,
    QDialogButtonBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal, QSize, QRect, QPoint, QSettings, QPropertyAnimation, QEasingCurve, QObject, pyqtSlot
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QAction, QKeySequence, QDesktopServices, QPainter, QBrush, QPen
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel
import re

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

# 日志初始化
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"run_{datetime.now().strftime('%Y-%m-%d')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

class Config:
    """配置管理类"""
    def __init__(self):
        logging.info("初始化配置...")
        self.settings = QSettings("AppLauncher", "AppLauncher")
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        self.theme_list = ["modern_light", "modern_dark"]
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        logging.info("加载配置...")
        # 首先尝试从JSON文件加载
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.categories = data.get("categories", ["信息收集", "漏洞扫描", "漏洞利用", "后渗透", "流量与代理", "编码与解码"])
                    self.tools = data.get("tools", [])
                    self.theme = data.get("theme", "modern_light")
                    self.view_mode = data.get("view_mode", "list")
                    self.recent_tools = data.get("recent_tools", [])
                    self.show_status_bar = data.get("show_status_bar", True)
                    self.auto_refresh = data.get("auto_refresh", True)
                    self.search_history = data.get("search_history", [])
            except Exception as e:
                logging.error(f"从JSON文件加载配置失败: {e}")
                # 如果JSON加载失败，从QSettings加载
                self._load_from_settings()
        else:
            # 如果JSON文件不存在，从QSettings加载
            self._load_from_settings()
        
        logging.info(f"加载的配置: categories={self.categories}, tools={len(self.tools)}")
    
    def _load_from_settings(self):
        """从QSettings加载配置"""
        self.categories = self.settings.value("categories", ["信息收集", "漏洞扫描", "漏洞利用", "后渗透", "流量与代理", "编码与解码"])
        self.tools = self.settings.value("tools", [])
        self.theme = self.settings.value("theme", "modern_light")
        self.view_mode = self.settings.value("view_mode", "list")
        self.recent_tools = self.settings.value("recent_tools", [])
        self.show_status_bar = self.settings.value("show_status_bar", True)
        self.auto_refresh = self.settings.value("auto_refresh", True)
        self.search_history = self.settings.value("search_history", [])
    
    def save_config(self):
        """保存配置"""
        logging.info("保存配置...")
        # 保存到QSettings
        self.settings.setValue("categories", self.categories)
        self.settings.setValue("tools", self.tools)
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("view_mode", self.view_mode)
        self.settings.setValue("recent_tools", self.recent_tools)
        self.settings.setValue("show_status_bar", self.show_status_bar)
        self.settings.setValue("auto_refresh", self.auto_refresh)
        self.settings.setValue("search_history", self.search_history)
        self.settings.sync()
        
        # 同时保存到JSON文件
        try:
            data = {
                "categories": self.categories,
                "tools": self.tools,
                "theme": self.theme,
                "view_mode": self.view_mode,
                "recent_tools": self.recent_tools,
                "show_status_bar": self.show_status_bar,
                "auto_refresh": self.auto_refresh,
                "search_history": self.search_history
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存到JSON文件失败: {e}")
    
    def add_to_recent(self, tool_name):
        """添加到最近使用"""
        if tool_name in self.recent_tools:
            self.recent_tools.remove(tool_name)
        self.recent_tools.insert(0, tool_name)
        # 只保留最近20个
        self.recent_tools = self.recent_tools[:20]
        self.save_config()
    
    def add_to_favorites(self, tool_name):
        """添加到收藏"""
        if tool_name not in self.favorites:
            self.favorites.append(tool_name)
            self.save_config()
    
    def remove_from_favorites(self, tool_name):
        """从收藏中移除"""
        if tool_name in self.favorites:
            self.favorites.remove(tool_name)
        self.save_config()
    
    def add_search_history(self, search_text):
        """添加搜索历史"""
        if search_text in self.search_history:
            self.search_history.remove(search_text)
        self.search_history.insert(0, search_text)
        # 只保留最近10个
        self.search_history = self.search_history[:10]
        self.save_config()

logging.info("定义配置类完成...")

class PipInstallerWorker(QObject):
    """在工作线程中安装Python包"""
    installationStarted = pyqtSignal(str)  # tool_name
    installationProgress = pyqtSignal(str, str)  # tool_name, message
    installationFinished = pyqtSignal(str, bool, str, object)  # tool_name, success, error_msg, tool_object

    @pyqtSlot(object, str)
    def install(self, tool, target):
        """
        安装依赖
        :param tool: 工具对象
        :param target: 'requirements' 或模块名
        """
        self.installationStarted.emit(tool.name)
        tool_dir = os.path.dirname(tool.path)
        
        try:
            if target == 'requirements':
                req_file = os.path.join(tool_dir, 'requirements.txt')
                cmd = ["python", "-m", "pip", "install", "--upgrade", "pip"]
                
                # 首先升级pip
                self.installationProgress.emit(tool.name, "正在检查并升级pip...")
                upgrade_process = subprocess.run(cmd, cwd=tool_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
                if upgrade_process.returncode == 0:
                    self.installationProgress.emit(tool.name, "pip已是最新版本或升级成功。")
                else:
                    self.installationProgress.emit(tool.name, f"pip升级失败，继续尝试安装依赖...")

                # 然后安装requirements
                cmd = ["python", "-m", "pip", "install", "-r", req_file]
                self.installationProgress.emit(tool.name, f"正在从 requirements.txt 安装依赖...")
            else:
                cmd = ["python", "-m", "pip", "install", target]
                self.installationProgress.emit(tool.name, f"正在安装模块: {target}...")

            process = subprocess.Popen(
                cmd,
                cwd=tool_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )

            for line in iter(process.stdout.readline, ''):
                self.installationProgress.emit(tool.name, line.strip())
            
            process.stdout.close()
            return_code = process.wait()

            if return_code == 0:
                self.installationProgress.emit(tool.name, "依赖安装成功!")
                self.installationFinished.emit(tool.name, True, "", tool)
            else:
                error_msg = f"Pip 安装失败，返回码: {return_code}"
                self.installationProgress.emit(tool.name, error_msg)
                self.installationFinished.emit(tool.name, False, error_msg, tool)

        except Exception as e:
            error_msg = f"安装过程中发生错误: {e}"
            self.installationProgress.emit(tool.name, error_msg)
            self.installationFinished.emit(tool.name, False, error_msg, tool)

class Tool:
    """工具类"""
    def __init__(self, name, path, category, subcategory="", tool_type="exe",
                 description="", icon_path=None, color="#000000", launch_count=0, args=""):
        self.name = name
        self.path = path
        self.category = category
        self.subcategory = subcategory
        self.tool_type = tool_type
        self.description = description
        self.icon_path = icon_path
        self.color = color
        self.launch_count = launch_count
        self.last_launch = None
        self.args = args  # 新增启动参数字段
    
    def to_dict(self):
        """转换为字典"""
        return {
            "name": self.name,
            "path": self.path,
            "category": self.category,
            "subcategory": self.subcategory,
            "tool_type": self.tool_type,
            "description": self.description,
            "icon_path": self.icon_path,
            "color": self.color,
            "launch_count": self.launch_count,
            "last_launch": self.last_launch,
            "args": self.args  # 新增启动参数字段
        }
    
    @classmethod
    def from_dict(cls, data):
        """从字典创建工具"""
        # 兼容旧版本的sub_category字段
        subcategory = data.get("subcategory", data.get("sub_category", ""))
        
        return cls(
            data["name"],
            data["path"],
            data["category"],
            subcategory,
            data.get("tool_type", "exe"),
            data.get("description", ""),
            data.get("icon_path"),
            data.get("color", "#000000"),
            data.get("launch_count", 0),
            data.get("args", "")  # 新增启动参数字段
        )

logging.info("定义工具类完成...")

class CyberChefDialog(QDialog):
    """CyberChef 对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CyberChef 编解码")
        self.setMinimumSize(1000, 700)
        layout = QVBoxLayout(self)
        
        # 创建工具栏
        toolbar = QHBoxLayout()
        self.copy_btn = QPushButton("复制结果")
        self.clear_btn = QPushButton("清空")
        toolbar.addWidget(self.copy_btn)
        toolbar.addWidget(self.clear_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # 创建 WebView
        self.webview = QWebEngineView(self)
        # 优化本地路径引用
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cyberchef_index = os.path.join(current_dir, "project", "CyberChef", "index.html")
        if os.path.exists(cyberchef_index):
            url = QUrl.fromLocalFile(cyberchef_index)
            self.webview.setUrl(url)
        else:
            self.webview.setUrl(QUrl("https://btsrk.me/"))
        layout.addWidget(self.webview)
        
        # 连接信号
        self.copy_btn.clicked.connect(self.copy_result)
        self.clear_btn.clicked.connect(self.clear_result)
    
    def copy_result(self):
        """复制结果"""
        self.webview.page().runJavaScript(
            "document.getElementById('output-text').value",
            self.handle_copy_result
        )
    
    def handle_copy_result(self, result):
        """处理复制结果"""
        if result:
            QApplication.clipboard().setText(result)
            QMessageBox.information(self, "提示", "已复制到剪贴板")
    
    def clear_result(self):
        """清空结果"""
        self.webview.page().runJavaScript(
            "document.getElementById('input-text').value = '';"
            "document.getElementById('output-text').value = '';"
        )

class AddToolDialog(QDialog):
    """添加工具对话框"""
    def __init__(self, categories, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowTitle("添加/编辑工具")
        self.setMinimumWidth(600)
        self.categories = categories
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setStyleSheet("background: transparent;")
        
        # Container with shadow
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #fdfdfe;
                border-radius: 12px;
            }
        """)
        main_layout.addWidget(container)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 20)
        container_layout.setSpacing(0)
        
        # --- Custom Title Bar ---
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        title_text = QLabel("添加/编辑工具")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # Draggability
        self.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                self.offset = event.globalPosition().toPoint() - self.pos()
        def mouseMoveEvent(event):
            if self.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                self.move(event.globalPosition().toPoint() - self.offset)
        def mouseReleaseEvent(event):
            self.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        
        container_layout.addWidget(title_bar)
        
        # --- Form Layout ---
        form_layout = QFormLayout()
        form_layout.setContentsMargins(25, 20, 25, 20)
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # --- Widgets ---
        self.name_edit = QLineEdit()
        self.type_combo = QComboBox()
        self.path_edit = QLineEdit()
        self.path_btn = QPushButton("📂")
        self.icon_edit = QLineEdit()
        self.icon_btn = QPushButton("🖼️")
        self.category_combo = QComboBox()
        self.args_edit = QLineEdit()
        self.desc_edit = QTextEdit()
        
        # --- Styling ---
        common_style = """
            QLineEdit, QTextEdit, QComboBox {
                background: #f1f3f5;
                color: #212529;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #764ba2;
                background: #fdfdfe;
            }
            QLabel {
                color: #495057;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton {
                background: #e9ecef;
                color: #495057;
                border-radius: 8px;
                padding: 8px;
                font-weight: bold;
                font-size: 13px;
                border: 1px solid #dee2e6;
            }
            QPushButton:hover { background: #dee2e6; }
        """
        self.setStyleSheet(self.styleSheet() + common_style)

        # Tool Name
        self.name_edit.setPlaceholderText("例如: MyCoolTool")
        form_layout.addRow("工具名称:", self.name_edit)
        
        # Tool Type
        self.type_combo.addItems(["GUI应用", "命令行", "java8图形化", "java11图形化", "java8", "java11", "python", "powershell", "批处理", "网页", "文件夹"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addRow("工具类型:", self.type_combo)
        
        # Tool Path
        path_layout = QHBoxLayout()
        self.path_edit.setPlaceholderText("选择工具路径或输入URL")
        self.path_btn.setFixedSize(40, 40)
        self.path_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.path_btn.setToolTip("浏览文件或文件夹")
        self.path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_btn)
        form_layout.addRow("工具路径:", path_layout)
        
        # Icon Path
        icon_layout = QHBoxLayout()
        self.icon_edit.setPlaceholderText("可选: 选择一个漂亮的图标")
        self.icon_btn.setFixedSize(40, 40)
        self.icon_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.icon_btn.setToolTip("选择图标文件")
        self.icon_btn.clicked.connect(self.browse_icon)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(self.icon_btn)
        form_layout.addRow("图标路径:", icon_layout)
        
        # Category
        self.category_combo.addItems(categories)
        self.category_combo.setEditable(True)
        form_layout.addRow("工具分类:", self.category_combo)
        
        # Arguments
        self.args_edit.setPlaceholderText("可选: 输入启动参数")
        form_layout.addRow("启动参数:", self.args_edit)
        
        # Description
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText("可选: 简单的描述一下这个工具")
        form_layout.addRow("工具描述:", self.desc_edit)
        
        container_layout.addLayout(form_layout)
        
        # --- Buttons ---
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 10, 25, 0)
        buttons_layout.addStretch()

        self.ok_button = QPushButton("✔️ 确定")
        self.cancel_button = QPushButton("❌ 取消")

        self.ok_button.setFixedSize(120, 40)
        self.cancel_button.setFixedSize(120, 40)
        
        self.ok_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        
        self.ok_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
             QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b); }
        """)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background: #e9ecef; color: #495057; border-radius: 20px; font-size: 14px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #dee2e6; }
        """)
        
        buttons_layout.addWidget(self.cancel_button)
        buttons_layout.addWidget(self.ok_button)
        container_layout.addLayout(buttons_layout)

    def on_type_changed(self, type_text):
        """工具类型改变时的处理"""
        if type_text == "网页":
            self.path_edit.setText("http://")
            self.path_btn.setEnabled(False)
            self.args_edit.setEnabled(False)
        elif type_text == "文件夹":
            self.path_edit.setText("")
            self.path_btn.setEnabled(True)
            self.args_edit.setEnabled(False)
        else:
            self.path_btn.setEnabled(True)
            self.args_edit.setEnabled(True)
    
    def browse_path(self):
        """浏览路径"""
        type_text = self.type_combo.currentText()
        
        if type_text == "文件夹":
            path = QFileDialog.getExistingDirectory(self, "选择文件夹")
        elif type_text in ["GUI应用", "命令行", "批处理"]:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择可执行文件", "", 
                "可执行文件 (*.exe *.bat *.cmd);;所有文件 (*)"
            )
        elif type_text in ["java8图形化", "java11图形化", "java8", "java11"]:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择JAR文件", "", 
                "JAR文件 (*.jar);;所有文件 (*)"
            )
        elif type_text == "python":
            path, _ = QFileDialog.getOpenFileName(
                self, "选择Python脚本", "", 
                "Python文件 (*.py);;所有文件 (*)"
            )
        elif type_text == "powershell":
            path, _ = QFileDialog.getOpenFileName(
                self, "选择PowerShell脚本", "", 
                "PowerShell文件 (*.ps1);;所有文件 (*)"
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "选择文件", "", "所有文件 (*)"
            )
        
        if path:
            self.path_edit.setText(path)
    
    def browse_icon(self):
        """浏览图标"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择图标", "", 
            "图标文件 (*.ico *.png *.jpg *.jpeg);;所有文件 (*)"
        )
        if path:
            self.icon_edit.setText(path)
    
    def get_tool_data(self):
        """获取工具数据"""
        type_mapping = {
            "GUI应用": "exe",
            "命令行": "exe", 
            "java8图形化": "java8_gui",
            "java11图形化": "java11_gui",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "批处理": "batch",
            "网页": "url",
            "文件夹": "folder"
        }
        
        return {
            "name": self.name_edit.text().strip(),
            "path": self.path_edit.text().strip(),
            "category": self.category_combo.currentText().strip(),
            "subcategory": "",  # 暂时保留，后续可以通过界面添加
            "tool_type": type_mapping.get(self.type_combo.currentText(), "exe"),
            "description": self.desc_edit.toPlainText().strip(),
            "icon_path": self.icon_edit.text().strip() or None,
            "color": "#000000",
            "launch_count": 0,
            "last_launch": None,
            "args": self.args_edit.text().strip()  # 新增启动参数字段
        }

class SearchWorker(QObject):
    """在工作线程中执行搜索"""
    resultsReady = pyqtSignal(list)

    @pyqtSlot(list, str)
    def search(self, tools, text):
        """搜索工具"""
        if not text:
            self.resultsReady.emit(tools)
            return

        text = text.lower()
        results = []
        for tool_data in tools:
            if (text in tool_data.get('name', '').lower() or
                text in tool_data.get('description', '').lower() or
                text in tool_data.get('category', '').lower()):
                results.append(tool_data)
        
        self.resultsReady.emit(results)

class IconLoaderWorker(QObject):
    """在工作线程中懒加载图标"""
    # 信号发出: 行号, 工具路径 (用于验证), QIcon对象
    iconReady = pyqtSignal(int, str, QIcon)

    @pyqtSlot(int, str, str)
    def load_icon(self, row, tool_path, icon_path):
        """加载图标文件"""
        if icon_path and os.path.exists(icon_path):
            icon = QIcon(icon_path)
            if not icon.isNull():
                self.iconReady.emit(row, tool_path, icon)


class ToolLauncherWorker(QObject):
    """在工作线程中启动工具"""
    toolLaunched = pyqtSignal(str, bool, str)  # 工具名, 成功状态, 错误信息
    installationRequired = pyqtSignal(object, str) # tool, target ('requirements' or module_name)
    
    @pyqtSlot(object, bool)
    def launch_tool(self, tool, dependency_check=True):
        """
        启动工具
        :param tool: 工具对象
        :param dependency_check: 是否进行依赖检查
        """
        try:
            if tool.tool_type == "python" and dependency_check:
                tool_dir = os.path.dirname(tool.path)
                req_file = os.path.join(tool_dir, 'requirements.txt')
                
                if os.path.exists(req_file):
                    self.installationRequired.emit(tool, 'requirements')
                    return

                cmd = ["python", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                
                # 尝试运行一次来检查模块错误
                process = subprocess.run(cmd, cwd=tool_dir, capture_output=True, text=True, encoding='utf-8', errors='replace')
                
                if process.returncode != 0:
                    stderr = process.stderr
                    if "ModuleNotFoundError" in stderr:
                        match = re.search(r"ModuleNotFoundError: No module named '([\w\.]+)'", stderr)
                        if match:
                            module_name = match.group(1)
                            self.installationRequired.emit(tool, module_name)
                            return
                    # 在测试运行时发生了其他错误
                    self.toolLaunched.emit(tool.name, False, stderr or process.stdout)
                    return

            # 如果我们在这里，意味着：
            # 1. 它不是一个python工具
            # 2. 它是一个python工具，并且dependency_check为False（已经安装）
            # 3. 它是一个python工具，dependency_check为True，但没有发现缺少依赖项
            
            if tool.tool_type == "url":
                QDesktopServices.openUrl(QUrl(tool.path))
                self.toolLaunched.emit(tool.name, True, "")
            elif tool.tool_type == "folder":
                QDesktopServices.openUrl(QUrl.fromLocalFile(tool.path))
                self.toolLaunched.emit(tool.name, True, "")
            else:
                tool_dir = os.path.dirname(tool.path)
                cmd = []
                
                if tool.tool_type in ["java8_gui", "java11_gui"]:
                    cmd = ["java", "-jar", tool.path]
                elif tool.tool_type in ["java8", "java11"]:
                    cmd = ["java"]
                elif tool.tool_type == "python":
                    cmd = ["python", tool.path]
                elif tool.tool_type == "powershell":
                    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", tool.path]
                elif tool.tool_type == "batch":
                    cmd = [tool.path]
                else:  # 默认为 exe
                    cmd = [tool.path]
                
                if tool.args:
                    cmd.extend(tool.args.split())
                
                process = subprocess.Popen(cmd, cwd=tool_dir)
                self.toolLaunched.emit(tool.name, True, str(process.pid))
                
        except Exception as e:
            self.toolLaunched.emit(tool.name, False, str(e))

class ConfigSaverWorker(QObject):
    """在工作线程中保存配置"""
    configSaved = pyqtSignal(bool, str)  # 成功状态, 错误信息
    
    @pyqtSlot(dict)
    def save_config(self, config_data):
        """保存配置"""
        try:
            # 保存到QSettings
            settings = QSettings("AppLauncher", "AppLauncher")
            for key, value in config_data.items():
                settings.setValue(key, value)
            settings.sync()
            
            # 保存到JSON文件
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            self.configSaved.emit(True, "")
        except Exception as e:
            self.configSaved.emit(False, str(e))

class ProcessMonitorWorker(QObject):
    """监控已启动的进程"""
    processStatusChanged = pyqtSignal(str, str, bool)  # 工具名, 进程ID, 是否运行
    
    def __init__(self):
        super().__init__()
        self.monitored_processes = {}  # {tool_name: pid}
        self.running = True
    
    @pyqtSlot()
    def start_monitoring(self):
        """开始监控进程"""
        while self.running:
            try:
                for tool_name, pid in list(self.monitored_processes.items()):
                    try:
                        # 检查进程是否还在运行
                        process = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                               capture_output=True, text=True)
                        is_running = str(pid) in process.stdout
                        self.processStatusChanged.emit(tool_name, str(pid), is_running)
                        
                        if not is_running:
                            # 进程已结束，从监控列表中移除
                            del self.monitored_processes[tool_name]
                    except:
                        # 进程可能已经结束
                        del self.monitored_processes[tool_name]
                
                time.sleep(2)  # 每2秒检查一次
            except:
                break
    
    def add_process(self, tool_name, pid):
        """添加进程到监控列表"""
        self.monitored_processes[tool_name] = pid
    
    def stop_monitoring(self):
        """停止监控"""
        self.running = False

class CacheManager:
    """缓存管理器"""
    def __init__(self, max_size=100):
        self.cache = {}
        self.max_size = max_size
        self.access_order = []
    
    def get(self, key):
        """获取缓存项"""
        if key in self.cache:
            # 更新访问顺序
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        """设置缓存项"""
        if key in self.cache:
            # 更新现有项
            self.cache[key] = value
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
        else:
            # 添加新项
            if len(self.cache) >= self.max_size:
                # 移除最久未访问的项
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = value
            self.access_order.append(key)
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_order.clear()

class ClipboardBridge(QObject):
    """提供给JS调用的剪贴板桥接"""
    @pyqtSlot(str)
    def copy(self, text):
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            logging.info(f"通过桥接复制到剪贴板: {text[:50]}...")

class MainWindow(QMainWindow):
    """主窗口"""
    # 为工作线程添加信号
    startSearch = pyqtSignal(list, str)
    startIconLoad = pyqtSignal(int, str, str)
    startToolLaunch = pyqtSignal(object, bool)
    startPipInstall = pyqtSignal(object, str)
    startConfigSave = pyqtSignal(dict)

    def __init__(self):
        logging.info("初始化主窗口...")
        super().__init__()
        self.config = Config()
        self.cache_manager = CacheManager()
        self.init_workers()
        self.init_ui()
        self.load_data()
        logging.info("主窗口初始化完成")

    def init_workers(self):
        """初始化后台工作线程"""
        # --- 搜索线程 ---
        self.search_thread = QThread()
        self.search_worker = SearchWorker()
        self.search_worker.moveToThread(self.search_thread)
        self.startSearch.connect(self.search_worker.search)
        self.search_worker.resultsReady.connect(self.handle_search_results)
        self.search_thread.start()
        
        # --- 图标加载线程 ---
        self.icon_loader_thread = QThread()
        self.icon_loader_worker = IconLoaderWorker()
        self.icon_loader_worker.moveToThread(self.icon_loader_thread)
        self.startIconLoad.connect(self.icon_loader_worker.load_icon)
        self.icon_loader_worker.iconReady.connect(self.set_tool_icon)
        self.icon_loader_thread.start()
        
        # --- 工具启动线程 ---
        self.tool_launcher_thread = QThread()
        self.tool_launcher_worker = ToolLauncherWorker()
        self.tool_launcher_worker.moveToThread(self.tool_launcher_thread)
        self.startToolLaunch.connect(self.tool_launcher_worker.launch_tool)
        self.tool_launcher_worker.toolLaunched.connect(self.handle_tool_launched)
        self.tool_launcher_worker.installationRequired.connect(self.handle_installation_required)
        self.tool_launcher_thread.start()
        
        # --- Pip安装线程 ---
        self.pip_installer_thread = QThread()
        self.pip_installer_worker = PipInstallerWorker()
        self.pip_installer_worker.moveToThread(self.pip_installer_thread)
        self.startPipInstall.connect(self.pip_installer_worker.install)
        self.pip_installer_worker.installationStarted.connect(self.handle_installation_started)
        self.pip_installer_worker.installationProgress.connect(self.handle_installation_progress)
        self.pip_installer_worker.installationFinished.connect(self.handle_installation_finished)
        self.pip_installer_thread.start()
        
        # --- 配置保存线程 ---
        self.config_saver_thread = QThread()
        self.config_saver_worker = ConfigSaverWorker()
        self.config_saver_worker.moveToThread(self.config_saver_thread)
        self.startConfigSave.connect(self.config_saver_worker.save_config)
        self.config_saver_worker.configSaved.connect(self.handle_config_saved)
        self.config_saver_thread.start()
        
        # --- 进程监控线程 ---
        self.process_monitor_thread = QThread()
        self.process_monitor_worker = ProcessMonitorWorker()
        self.process_monitor_worker.moveToThread(self.process_monitor_thread)
        self.process_monitor_worker.processStatusChanged.connect(self.handle_process_status)
        self.process_monitor_thread.started.connect(self.process_monitor_worker.start_monitoring)
        self.process_monitor_thread.start()
        
        # --- 搜索防抖计时器 ---
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300) # 300ms延迟
        self.search_timer.timeout.connect(self.trigger_search)
        
        # --- 配置保存防抖计时器 ---
        self.config_save_timer = QTimer(self)
        self.config_save_timer.setSingleShot(True)
        self.config_save_timer.setInterval(500) # 500ms延迟
        self.config_save_timer.timeout.connect(self.trigger_config_save)
        
        # --- 内存优化定时器 ---
        self.memory_optimize_timer = QTimer(self)
        self.memory_optimize_timer.setInterval(30000) # 每30秒优化一次内存
        self.memory_optimize_timer.timeout.connect(self.optimize_memory)
        self.memory_optimize_timer.start()
        
        logging.info("后台工作线程初始化完成")
    
    def handle_tool_launched(self, tool_name, success, result):
        """处理工具启动结果"""
        if success:
            if result.isdigit():  # 返回的是进程ID
                self.process_monitor_worker.add_process(tool_name, int(result))
            self.status_label.setText(f"✅ 已启动: {tool_name}")
            # 更新启动统计
            self.update_tool_stats(tool_name)
        else:
            QMessageBox.critical(self, "启动失败", f"启动 {tool_name} 失败: {result}")
            self.status_label.setText(f"❌ 启动失败: {tool_name}")
    
    def handle_config_saved(self, success, error_msg):
        """处理配置保存结果"""
        if not success:
            logging.error(f"配置保存失败: {error_msg}")
            QMessageBox.warning(self, "配置保存失败", f"配置保存失败: {error_msg}")
    
    def handle_process_status(self, tool_name, pid, is_running):
        """处理进程状态变化"""
        if not is_running:
            logging.info(f"进程已结束: {tool_name} (PID: {pid})")
    
    def update_tool_stats(self, tool_name):
        """更新工具启动统计"""
        for tool_dict in self.config.tools:
            if tool_dict.get('name') == tool_name:
                tool_dict['launch_count'] = tool_dict.get('launch_count', 0) + 1
                tool_dict['last_launch'] = datetime.now().isoformat()
                break
        
        # 添加到最近使用列表
        self.config.add_to_recent(tool_name)
        
        # 触发配置保存
        self.schedule_config_save()
        
        # 更新UI
        self.update_status_stats()
    
    def schedule_config_save(self):
        """调度配置保存（防抖）"""
        self.config_save_timer.start()
    
    def trigger_config_save(self):
        """触发配置保存"""
        config_data = {
            "categories": self.config.categories,
            "tools": self.config.tools,
            "theme": self.config.theme,
            "view_mode": self.config.view_mode,
            "recent_tools": self.config.recent_tools,
            "show_status_bar": self.config.show_status_bar,
            "auto_refresh": self.config.auto_refresh,
            "search_history": self.config.search_history
        }
        self.startConfigSave.emit(config_data)
    
    def init_ui(self):
        """初始化界面（重构为左侧固定导航栏）"""
        logging.info("开始初始化界面...")
        self.setWindowTitle("AppLauncher - 智能程序启动与编码助手")
        self.setMinimumSize(1200, 800)

        # 分页参数
        self.tools_per_page = 20
        self.current_page = 1
        self.total_pages = 1
        self.current_tools = []  # 当前显示的工具列表

        # 创建主窗口部件
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        # 创建主布局
        layout = QHBoxLayout(main_widget)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setChildrenCollapsible(False)
        layout.addWidget(splitter)

        # 左侧导航栏
        nav_panel = QWidget()
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(5, 5, 5, 5)
        nav_layout.setSpacing(10)
        # 固定导航按钮
        self.btn_safe_tools = QPushButton("安全工具")
        self.btn_safe_tools.setCheckable(True)
        self.btn_safe_tools.setChecked(True)
        self.btn_safe_tools.clicked.connect(lambda: self.switch_nav('safe'))
        self.btn_code_tools = QPushButton("编码与解码")
        self.btn_code_tools.setCheckable(True)
        self.btn_code_tools.setChecked(False)
        self.btn_code_tools.clicked.connect(lambda: self.switch_nav('code'))
        self.btn_assist_tools = QPushButton("辅助工具")
        self.btn_assist_tools.setCheckable(True)
        self.btn_assist_tools.setChecked(False)
        self.btn_assist_tools.clicked.connect(lambda: self.switch_nav('assist'))
        nav_layout.addWidget(self.btn_safe_tools)
        nav_layout.addWidget(self.btn_code_tools)
        nav_layout.addWidget(self.btn_assist_tools)
        nav_layout.addStretch()
        splitter.addWidget(nav_panel)

        # 右侧内容区（后续填充树形大纲和工具列表/CyberChef/辅助工具）
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(0, 0, 0, 0)
        self.right_layout.setSpacing(0)
        splitter.addWidget(self.right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        # 初始化导航状态
        self.switch_nav('safe')

        # 创建菜单栏
        self.create_menu()
        # 创建状态栏
        self.create_status_bar()
        # 设置样式
        self.apply_theme()
        logging.info("界面初始化完成")

    def switch_nav(self, nav):
        """切换导航（safe/code/assist）"""
        # 清空右侧内容区
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        if nav == 'safe':
            self.btn_safe_tools.setChecked(True)
            self.btn_code_tools.setChecked(False)
            self.btn_assist_tools.setChecked(False)
            # --- 安全工具树形大纲和工具列表 ---
            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            # 树形大纲
            self.outline_tree = QTreeWidget()
            self.outline_tree.setHeaderLabel('工具分类大纲')
            self.outline_tree.setMinimumWidth(220)
            self.outline_tree.setMaximumWidth(320)
            self.outline_tree.itemClicked.connect(self.on_outline_clicked)
            container_layout.addWidget(self.outline_tree)
            # 工具列表
            self.tools_list = QListWidget()
            self.tools_list.setViewMode(QListWidget.ViewMode.ListMode)
            self.tools_list.setSpacing(4)
            self.tools_list.setResizeMode(QListWidget.ResizeMode.Adjust)
            self.tools_list.setMovement(QListWidget.Movement.Static)
            self.tools_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            self.tools_list.customContextMenuRequested.connect(self.show_context_menu)
            self.tools_list.itemDoubleClicked.connect(self.launch_tool)
            container_layout.addWidget(self.tools_list)
            self.right_layout.addWidget(container)
            # 搜索框
            self.search_input = QLineEdit()
            self.search_input.setPlaceholderText("搜索工具...")
            self.search_input.textChanged.connect(self.on_search_text_changed)
            self.right_layout.insertWidget(0, self.search_input)
            # 刷新树形大纲和工具列表
            self.refresh_outline_and_tools()
        elif nav == 'code':
            self.btn_safe_tools.setChecked(False)
            self.btn_code_tools.setChecked(True)
            self.btn_assist_tools.setChecked(False)
            # --- 编码与解码页面 ---
            # 复用原有CyberChef页面逻辑
            self.show_cyberchef()
        elif nav == 'assist':
            self.btn_safe_tools.setChecked(False)
            self.btn_code_tools.setChecked(False)
            self.btn_assist_tools.setChecked(True)
            # --- 辅助工具页面 ---
            assist_container = QWidget()
            assist_layout = QVBoxLayout(assist_container)
            assist_layout.setContentsMargins(0, 0, 0, 0)
            assist_layout.setSpacing(0)
            # 顶部tab按钮区
            self.assist_tab_bar = QHBoxLayout()
            self.assist_tab_bar.setContentsMargins(16, 16, 16, 0)
            self.assist_tab_bar.setSpacing(12)
            self.assist_tabs = []
            # 目前只加一个tab，后续可扩展
            self.btn_shellgen = QPushButton("反弹shell生成")
            self.btn_shellgen.setCheckable(True)
            self.btn_shellgen.setChecked(True)
            self.btn_shellgen.clicked.connect(lambda: self.switch_assist_tab('shellgen'))
            self.assist_tab_bar.addWidget(self.btn_shellgen)
            self.assist_tabs.append(self.btn_shellgen)
            # 新增Java命令编码Tab
            self.btn_java_encode = QPushButton("Java_Exec_Encode")
            self.btn_java_encode.setCheckable(True)
            self.btn_java_encode.setChecked(False)
            self.btn_java_encode.clicked.connect(lambda: self.switch_assist_tab('java_encode'))
            self.assist_tab_bar.addWidget(self.btn_java_encode)
            self.assist_tabs.append(self.btn_java_encode)
            self.assist_tab_bar.addStretch()
            assist_layout.addLayout(self.assist_tab_bar)
            # 下方内容区
            self.assist_content = QStackedWidget()
            # 反弹shell生成页面
            self.shellgen_webview = QWebEngineView()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            shellgen_path = os.path.join(current_dir, "project", "reverse-shell", "index.html")
            if os.path.exists(shellgen_path):
                url = QUrl.fromLocalFile(shellgen_path)
                self.shellgen_webview.setUrl(url)
            else:
                self.shellgen_webview.setUrl(QUrl("https://btsrk.me/"))
            self.assist_content.addWidget(self.shellgen_webview)
            # Java命令编码页面
            self.java_encode_webview = QWebEngineView()
            
            # 创建JS-Python桥接，解决内嵌页面剪贴板权限问题
            self.clipboard_bridge = ClipboardBridge()
            channel = QWebChannel(self.java_encode_webview.page())
            self.java_encode_webview.page().setWebChannel(channel)
            channel.registerObject("qt_bridge", self.clipboard_bridge)
            
            java_encode_path = os.path.join(current_dir, "project", "java-encode", "index.html")
            if os.path.exists(java_encode_path):
                url = QUrl.fromLocalFile(java_encode_path)
                self.java_encode_webview.setUrl(url)
            else:
                self.java_encode_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))
            self.assist_content.addWidget(self.java_encode_webview)
            assist_layout.addWidget(self.assist_content)
            self.right_layout.addWidget(assist_container)
            # 便于后续扩展tab
            self.current_assist_tab = 'java_encode'
        else:
            self.btn_safe_tools.setChecked(False)
            self.btn_code_tools.setChecked(False)
            self.btn_assist_tools.setChecked(False)

    def on_search_text_changed(self, text):
        """当搜索框文本变化时，启动/重置防抖计时器"""
        self.search_timer.start()

    def trigger_search(self):
        """计时器结束后，触发后台搜索"""
        search_text = self.search_input.text().strip()
        
        # 如果搜索框为空，则显示当前分类的工具，而不是所有工具
        if not search_text:
            current_item = self.outline_tree.currentItem()
            if current_item:
                self.on_outline_clicked(current_item)
            else:
                self.update_tools_list_for_outline() # 如果没有选中分类，显示所有
            return

        all_tools_data = self.config.tools
        self.startSearch.emit(all_tools_data, search_text)

    def handle_search_results(self, results):
        """用后台线程的搜索结果更新UI"""
        tools_to_show = [Tool.from_dict(r) for r in results]
        self.show_tools_list(tools_to_show)

    def refresh_outline_and_tools(self):
        """根据所有工具的分类字段动态生成树形大纲（支持多级），并显示所有工具"""
        self.outline_tree.clear()
        # 构建支持多级的分类树结构
        tree_dict = {}
        for t in self.config.tools:
            # 使用strip()去除前后空格，并过滤掉空部分
            parts = [p.strip() for p in t.get('category', '').split('/') if p.strip()]
            if not parts:
                continue
            
            current_level = tree_dict
            for part in parts:
                current_level = current_level.setdefault(part, {})

        # 递归函数，用于将字典树添加到QTreeWidget
        def add_items_to_tree(parent_item, children):
            for name, sub_children in sorted(children.items()):
                child_item = QTreeWidgetItem([name])
                parent_item.addChild(child_item)
                if sub_children:
                    add_items_to_tree(child_item, sub_children)

        # 遍历顶层分类并添加到树中
        for name, children in sorted(tree_dict.items()):
            top_level_item = QTreeWidgetItem([name])
            self.outline_tree.addTopLevelItem(top_level_item)
            if children:
                add_items_to_tree(top_level_item, children)
        
        self.outline_tree.expandAll()
        
        # 默认显示所有工具
        self.update_tools_list_for_outline()

    def on_outline_clicked(self, item):
        """点击树形大纲分类，显示对应工具（支持多级）"""
        # 获取完整分类路径
        path = []
        cur = item
        while cur:
            path.insert(0, cur.text(0))
            cur = cur.parent()
        
        # 拼接成前缀，用于匹配
        cat_prefix = '/'.join(path)
        
        # 筛选出所有分类以该前缀开头的工具
        tools = [Tool.from_dict(t) for t in self.config.tools if t.get('category', '').startswith(cat_prefix)]
        
        self.show_tools_list(tools)

    def update_tools_list_for_outline(self):
        """显示所有工具（或可根据需要显示默认分类）"""
        tools = [Tool.from_dict(t) for t in self.config.tools]
        self.show_tools_list(tools)

    def show_tools_list(self, tools):
        self.tools_list.clear()
        self.tools_list.setIconSize(QSize(40, 40))  # 图标更大
        
        # 使用缓存优化性能
        cache_key = f"tools_list_{len(tools)}_{hash(str(tools))}"
        cached_data = self.cache_manager.get(cache_key)
        
        for i, tool in enumerate(tools):
            item = QListWidgetItem()
            
            # 存储工具对象和路径，用于后续操作和验证
            item.setData(Qt.ItemDataRole.UserRole, tool)
            
            # 设置通用样式和提示
            font = QFont("Microsoft YaHei", 12, QFont.Weight.Bold)
            item.setFont(font)
            item.setSizeHint(QSize(0, 54))
            desc = tool.description or ""
            tooltip = f"<b>{tool.name}</b><br>类型: {tool.tool_type}<br>路径: {tool.path}"
            if desc:
                tooltip += f"<br>描述: {desc}"
            item.setToolTip(tooltip)
            
            # 懒加载图标（使用缓存优化）
            if tool.icon_path:
                item.setText(tool.name)
                # 检查缓存中是否有图标
                icon_cache_key = f"icon_{hash(tool.icon_path)}"
                cached_icon = self.cache_manager.get(icon_cache_key)
                
                if cached_icon:
                    item.setIcon(cached_icon)
                else:
                    # 使用一个标准图标作为占位符
                    placeholder_icon = self.style().standardIcon(QApplication.style().StandardPixmap.SP_DriveNetIcon)
                    item.setIcon(placeholder_icon)
                    # 触发后台加载
                    self.startIconLoad.emit(i, tool.path, tool.icon_path)
            else:
                # 如果没有自定义图标，使用emoji
                emoji = self._get_tool_icon(tool)
                item.setText(f"{emoji}  {tool.name}")
                item.setIcon(QIcon()) # 明确设置空图标以保证对齐

            self.tools_list.addItem(item)
            
        # 美化列表整体样式
        self.tools_list.setStyleSheet('''
            QListWidget {
                background: #fff;
                border: none;
                outline: none;
                padding: 8px;
            }
            QListWidget::item {
                background: #f8fafd;
                border: 1px solid #e1e8ed;
                border-radius: 10px;
                margin: 6px 0;
                min-height: 54px;
                padding-left: 10px;
                font-size: 15px;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                border: 1.5px solid #1da1f2;
            }
            QListWidget::item:hover {
                background: #f0f6ff;
                border: 1.5px solid #1da1f2;
            }
        ''')
    
    def set_tool_icon(self, row, tool_path, icon):
        """Slot to set a lazy-loaded icon on a list item."""
        if row >= self.tools_list.count():
            return  # 行越界，列表可能已更新
            
        item = self.tools_list.item(row)
        if item:
            # 验证item是否仍然是当初请求图标的那个工具
            item_tool = item.data(Qt.ItemDataRole.UserRole)
            if item_tool and item_tool.path == tool_path:
                item.setIcon(icon)
                # 缓存图标以提高性能
                if item_tool.icon_path:
                    icon_cache_key = f"icon_{hash(item_tool.icon_path)}"
                    self.cache_manager.set(icon_cache_key, icon)
    
    def optimize_memory(self):
        """优化内存使用"""
        # 清理缓存中的旧条目
        if len(self.cache_manager.cache) > self.cache_manager.max_size * 0.8:
            # 当缓存使用超过80%时，清理最旧的20%条目
            items_to_remove = int(self.cache_manager.max_size * 0.2)
            for _ in range(items_to_remove):
                if self.cache_manager.access_order:
                    oldest_key = self.cache_manager.access_order.pop(0)
                    if oldest_key in self.cache_manager.cache:
                        del self.cache_manager.cache[oldest_key]
        
        # 强制垃圾回收
        import gc
        gc.collect()
        
        logging.info("内存优化完成")

    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_tool_action = QAction("添加工具", self)
        add_tool_action.setShortcut(QKeySequence("Ctrl+N"))
        add_tool_action.triggered.connect(self.add_tool)
        file_menu.addAction(add_tool_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("导出配置", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self.export_config)
        file_menu.addAction(export_action)
        
        import_action = QAction("导入配置", self)
        import_action.setShortcut(QKeySequence("Ctrl+I"))
        import_action.triggered.connect(self.import_config)
        file_menu.addAction(import_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("退出", self)
        exit_action.setShortcut(QKeySequence("Ctrl+Q"))
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 主题菜单
        theme_menu = menubar.addMenu("主题")
        
        # 现代化主题
        modern_light_action = QAction("🌞 现代浅色", self)
        modern_light_action.triggered.connect(partial(self.set_theme, "modern_light"))
        theme_menu.addAction(modern_light_action)
        
        modern_dark_action = QAction("🌙 现代深色", self)
        modern_dark_action.triggered.connect(partial(self.set_theme, "modern_dark"))
        theme_menu.addAction(modern_dark_action)
        
        dracula_action = QAction("🧛 Dracula", self)
        dracula_action.triggered.connect(partial(self.set_theme, "dracula"))
        theme_menu.addAction(dracula_action)
        
        solarized_light_action = QAction("☀️ Solarized Light", self)
        solarized_light_action.triggered.connect(partial(self.set_theme, "solarized_light"))
        theme_menu.addAction(solarized_light_action)
        
        solarized_dark_action = QAction("🌑 Solarized Dark", self)
        solarized_dark_action.triggered.connect(partial(self.set_theme, "solarized_dark"))
        theme_menu.addAction(solarized_dark_action)
        
        nord_action = QAction("❄️ Nord", self)
        nord_action.triggered.connect(partial(self.set_theme, "nord"))
        theme_menu.addAction(nord_action)
        
        theme_menu.addSeparator()
        
        # 统计菜单
        stats_menu = menubar.addMenu("统计")
        
        # 总工具数
        total_tools_action = QAction("总工具数", self)
        total_tools_action.triggered.connect(self.show_total_tools)
        stats_menu.addAction(total_tools_action)
        
        # 最近启动的工具
        recent_tools_action = QAction("最近启动的工具", self)
        recent_tools_action.triggered.connect(self.show_recent_tools)
        stats_menu.addAction(recent_tools_action)
        
        stats_menu.addSeparator()
        
        # 刷新统计
        refresh_stats_action = QAction("刷新统计", self)
        refresh_stats_action.setShortcut(QKeySequence("F5"))
        refresh_stats_action.triggered.connect(self.refresh_data)
        stats_menu.addAction(refresh_stats_action)
        
        # 直接添加关于菜单项到菜单栏
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        menubar.addAction(about_action)
        
        # 添加快捷键
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # 搜索快捷键
        search_shortcut = QAction(self)
        search_shortcut.setShortcut(QKeySequence("Ctrl+F"))
        search_shortcut.triggered.connect(self.focus_search)
        self.addAction(search_shortcut)
        
        # 刷新快捷键
        refresh_shortcut = QAction(self)
        refresh_shortcut.setShortcut(QKeySequence("F5"))
        refresh_shortcut.triggered.connect(self.refresh_data)
        self.addAction(refresh_shortcut)
        
        # 全屏快捷键
        fullscreen_shortcut = QAction(self)
        fullscreen_shortcut.setShortcut(QKeySequence("F11"))
        fullscreen_shortcut.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_shortcut)
    
    def focus_search(self):
        """聚焦到搜索框"""
        self.search_input.setFocus()
        self.search_input.selectAll()
    
    def refresh_data(self):
        """刷新数据（移除category_tree相关逻辑）"""
        self.update_status_stats()
        # 只刷新工具大纲和工具列表
        self.refresh_outline_and_tools()
        self.status_label.setText("数据已刷新")
    
    def toggle_fullscreen(self):
        """切换全屏模式"""
        if self.isFullScreen():
            self.showNormal()
            self.status_label.setText("退出全屏模式")
        else:
            self.showFullScreen()
            self.status_label.setText("进入全屏模式")
    
    def show_about(self):
        """显示关于对话框（现代化UI）"""
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setMinimumSize(450, 550)

        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Container with shadow
        container = QWidget()
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            QWidget {
                background: #ffffff;
                border-radius: 12px;
            }
        """)
        main_layout.addWidget(container)
        
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # --- Custom Title Bar ---
        title_bar = QWidget()
        title_bar.setFixedHeight(50)
        title_bar.setStyleSheet("""
            QWidget {
                background: #2d3436;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(15, 0, 15, 0)
        
        title_icon = QLabel("💡")
        title_icon.setStyleSheet("font-size: 20px; color: white; background: transparent;")
        title_layout.addWidget(title_icon)
        
        title_text = QLabel("关于 AppLauncher")
        title_text.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent; margin-left: 5px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.1); border: none; border-radius: 15px; color: white; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: rgba(255, 255, 255, 0.2); }
            QPushButton:pressed { background: rgba(0, 0, 0, 0.1); }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        
        # Draggability
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()
        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)
        def mouseReleaseEvent(event):
            dialog.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent

        container_layout.addWidget(title_bar)
        
        # --- Content ---
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(15)

        title = QLabel("关于 AppLauncher")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1da1f2; margin-bottom: 10px;")
        content_layout.addWidget(title)
        
        about_text = QTextBrowser()
        about_text.setOpenExternalLinks(True)
        about_text.setStyleSheet("""
            QTextBrowser {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #34495e;
            }
        """)
        about_text.setHtml('''
        <div style="line-height:1.7;">
        <b>AppLauncher - 智能程序启动与编码助手</b><br><br>
        <b>版本：</b>1.0<br>
        <b>功能：</b>工具管理、分类组织、快速启动、CyberChef集成<br><br>
        <b>支持多种工具类型：</b><br>
        • GUI应用、命令行工具<br>
        • Java、Python、PowerShell脚本<br>
        • 网页链接、文件夹、批处理文件<br><br>
        <b>快捷键：</b><br>
        • Ctrl+N：添加工具<br>
        • Ctrl+F：搜索<br>
        • F5：刷新<br>
        • F11：全屏切换<br><br>
        <b>开发者：</b><br>
        • GitHub：<a href="https://github.com/z50n6" style="color:#1da1f2;text-decoration:none; font-weight:bold;">z50n6</a>
        </div>
        ''')
        content_layout.addWidget(about_text)
        
        btn = QPushButton("关闭")
        btn.setMinimumSize(120, 40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1da1f2, stop:1 #0d8bd9);
                color: white;
                border-radius: 20px;
                font-size: 15px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d8bd9, stop:1 #1da1f2);
            }
        """)
        btn.clicked.connect(dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(btn)
        button_layout.addStretch()
        content_layout.addLayout(button_layout)

        container_layout.addLayout(content_layout)
        
        dialog.exec()
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态信息标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label, 1) # 添加拉伸因子
        
        # 安装进度条
        self.install_progress_bar = QProgressBar()
        self.install_progress_bar.setVisible(False)
        self.install_progress_bar.setFixedWidth(200)
        self.status_bar.addPermanentWidget(self.install_progress_bar)
        
        # 工具统计信息
        self.stats_label = QLabel("")
        self.status_bar.addPermanentWidget(self.stats_label)
        
        # 更新统计信息
        self.update_status_stats()
    
    def update_status_stats(self):
        """更新状态栏统计信息"""
        total_tools = len(self.config.tools)
        total_categories = len(self.config.categories)
        total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
        
        stats_text = f"工具: {total_tools} | 分类: {total_categories} | 启动: {total_launches}"
        self.stats_label.setText(stats_text)
    
    def load_data(self):
        """加载数据（已不再需要分类树）"""
        pass
    
    def update_category_tree(self):
        """已废弃：分类树相关逻辑移除"""
        pass
    
    def update_tools_list(self, category=None):
        """更新工具列表，支持分页和全部工具展示"""
        self.tools_list.clear()
        
        # 获取所有需要展示的工具
        if category:
            tools = [Tool.from_dict(t) for t in self.config.tools if t.get('category') == category]
        else:
            tools = [Tool.from_dict(t) for t in self.config.tools]
        
        self.current_tools = tools
        
        # 分页计算
        total = len(tools)
        self.total_pages = max(1, (total + self.tools_per_page - 1) // self.tools_per_page)
        self.current_page = min(self.current_page, self.total_pages)
        start = (self.current_page - 1) * self.tools_per_page
        end = start + self.tools_per_page
        page_tools = tools[start:end]
        
        # 显示当前页的工具
        for tool in page_tools:
            self._create_tool_item(tool)
        
        # 更新分页控件
        self.page_label.setText(f"第 {self.current_page} / {self.total_pages} 页   共 {total} 个工具")
        self.prev_btn.setEnabled(self.current_page > 1)
        self.next_btn.setEnabled(self.current_page < self.total_pages)
        
        # 确保显示工具列表页面
        self.right_stack.setCurrentWidget(self.tools_page)
    
    def _create_tool_item(self, tool):
        """创建工具项"""
        tool_item = QListWidgetItem()
        
        # 设置工具名称和图标
        if tool.icon_path and os.path.exists(tool.icon_path):
            # 使用配置的图标
            icon = QIcon(tool.icon_path)
            tool_item.setIcon(icon)
            tool_item.setText(tool.name)
        else:
            # 使用默认图标
            default_icon = self._get_tool_icon(tool)
            tool_item.setText(f"{default_icon} {tool.name}")
        
        # 设置字体
        font = QFont("Microsoft YaHei", 11, QFont.Weight.Normal)
        tool_item.setFont(font)
        
        # 设置数据
        tool_item.setData(Qt.ItemDataRole.UserRole, tool)
        
        # 设置工具提示
        tooltip_text = f"工具名称: {tool.name}\n"
        tooltip_text += f"工具类型: {tool.tool_type}\n"
        tooltip_text += f"启动次数: {tool.launch_count}\n"
        if tool.description:
            tooltip_text += f"描述: {tool.description}\n"
        if tool.last_launch:
            tooltip_text += f"最后启动: {tool.last_launch[:19]}"
        
        tool_item.setToolTip(tooltip_text)
        
        # 添加到列表
        self.tools_list.addItem(tool_item)
    
    def _get_tool_icon(self, tool):
        """根据工具类型获取图标"""
        icon_map = {
            "exe": "⚙️",
            "java8_gui": "☕",
            "java11_gui": "☕",
            "java8": "👨‍💻",
            "java11": "👨‍💻",
            "python": "🐍",
            "powershell": "💻",
            "batch": "📜",
            "url": "🌐",
            "folder": "📁",
            "placeholder": "📂"
        }
        return icon_map.get(tool.tool_type, "🚀")
    
    def _get_tool_status(self, tool):
        """获取工具状态"""
        if tool.tool_type == "placeholder":
            return "空分类", QColor(150, 150, 150)
        
        # 检查工具路径是否存在
        if tool.tool_type in ["url", "folder"]:
            return "可用", QColor(0, 150, 0)
        elif tool.tool_type in ["java8", "java11", "java8_gui", "java11_gui"]:
            # 检查Java环境
            try:
                subprocess.run(["java", "-version"], capture_output=True, check=True)
                return "可用", QColor(0, 150, 0)
            except:
                return "需Java环境", QColor(255, 100, 0)
        elif tool.tool_type == "python":
            # 检查Python环境
            try:
                subprocess.run(["python", "--version"], capture_output=True, check=True)
                return "可用", QColor(0, 150, 0)
            except:
                return "需Python环境", QColor(255, 100, 0)
        elif tool.tool_type == "powershell":
            return "可用", QColor(0, 150, 0)
        else:
            # 检查文件是否存在
            if os.path.exists(tool.path):
                return "可用", QColor(0, 150, 0)
            else:
                return "文件不存在", QColor(255, 0, 0)
    
    def on_category_clicked(self, item):
        """分类点击处理"""
        category_name = item.text(0)
        logging.info(f"点击分类: {category_name}")
        if category_name == "编码与解码":
            logging.info("切换到CyberChef页面")
            self.right_stack.setCurrentWidget(self.cyberchef_page)
            self.cyberchef_webview.setFocus()
        else:
            self.current_page = 1
            self.update_tools_list(category_name)
            self.right_stack.setCurrentWidget(self.tools_page)
            # 如果该分类下没有工具，显示提示
            if not self.current_tools:
                empty_item = QListWidgetItem("📂 此分类暂无工具")
                empty_item.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Normal))
                empty_item.setForeground(QColor(150, 150, 150))
                empty_item.setToolTip("点击右键菜单可以添加工具到此分类")
                self.tools_list.addItem(empty_item)
    
    def on_tool_item_clicked(self, item):
        """工具项点击处理"""
        # 如果点击的是工具项，则启动工具
        tool = item.data(Qt.ItemDataRole.UserRole)
        if tool:
            self.launch_tool(item)
    
    def _launch_and_update_stats(self, tool_to_launch):
        """统一处理工具启动、统计更新和配置保存（已废弃，使用新的后台启动机制）"""
        # 使用新的后台启动机制
        self.startToolLaunch.emit(tool_to_launch)
        return True

    def launch_tool(self, item):
        """启动工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        if tool.tool_type == "placeholder":
            QMessageBox.information(self, "提示", "这是一个空分类的占位符，请添加实际工具到此分类。")
            return
            
        # 使用新的后台启动机制
        self.startToolLaunch.emit(tool, True)
    
    def edit_tool(self, item):
        """编辑工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        dialog = AddToolDialog(self.config.categories, self)
        
        # 设置当前值
        type_mapping_reverse = {
            "exe": "GUI应用",
            "java8_gui": "java8图形化",
            "java11_gui": "java11图形化",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "batch": "批处理",
            "url": "网页",
            "folder": "文件夹"
        }
        
        dialog.name_edit.setText(tool.name)
        dialog.path_edit.setText(tool.path)
        dialog.category_combo.setCurrentText(tool.category)
        dialog.args_edit.setText(tool.args)
        dialog.icon_edit.setText(tool.icon_path or "")
        dialog.desc_edit.setPlainText(tool.description)
        
        # 设置工具类型
        tool_type = type_mapping_reverse.get(tool.tool_type, "GUI应用")
        dialog.type_combo.setCurrentText(tool_type)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["launch_count"] = tool.launch_count
            tool_data["last_launch"] = tool.last_launch
            
            # 检查是否添加了新分类
            new_category = tool_data["category"]
            if new_category not in self.config.categories:
                self.config.categories.append(new_category)
                logging.info(f"编辑时添加新分类: {new_category}")
            
            # 更新工具数据
            index = self.config.tools.index(tool.to_dict())
            self.config.tools[index] = tool_data
            self.config.save_config()
            self.update_category_tree()  # 更新分类树
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def delete_tool(self, item):
        """删除工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工具 '{tool.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 更稳妥地删除工具，避免list.remove(x): x not in list
            for idx, t in enumerate(self.config.tools):
                if (
                    t.get('name') == tool.name and
                    t.get('path') == tool.path and
                    t.get('category') == tool.category
                ):
                    del self.config.tools[idx]
                    break
            self.config.save_config()
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def open_tool_folder(self, item):
        """打开工具所在文件夹"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        
        path_to_check = tool.path
        
        # 如果是文件，获取其所在目录；如果是目录，则使用其本身
        if tool.tool_type == 'folder':
             folder_to_open = path_to_check
        else:
             folder_to_open = os.path.dirname(path_to_check)

        if os.path.exists(folder_to_open) and os.path.isdir(folder_to_open):
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_to_open))
        else:
            QMessageBox.warning(self, "路径不存在", f"无法打开文件夹，路径不是一个有效的文件夹:\n{folder_to_open}")
    
    def open_tool_cmd(self, item):
        """打开工具命令行, 优先使用Windows Terminal, 其次PowerShell, 最后cmd"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        if tool.tool_type == "folder":
            path = tool.path
        else:
            path = os.path.dirname(tool.path)
            
        if not os.path.isdir(path):
            QMessageBox.warning(self, "路径无效", f"无法打开命令行，路径不是一个有效的文件夹:\n{path}")
            return

        # Define creation flags for a new console window
        CREATE_NEW_CONSOLE = 0x00000010

        # Commands to try, in order of preference.
        # The first element is the command list, the second is a dict of extra Popen args.
        terminal_options = [
            {"cmd": ["wt.exe", "-d", path], "args": {}, "name": "Windows Terminal"},
            {"cmd": ["pwsh.exe", "-NoExit"], "args": {"cwd": path}, "name": "PowerShell Core"},
            {"cmd": ["powershell.exe", "-NoExit"], "args": {"cwd": path}, "name": "Windows PowerShell"},
            {"cmd": ["cmd.exe"], "args": {"cwd": path}, "name": "Command Prompt"}
        ]

        for option in terminal_options:
            try:
                subprocess.Popen(option["cmd"], creationflags=CREATE_NEW_CONSOLE, **option["args"])
                logging.info(f"成功使用 {option['name']} 打开路径: {path}")
                return
            except FileNotFoundError:
                logging.info(f"未找到 {option['name']}，尝试下一个...")
            except Exception as e:
                logging.warning(f"启动 {option['name']} 失败: {e}，尝试下一个...")

        QMessageBox.critical(self, "错误", "无法打开任何终端。请检查您的系统配置。")
    
    def show_cyberchef(self):
        """显示CyberChef页面，兼容新版右侧内容区"""
        # 清空右侧内容区
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        # 每次都新建WebView，避免切换后不显示
        self.cyberchef_webview = QWebEngineView()
        self.cyberchef_webview.setMinimumSize(800, 600)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cyberchef_index = os.path.join(current_dir, "project", "CyberChef", "index.html")
        if os.path.exists(cyberchef_index):
            url = QUrl.fromLocalFile(cyberchef_index)
            self.cyberchef_webview.setUrl(url)
        else:
            self.cyberchef_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))
        self.cyberchef_webview.loadFinished.connect(self.on_cyberchef_loaded)
        self.right_layout.addWidget(self.cyberchef_webview)
    
    def set_theme(self, theme_name):
        self.config.theme = theme_name
        self.config.save_config()
        self.apply_theme()
    
    def apply_theme(self):
        """应用主题"""
        theme = self.config.theme
        if theme == "modern_light":
            qss = """
            QMainWindow { background: #fafbfc; }
            QWidget { background: #fafbfc; color: #2c3e50; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #ffffff; color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 6px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #1da1f2; background: #ffffff; 
            }
            QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1da1f2, stop:1 #0d8bd9); 
                color: #fff; 
                border-radius: 8px; 
                padding: 8px 16px; 
                font-weight: 600; 
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d8bd9, stop:1 #1da1f2); 
            }
            QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
                background: #0c7bb8; 
            }
            QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
                background: #b0b0b0;
                color: #f5f5f5;
            }
            QDialog, QMessageBox, QInputDialog {
                background: #fff;
                border-radius: 14px;
            }
            QLabel, QTextBrowser {
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QMenuBar { background: #ffffff; color: #2c3e50; border-bottom: 1px solid #e1e8ed; }
            QMenuBar::item:selected { background: #f7f9fa; border-radius: 4px; }
            QMenu { background: #ffffff; color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 6px; padding: 4px; }
            QMenu::item:selected { background: #f7f9fa; border-radius: 4px; }
            """
        elif theme == "modern_dark":
            qss = """
            QMainWindow { background: #1a1a1a; }
            QWidget { background: #1a1a1a; color: #e0e0e0; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #2d2d2d; color: #e0e0e0; border: 2px solid #404040; border-radius: 8px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #00d4ff; background: #333333; 
            }
            QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00d4ff, stop:1 #0099cc); 
                color: #fff; 
                border-radius: 8px; 
                padding: 10px 16px; 
                font-weight: bold; 
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0099cc, stop:1 #00d4ff); 
            }
            QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
                background: #006699; 
            }
            QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
                background: #444;
                color: #888;
            }
            QDialog, QMessageBox, QInputDialog {
                background: #23272e;
                border-radius: 14px;
            }
            QLabel, QTextBrowser {
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QMenuBar { background: #1a1a1a; color: #e0e0e0; border-bottom: 1px solid #404040; }
            QMenuBar::item:selected { background: #333333; border-radius: 4px; }
            QMenu { background: #2d2d2d; color: #e0e0e0; border: 1px solid #404040; border-radius: 8px; padding: 4px; }
            QMenu::item:selected { background: #333333; border-radius: 4px; }
            """
        elif theme == "dracula":
            qss = """
            QMainWindow { background: #282a36; }
            QWidget { background: #282a36; color: #f8f8f2; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #44475a; color: #f8f8f2; border: 1px solid #6272a4; border-radius: 8px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #bd93f9; background: #44475a; 
            }
            QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
                background: #bd93f9; 
                color: #f8f8f2; 
                border-radius: 8px; 
                padding: 10px 16px; 
                font-weight: bold; 
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
                background: #ff79c6; 
            }
            QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
                background: #ff55b8; 
            }
            QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
                background: #6272a4;
                color: #44475a;
            }
            QDialog, QMessageBox, QInputDialog {
                background: #282a36;
                border-radius: 14px;
            }
            QLabel, QTextBrowser {
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QMenuBar { background: #282a36; color: #f8f8f2; border-bottom: 1px solid #44475a; }
            QMenuBar::item:selected { background: #44475a; border-radius: 4px; }
            QMenu { background: #44475a; color: #f8f8f2; border: 1px solid #6272a4; border-radius: 8px; padding: 4px; }
            QMenu::item:selected { background: #6272a4; border-radius: 4px; }
            """
        elif theme == "solarized_light":
            qss = """
            QMainWindow { background: #fdf6e3; }
            QWidget { background: #fdf6e3; color: #657b83; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #eee8d5; color: #586e75; border: 1px solid #93a1a1; border-radius: 8px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #268bd2; background: #fdf6e3; 
            }
            QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
                background: #2aa198; 
                color: #fdf6e3; 
                border-radius: 8px; 
                padding: 10px 16px; 
                font-weight: bold; 
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
                background: #268bd2; 
            }
            QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
                background: #b58900; 
            }
            QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
                background: #eee8d5;
                color: #93a1a1;
            }
            QDialog, QMessageBox, QInputDialog {
                background: #fdf6e3;
                border-radius: 14px;
            }
            QLabel, QTextBrowser {
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QMenuBar { background: #fdf6e3; color: #657b83; border-bottom: 1px solid #eee8d5; }
            QMenuBar::item:selected { background: #eee8d5; border-radius: 4px; }
            QMenu { background: #eee8d5; color: #586e75; border: 1px solid #93a1a1; border-radius: 8px; padding: 4px; }
            QMenu::item:selected { background: #fdf6e3; border-radius: 4px; }
            """
        elif theme == "solarized_dark":
            qss = """
            QMainWindow { background: #002b36; }
            QWidget { background: #002b36; color: #839496; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #073642; color: #93a1a1; border: 1px solid #586e75; border-radius: 8px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #268bd2; background: #073642; 
            }
            QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
                background: #2aa198; 
                color: #002b36; 
                border-radius: 8px; 
                padding: 10px 16px; 
                font-weight: bold; 
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
                background: #268bd2; 
            }
            QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
                background: #b58900; 
            }
            QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
                background: #073642;
                color: #586e75;
            }
            QDialog, QMessageBox, QInputDialog {
                background: #002b36;
                border-radius: 14px;
            }
            QLabel, QTextBrowser {
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QMenuBar { background: #002b36; color: #839496; border-bottom: 1px solid #073642; }
            QMenuBar::item:selected { background: #073642; border-radius: 4px; }
            QMenu { background: #073642; color: #93a1a1; border: 1px solid #586e75; border-radius: 8px; padding: 4px; }
            QMenu::item:selected { background: #586e75; border-radius: 4px; }
            """
        elif theme == "nord":
            qss = """
            QMainWindow { background: #2e3440; }
            QWidget { background: #2e3440; color: #d8dee9; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #3b4252; color: #eceff4; border: 1px solid #4c566a; border-radius: 8px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #88c0d0; background: #434c5e; 
            }
            QPushButton, QDialogButtonBox QPushButton, QMessageBox QPushButton { 
                background: #81a1c1; 
                color: #2e3440; 
                border-radius: 8px; 
                padding: 10px 16px; 
                font-weight: bold; 
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover, QDialogButtonBox QPushButton:hover, QMessageBox QPushButton:hover { 
                background: #88c0d0; 
            }
            QPushButton:pressed, QDialogButtonBox QPushButton:pressed, QMessageBox QPushButton:pressed { 
                background: #5e81ac; 
            }
            QPushButton:disabled, QDialogButtonBox QPushButton:disabled, QMessageBox QPushButton:disabled {
                background: #4c566a;
                color: #3b4252;
            }
            QDialog, QMessageBox, QInputDialog {
                background: #2e3440;
                border-radius: 14px;
            }
            QLabel, QTextBrowser {
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QMenuBar { background: #2e3440; color: #d8dee9; border-bottom: 1px solid #3b4252; }
            QMenuBar::item:selected { background: #434c5e; border-radius: 4px; }
            QMenu { background: #3b4252; color: #eceff4; border: 1px solid #4c566a; border-radius: 8px; padding: 4px; }
            QMenu::item:selected { background: #4c566a; border-radius: 4px; }
            """
        else:
            qss = ""
        self.setStyleSheet(qss)
    
    def export_config(self):
        """导出配置，包含所有工具及分类信息"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({
                        "tools": self.config.tools,
                        "theme": self.config.theme,
                        "view_mode": self.config.view_mode
                    }, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", "配置导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def import_config(self):
        """导入配置，自动刷新树形大纲和工具列表"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config.tools = data.get("tools", [])
                self.config.theme = data.get("theme", "modern_light")
                self.config.view_mode = data.get("view_mode", "list")
                self.config.save_config()
                self.refresh_outline_and_tools()
                self.apply_theme()
                QMessageBox.information(self, "成功", "配置导入成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")

    def show_category_context_menu(self, position):
        item = self.category_tree.itemAt(position)
        menu = QMenu()
        if item:
            rename_action = QAction("重命名", self)
            rename_action.triggered.connect(partial(self.rename_category, item))
            menu.addAction(rename_action)

            delete_action = QAction("删除", self)
            delete_action.triggered.connect(partial(self.delete_category, item))
            menu.addAction(delete_action)

            add_sub_action = QAction("添加子分类", self)
            add_sub_action.triggered.connect(partial(self.add_subcategory, item))
            menu.addAction(add_sub_action)
        else:
            add_action = QAction("添加主分类", self)
            add_action.triggered.connect(self.add_category)
            menu.addAction(add_action)
        menu.exec(self.category_tree.viewport().mapToGlobal(position))

    def rename_category(self, item):
        old_name = item.text(0)
        new_name, ok = QInputDialog.getText(self, "重命名分类", "请输入新名称:", text=old_name)
        if ok and new_name and new_name != old_name:
            # 更新分类列表
            if item.parent() is None:
                # 主分类
                if new_name in self.config.categories:
                    QMessageBox.warning(self, "错误", "该分类已存在")
                    return
                idx = self.config.categories.index(old_name)
                self.config.categories[idx] = new_name
                # 更新所有工具的分类字段
                for tool in self.config.tools:
                    if tool["category"] == old_name:
                        tool["category"] = new_name
            else:
                # 子分类
                parent_name = item.parent().text(0)
                for tool in self.config.tools:
                    if tool["category"] == parent_name and tool["subcategory"] == old_name:
                        tool["subcategory"] = new_name
            self.config.save_config()
            self.update_category_tree()
            self.update_tools_list()

    def delete_category(self, item):
        name = item.text(0)
        if item.parent() is None:
            # 主分类
            reply = QMessageBox.question(self, "确认删除", f"确定要删除主分类 '{name}' 及其所有子分类和工具吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.config.categories.remove(name)
                # 删除所有相关工具
                self.config.tools = [tool for tool in self.config.tools if tool["category"] != name]
                self.config.save_config()
                self.update_category_tree()
                self.update_tools_list()
        else:
            # 子分类
            parent_name = item.parent().text(0)
            reply = QMessageBox.question(self, "确认删除", f"确定要删除子分类 '{name}' 及其所有工具吗？", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                for tool in self.config.tools:
                    if tool["category"] == parent_name and tool["subcategory"] == name:
                        tool["subcategory"] = ""
                self.config.save_config()
                self.update_category_tree()
                self.update_tools_list()

    def add_subcategory(self, item):
        if item.parent() is not None:
            QMessageBox.warning(self, "提示", "暂不支持多级子分类")
            return
        parent_name = item.text(0)
        sub_name, ok = QInputDialog.getText(self, "添加子分类", f'请输入"{parent_name}"下的新子分类名称:')
        if ok and sub_name:
            # 检查是否已存在
            for tool in self.config.tools:
                if tool["category"] == parent_name and tool["subcategory"] == sub_name:
                    QMessageBox.warning(self, "错误", "该子分类已存在")
                    return
            
            # 创建一个空的占位工具来显示二级分类
            placeholder_tool = {
                "name": f"[{sub_name}] - 空分类",
                "path": "",
                "category": parent_name,
                "subcategory": sub_name,
                "tool_type": "placeholder",
                "description": f"这是 {sub_name} 分类的占位符，可以添加工具到此分类",
                "icon_path": None,
                "color": "#000000",
                "launch_count": 0,
                "last_launch": None,
                "args": ""
            }
            
            self.config.tools.append(placeholder_tool)
            self.config.save_config()
            
            # 刷新当前分类的工具列表以显示新的二级分类
            self.update_tools_list(parent_name)

    def resizeEvent(self, event):
        """窗口大小变化事件，兼容新版右侧内容区"""
        super().resizeEvent(event)
        # 兼容新版：如果右侧内容区有CyberChef页面则自适应
        if hasattr(self, 'cyberchef_webview') and self.cyberchef_webview.parent() == self.right_panel:
            self.cyberchef_webview.resize(self.right_panel.size())

    def on_cyberchef_loaded(self, success):
        """CyberChef加载完成后的处理"""
        if success:
            logging.info("CyberChef加载成功")
            # 注入更强力的JS，自动均分三栏并触发resize
            js = '''
            (function() {
                let splitters = document.querySelectorAll('.vsplit, .hsplit');
                splitters.forEach(function(splitter) {
                    let children = Array.from(splitter.children);
                    children.forEach(function(child) {
                        child.style.width = (100 / children.length) + '%';
                        child.style.flex = '1 1 0%';
                        child.style.minWidth = '0';
                    });
                    window.dispatchEvent(new Event('resize'));
                });
            })();
            '''
            self.cyberchef_webview.page().runJavaScript(js)
        else:
            logging.error("CyberChef加载失败")
            self.cyberchef_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))

    def rename_subcategory(self, item):
        """重命名二级分类"""
        # 从显示文本中提取分类名称（去掉图标）
        old_name = item.text(0).replace("📁 ", "").replace("📂 ", "")
        new_name, ok = QInputDialog.getText(
            self, "重命名分类", "请输入新的分类名称:", text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            # 获取当前选中的一级分类
            current_category_item = self.category_tree.currentItem()
            if not current_category_item:
                return
            category_name = current_category_item.text(0)
            
            # 更新所有相关工具的子分类字段
            for tool in self.config.tools:
                if tool["category"] == category_name and tool["subcategory"] == old_name:
                    tool["subcategory"] = new_name
            
            self.config.save_config()
            # 重新加载当前分类的工具列表
            self.update_tools_list(category_name)

    def custom_drag_enter_event(self, event):
        """自定义拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def custom_drag_move_event(self, event):
        """自定义拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def custom_drop_event(self, event):
        """自定义拖拽放置事件"""
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.ignore()
            return

        source_item = self.tools_tree.currentItem()
        if not source_item:
            event.ignore()
            return

        target_item = self.tools_tree.itemAt(event.position().toPoint())
        if not target_item:
            event.ignore()
            return

        # 拖动工具到二级分类
        if source_item.parent() is not None and target_item.parent() is None and target_item.childCount() > 0:
            tool = source_item.data(0, Qt.ItemDataRole.UserRole)
            if tool:
                subcategory_name = target_item.text(0).replace("📁 ", "").replace("📂 ", "")
                current_category_item = self.category_tree.currentItem()
                if current_category_item:
                    category_name = current_category_item.text(0)
                    for t in self.config.tools:
                        if t["name"] == tool.name and t["category"] == category_name:
                            t["subcategory"] = subcategory_name
                            break
                    self.config.save_config()
                    self.update_tools_list(category_name)
            event.acceptProposedAction()
            return

        # 二级分类之间拖动
        if (source_item.parent() is None and source_item.childCount() > 0 and
            target_item.parent() is None and target_item.childCount() > 0):
            source_index = self.tools_tree.indexOfTopLevelItem(source_item)
            target_index = self.tools_tree.indexOfTopLevelItem(target_item)
            if source_index != target_index:
                self.tools_tree.takeTopLevelItem(source_index)
                self.tools_tree.insertTopLevelItem(target_index, source_item)
                current_category_item = self.category_tree.currentItem()
                if current_category_item:
                    category_name = current_category_item.text(0)
                    self.reorder_subcategories(category_name)
            event.acceptProposedAction()
            return

        # 其他情况不允许
        event.ignore()

    def reorder_subcategories(self, category_name):
        """重新排序二级分类"""
        # 获取当前树中的所有二级分类顺序
        subcategory_order = []
        for i in range(self.tools_tree.topLevelItemCount()):
            item = self.tools_tree.topLevelItem(i)
            if item.childCount() > 0:  # 这是一个二级分类
                subcategory_name = item.text(0).replace("📁 ", "").replace("📂 ", "")
                subcategory_order.append(subcategory_name)
        
        # 重新组织工具数据，按照新的顺序
        reorganized_tools = []
        
        # 先添加没有子分类的工具
        for tool in self.config.tools:
            if tool["category"] == category_name and not tool["subcategory"]:
                reorganized_tools.append(tool)
        
        # 按照新顺序添加有子分类的工具
        for subcategory in subcategory_order:
            for tool in self.config.tools:
                if tool["category"] == category_name and tool["subcategory"] == subcategory:
                    reorganized_tools.append(tool)
        
        # 更新配置中的工具列表
        # 先移除当前分类的所有工具
        self.config.tools = [tool for tool in self.config.tools if tool["category"] != category_name]
        # 再添加重新组织的工具
        self.config.tools.extend(reorganized_tools)
        
        self.config.save_config()

    def add_tool_to_subcategory(self, subcategory_name):
        """添加工具到指定子分类"""
        # 获取当前选中的一级分类
        current_category_item = self.category_tree.currentItem()
        if not current_category_item:
            return
        category_name = current_category_item.text(0)
        
        # 打开添加工具对话框，并预设子分类
        dialog = AddToolDialog(self.config.categories, self)
        dialog.category_combo.setCurrentText(category_name)
        # 这里需要添加一个子分类输入框，暂时用文本提示
        dialog.setWindowTitle(f"添加工具到 {subcategory_name} 分类")
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["subcategory"] = subcategory_name  # 强制设置子分类
            
            # 检查是否添加了新分类
            new_category = tool_data["category"]
            if new_category not in self.config.categories:
                self.config.categories.append(new_category)
                logging.info(f"添加新分类: {new_category}")
            
            self.config.tools.append(tool_data)
            self.config.save_config()
            self.update_category_tree()  # 更新分类树
            
            # 如果当前选中的是工具所属的分类，则刷新工具列表
            if current_category_item.text(0) == tool_data["category"]:
                self.update_tools_list(tool_data["category"])
    
    def delete_placeholder_subcategory(self, placeholder_tool):
        """删除占位符子分类"""
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除空分类 '{placeholder_tool.subcategory}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除占位符工具
            self.config.tools.remove(placeholder_tool.to_dict())
            self.config.save_config()
            
            # 刷新当前分类的工具列表
            current_category_item = self.category_tree.currentItem()
            if current_category_item:
                category_name = current_category_item.text(0)
                self.update_tools_list(category_name)

    def show_total_tools(self):
        """显示总工具数统计（重新设计现代化UI）"""
        total_tools = len(self.config.tools)
        total_categories = len(self.config.categories)
        total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
        
        # 计算更多统计信息
        active_tools = sum(1 for tool in self.config.tools if tool.get("launch_count", 0) > 0)
        avg_launches = total_launches / total_tools if total_tools > 0 else 0
        
        # 计算使用率
        usage_rate = (active_tools / total_tools * 100) if total_tools > 0 else 0
        
        # 创建现代化对话框
        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setWindowTitle("📊 工具统计面板")
        dialog.setMinimumSize(800, 500)
        dialog.setMaximumSize(1000, 600)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        dialog.move((screen.width() - dialog.width()) // 2,
                   (screen.height() - dialog.height()) // 2)
        
        # 主布局
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 顶部标题栏
        title_bar = QWidget()
        title_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)
        
        title_icon = QLabel("📊")
        title_icon.setStyleSheet("font-size: 24px;")
        title_layout.addWidget(title_icon)
        
        title_text = QLabel("工具统计面板")
        title_text.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: white;
            margin-left: 10px;
        """)
        title_layout.addWidget(title_text)
        title_layout.addStretch()
        
        # Make window draggable
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()

        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)

        def mouseReleaseEvent(event):
            dialog.offset = None
        
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent
        
        # 关闭按钮
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 15px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.1);
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        
        main_layout.addWidget(title_bar)
        
        # 内容区域
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)
        
        # 主要统计卡片行
        main_stats_layout = QHBoxLayout()
        main_stats_layout.setSpacing(15)
        
        # 创建主要统计卡片
        main_stats = [
            {
                "title": "总工具数",
                "value": str(total_tools),
                "icon": "🛠️",
                "color": "#667eea",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2)",
                "description": "已配置的工具总数"
            },
            {
                "title": "总分类数",
                "value": str(total_categories),
                "icon": "📁",
                "color": "#f093fb",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #f093fb, stop:1 #f5576c)",
                "description": "工具分类数量"
            },
            {
                "title": "总启动次数",
                "value": str(total_launches),
                "icon": "🚀",
                "color": "#4facfe",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4facfe, stop:1 #00f2fe)",
                "description": "累计启动次数"
            }
        ]
        
        for stat in main_stats:
            card = self._create_stat_card(stat)
            main_stats_layout.addWidget(card)
        
        content_layout.addLayout(main_stats_layout)
        
        # 次要统计卡片行
        secondary_stats_layout = QHBoxLayout()
        secondary_stats_layout.setSpacing(15)
        
        # 创建次要统计卡片
        secondary_stats = [
            {
                "title": "活跃工具",
                "value": f"{active_tools}",
                "icon": "⭐",
                "color": "#43e97b",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7)",
                "description": f"使用率: {usage_rate:.1f}%"
            },
            {
                "title": "平均启动",
                "value": f"{avg_launches:.1f}",
                "icon": "📈",
                "color": "#fa709a",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fa709a, stop:1 #fee140)",
                "description": "每个工具平均启动次数"
            },
            {
                "title": "使用状态",
                "value": "正常" if total_tools > 0 else "无工具",
                "icon": "✅" if total_tools > 0 else "⚠️",
                "color": "#a8edea" if total_tools > 0 else "#fed6e3",
                "gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a8edea, stop:1 #fed6e3)" if total_tools > 0 else "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fed6e3, stop:1 #a8edea)",
                "description": "系统运行状态"
            }
        ]
        
        for stat in secondary_stats:
            card = self._create_stat_card(stat)
            secondary_stats_layout.addWidget(card)
        
        content_layout.addLayout(secondary_stats_layout)
        
        # 详细信息区域
        details_group = QGroupBox("📋 详细信息")
        details_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #495057;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background: #f8f9fa;
            }
        """)
        
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(15, 20, 15, 15)
        details_layout.setSpacing(10)
        
        # 详细信息文本
        details_text = f"""
        <div style="font-size: 13px; line-height: 1.6; color: #6c757d;">
        <b>📊 统计概览：</b><br>
        • 当前共配置了 <span style="color: #667eea; font-weight: bold;">{total_tools}</span> 个工具<br>
        • 分布在 <span style="color: #f093fb; font-weight: bold;">{total_categories}</span> 个分类中<br>
        • 累计启动 <span style="color: #4facfe; font-weight: bold;">{total_launches}</span> 次<br>
        • 活跃工具占比 <span style="color: #43e97b; font-weight: bold;">{usage_rate:.1f}%</span><br>
        • 平均每个工具启动 <span style="color: #fa709a; font-weight: bold;">{avg_launches:.1f}</span> 次<br>
        </div>
        """
        
        details_label = QLabel(details_text)
        details_label.setWordWrap(True)
        details_layout.addWidget(details_label)
        
        content_layout.addWidget(details_group)
        
        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 刷新按钮
        refresh_btn = QPushButton("🔄 刷新统计")
        refresh_btn.setFixedSize(120, 40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b);
            }
            QPushButton:pressed {
                background: #3dd16a;
            }
        """)
        refresh_btn.clicked.connect(lambda: self.refresh_stats_and_close(dialog))
        
        # 导出按钮
        export_btn = QPushButton("📤 导出报告")
        export_btn.setFixedSize(120, 40)
        export_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38f9d7, stop:1 #43e97b);
            }
            QPushButton:pressed {
                background: #3dd16a;
            }
        """)
        export_btn.clicked.connect(lambda: self.export_stats_report())
        
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(export_btn)
        button_layout.addStretch()
        
        content_layout.addLayout(button_layout)
        
        main_layout.addWidget(content_widget)
        
        dialog.exec()
    
    def _create_stat_card(self, stat_data):
        """创建统计卡片"""
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setFixedSize(200, 120)
        card.setStyleSheet(f"""
            QWidget {{
                background: {stat_data['gradient']};
                border-radius: 12px;
                color: white;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # 图标和标题
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)
        
        icon_label = QLabel(stat_data['icon'])
        icon_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(stat_data['title'])
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: rgba(255, 255, 255, 0.9);
        """)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 数值
        value_label = QLabel(stat_data['value'])
        value_label.setStyleSheet("""
            font-size: 28px;
            font-weight: bold;
            color: white;
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # 描述
        desc_label = QLabel(stat_data['description'])
        desc_label.setStyleSheet("""
            font-size: 10px;
            color: rgba(255, 255, 255, 0.8);
        """)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        return card
    
    def export_stats_report(self):
        """导出统计报告"""
        try:
            total_tools = len(self.config.tools)
            total_categories = len(self.config.categories)
            total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
            active_tools = sum(1 for tool in self.config.tools if tool.get("launch_count", 0) > 0)
            avg_launches = total_launches / total_tools if total_tools > 0 else 0
            usage_rate = (active_tools / total_tools * 100) if total_tools > 0 else 0
            
            # 生成报告内容
            report_content = f"""
AppLauncher 工具统计报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 基础统计 ===
总工具数: {total_tools}
总分类数: {total_categories}
总启动次数: {total_launches}
活跃工具数: {active_tools}
平均启动次数: {avg_launches:.1f}
使用率: {usage_rate:.1f}%

=== 分类统计 ===
"""
            
            # 按分类统计
            category_stats = {}
            for tool in self.config.tools:
                category = tool.get('category', '未分类')
                if category not in category_stats:
                    category_stats[category] = {'count': 0, 'launches': 0}
                category_stats[category]['count'] += 1
                category_stats[category]['launches'] += tool.get('launch_count', 0)
            
            for category, stats in sorted(category_stats.items()):
                report_content += f"{category}: {stats['count']} 个工具, {stats['launches']} 次启动\n"
            
            report_content += f"""
=== 最常用工具 (前10名) ===
"""
            
            # 最常用工具
            sorted_tools = sorted(self.config.tools, key=lambda x: x.get('launch_count', 0), reverse=True)
            for i, tool in enumerate(sorted_tools[:10], 1):
                report_content += f"{i}. {tool.get('name', 'Unknown')}: {tool.get('launch_count', 0)} 次启动\n"
            
            # 保存报告
            path, _ = QFileDialog.getSaveFileName(
                self, "导出统计报告", f"AppLauncher_统计报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", 
                "文本文件 (*.txt)"
            )
            
            if path:
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(report_content)
                QMessageBox.information(self, "导出成功", f"统计报告已导出到:\n{path}")
            
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出统计报告时发生错误:\n{str(e)}")
    
    def refresh_stats_and_close(self, dialog):
        """刷新统计并关闭对话框"""
        self.update_status_stats()
        dialog.accept()
        self.show_total_tools()
    
    def show_recent_tools(self):
        """显示最近启动的工具（优化UI，支持图标和点击执行）"""
        if not self.config.recent_tools:
            QMessageBox.information(self, "最近启动的工具", "暂无最近启动的工具")
            return

        dialog = QDialog(self)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        dialog.setWindowTitle("🕒 最近启动的工具")
        dialog.setMinimumSize(800, 600)

        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        dialog.move((screen.width() - dialog.width()) // 2,
                   (screen.height() - dialog.height()) // 2)

        # Main layout
        main_layout = QVBoxLayout(dialog)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Custom Title Bar
        title_bar = QWidget()
        title_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        title_bar.setFixedHeight(60)
        title_bar.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #43e97b, stop:1 #38f9d7);
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
            }
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(20, 0, 20, 0)

        title_icon = QLabel("🕒")
        title_icon.setStyleSheet("font-size: 24px; color: white;")
        title_layout.addWidget(title_icon)

        title_text = QLabel("最近启动的工具")
        title_text.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-left: 10px;")
        title_layout.addWidget(title_text)
        title_layout.addStretch()

        # Draggability
        dialog.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.MouseButton.LeftButton:
                dialog.offset = event.globalPosition().toPoint() - dialog.pos()
        def mouseMoveEvent(event):
            if dialog.offset is not None and event.buttons() == Qt.MouseButton.LeftButton:
                dialog.move(event.globalPosition().toPoint() - dialog.offset)
        def mouseReleaseEvent(event):
            dialog.offset = None
        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent
        title_bar.mouseReleaseEvent = mouseReleaseEvent

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton { background: rgba(255, 255, 255, 0.2); border: none; border-radius: 15px; color: white; font-size: 14px; font-weight: bold; }
            QPushButton:hover { background: rgba(255, 255, 255, 0.3); }
            QPushButton:pressed { background: rgba(255, 255, 255, 0.1); }
        """)
        close_btn.clicked.connect(dialog.accept)
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # Content Area
        content_widget = QWidget()
        content_widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        content_widget.setStyleSheet("""
            QWidget {
                background: #f8f9fa;
                border-bottom-left-radius: 12px;
                border-bottom-right-radius: 12px;
            }
        """)
        
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(15)

        # Scroll Area for the list
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { border: none; background: #e9ecef; width: 8px; margin: 0px 0px 0px 0px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #ced4da; min-height: 20px; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { border: none; background: none; }
        """)

        list_container = QWidget()
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 5, 0) # Right margin for scrollbar
        list_layout.setSpacing(10)
        
        # Populate list
        for i, tool_name in enumerate(self.config.recent_tools[:20], 1):
            tool = next((Tool.from_dict(t) for t in self.config.tools if t["name"] == tool_name), None)
            if tool:
                tool_item_card = self._create_recent_tool_card(tool, i, dialog)
                list_layout.addWidget(tool_item_card)
        
        list_layout.addStretch(1)
        scroll_area.setWidget(list_container)
        content_layout.addWidget(scroll_area)

        # Bottom button area
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        clear_button = QPushButton("🗑️ 清空历史")
        clear_button.setFixedSize(120, 40)
        clear_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fa709a, stop:1 #fee140);
                color: white; border: none; border-radius: 20px; font-size: 14px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #fee140, stop:1 #fa709a); }
        """)
        clear_button.clicked.connect(lambda: self.clear_recent_history(dialog))
        bottom_layout.addWidget(clear_button)
        bottom_layout.addStretch()
        content_layout.addLayout(bottom_layout)

        main_layout.addWidget(content_widget)
        dialog.exec()
    
    def _create_recent_tool_card(self, tool, index, parent_dialog):
        """Creates a styled card widget for a recent tool."""
        card = QWidget()
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setMinimumHeight(80)
        # Add a property to make it easy to find for double-click event handling if needed later
        card.setProperty("isCard", True)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setStyleSheet("""
            QWidget[isCard="true"] {
                background: white;
                border: 1px solid #e9ecef;
                border-radius: 10px;
            }
            QWidget[isCard="true"]:hover {
                border: 1px solid #43e97b;
                background: #f8f9fa;
            }
        """)
        
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(15, 10, 15, 10)
        card_layout.setSpacing(15)

        # Index
        index_label = QLabel(f"{index:02d}")
        index_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ced4da; background: transparent;")
        index_label.setFixedWidth(30)
        card_layout.addWidget(index_label)

        # Icon
        icon_label = QLabel()
        icon_label.setFixedSize(48, 48)
        icon_label.setStyleSheet("background: #e9ecef; border-radius: 24px;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if tool.icon_path and os.path.exists(tool.icon_path):
            pixmap = QIcon(tool.icon_path).pixmap(32, 32)
            icon_label.setPixmap(pixmap)
        else:
            emoji = self._get_tool_icon(tool)
            icon_label.setText(f"<span style='font-size: 24px;'>{emoji}</span>")
            
        card_layout.addWidget(icon_label)

        # Info
        info_container = QWidget()
        info_container.setStyleSheet("background: transparent;")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        name_label = QLabel(tool.name)
        name_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #212529; background: transparent;")
        desc_label = QLabel(f"类型: {tool.tool_type} | 启动: {tool.launch_count} 次")
        desc_label.setStyleSheet("font-size: 11px; color: #6c757d; background: transparent;")
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        card_layout.addWidget(info_container, 1)

        # Launch Button
        launch_btn = QPushButton("🚀 启动")
        launch_btn.setFixedSize(90, 36)
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        launch_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #667eea, stop:1 #764ba2);
                color: white; border: none; border-radius: 18px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #764ba2, stop:1 #667eea); }
        """)
        launch_btn.clicked.connect(lambda: self.launch_tool_from_recent(tool, parent_dialog))
        card_layout.addWidget(launch_btn)

        # Double click to launch
        card.mouseDoubleClickEvent = lambda event: self.launch_tool_from_recent(tool, parent_dialog)

        return card
    
    def launch_tool_from_recent(self, tool, dialog):
        """从最近工具列表启动工具"""
        self.startToolLaunch.emit(tool, True)
        dialog.accept() # 启动成功后关闭对话框
    
    def clear_recent_history(self, dialog):
        """清空最近使用历史（美化确认弹窗按钮）"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认清空")
        msg_box.setText("确定要清空最近使用历史吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        yes_btn = msg_box.addButton("是", QMessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton("否", QMessageBox.ButtonRole.NoRole)
        msg_box.setStyleSheet("""
            QMessageBox {
                background: #fff;
                border-radius: 12px;
            }
            QLabel {
                color: #222;
                font-size: 15px;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1da1f2, stop:1 #0d8bd9);
                color: #fff;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
                min-width: 80px;
                min-height: 32px;
                margin: 0 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0d8bd9, stop:1 #1da1f2);
            }
        """)
        msg_box.exec()
        if msg_box.clickedButton() == yes_btn:
            self.config.recent_tools.clear()
            self.config.save_config()
            dialog.accept()
            QMessageBox.information(self, "清空完成", "最近使用历史已清空")
    
    def show_favorites(self):
        """显示收藏工具"""
        if not self.config.favorites:
            QMessageBox.information(self, "收藏工具", "暂无收藏的工具")
            return
        
        favorites_text = "⭐ 收藏工具\n\n"
        for i, tool_name in enumerate(self.config.favorites, 1):
            favorites_text += f"{i}. {tool_name}\n"
        
        QMessageBox.information(self, "收藏工具", favorites_text)
    
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_tools_list()
    def next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_tools_list()

    def search_tools(self, text):
        """搜索工具(此方法已废弃,逻辑由多线程工作者替代)"""
        pass
    
    def _create_search_tool_item(self, tool):
        """创建搜索结果的工具项"""
        item = self.tools_list.findItems(tool.name, Qt.MatchFlag.MatchExactly)
        if item:
             self.show_tools_list([tool])

    def launch_tool_card(self, tool):
        """启动工具卡片"""
        self.startToolLaunch.emit(tool, True)
    
    def show_context_menu(self, position):
        """显示工具右键菜单，优化：仅右键空白处显示新增工具"""
        item = self.tools_list.itemAt(position)
        menu = QMenu()
        if item is not None and item.data(Qt.ItemDataRole.UserRole):
            tool = item.data(Qt.ItemDataRole.UserRole)
            launch_action = QAction("启动", self)
            launch_action.triggered.connect(lambda: self.launch_tool(item))
            menu.addAction(launch_action)
            edit_action = QAction("编辑", self)
            edit_action.triggered.connect(lambda: self.edit_tool(item))
            menu.addAction(edit_action)
            open_folder_action = QAction("打开所在文件夹", self)
            open_folder_action.triggered.connect(lambda: self.open_tool_folder(item))
            menu.addAction(open_folder_action)
            open_cmd_action = QAction("打开命令行", self)
            open_cmd_action.triggered.connect(lambda: self.open_tool_cmd(item))
            menu.addAction(open_cmd_action)
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(lambda: self.delete_tool(item))
            menu.addAction(delete_action)
        else:
            # 仅右键空白处显示新增工具
            add_action = QAction("新增工具", self)
            add_action.triggered.connect(self.add_tool)
            menu.addAction(add_action)
        menu.exec(self.tools_list.viewport().mapToGlobal(position))

    def edit_tool(self, item):
        """编辑工具，支持修改分类，保存后自动刷新大纲"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        dialog = AddToolDialog([], self)
        dialog.name_edit.setText(tool.name)
        dialog.path_edit.setText(tool.path)
        dialog.category_combo.setEditText(tool.category)
        dialog.args_edit.setText(tool.args)
        dialog.icon_edit.setText(tool.icon_path or "")
        dialog.desc_edit.setPlainText(tool.description)
        # 设置工具类型
        type_mapping_reverse = {
            "exe": "GUI应用",
            "java8_gui": "java8图形化",
            "java11_gui": "java11图形化",
            "java8": "java8",
            "java11": "java11",
            "python": "python",
            "powershell": "powershell",
            "batch": "批处理",
            "url": "网页",
            "folder": "文件夹"
        }
        tool_type = type_mapping_reverse.get(tool.tool_type, "GUI应用")
        dialog.type_combo.setCurrentText(tool_type)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            tool_data["launch_count"] = tool.launch_count
            tool_data["last_launch"] = tool.last_launch
            # 更新工具数据
            for idx, t in enumerate(self.config.tools):
                if t.get('name') == tool.name and t.get('path') == tool.path and t.get('category') == tool.category:
                    self.config.tools[idx] = tool_data
                    break
            self.config.save_config()
            self.refresh_outline_and_tools()

    def add_tool(self):
        """新增工具，保存后自动刷新大纲"""
        dialog = AddToolDialog([], self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            self.config.tools.append(tool_data)
            self.config.save_config()
            self.refresh_outline_and_tools()

    def delete_tool(self, item):
        """删除工具，自动刷新大纲"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工具 '{tool.name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for idx, t in enumerate(self.config.tools):
                if t.get('name') == tool.name and t.get('path') == tool.path and t.get('category') == tool.category:
                    del self.config.tools[idx]
                    break
            self.config.save_config()
            self.refresh_outline_and_tools()

    def open_tool_folder(self, item, all_paths=False):
        """打开工具所有路径文件夹"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        paths = [tool.path]
        if all_paths and hasattr(tool, 'extra_paths'):
            paths += tool.extra_paths
        for path in paths:
            folder = os.path.dirname(path)
            if os.path.exists(folder):
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def open_tool_cmd(self, item):
        """打开工具所在路径命令行"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
        folder = os.path.dirname(tool.path)
        if os.path.exists(folder):
            subprocess.Popen(["cmd", "/k", f"cd /d {folder}"])
    
    def add_favorite(self, tool_name):
        """添加到收藏"""
        self.config.add_to_favorites(tool_name)
        self.update_status_stats()
        self.status_label.setText(f"已添加 '{tool_name}' 到收藏")
    
    def remove_favorite(self, tool_name):
        """从收藏中移除"""
        self.config.remove_from_favorites(tool_name)
        self.update_status_stats()
        self.status_label.setText(f"已从收藏中移除 '{tool_name}'")

    def switch_assist_tab(self, tab_name):
        """切换辅助工具tab"""
        for btn in self.assist_tabs:
            btn.setChecked(False)
        if tab_name == 'shellgen':
            self.btn_shellgen.setChecked(True)
            self.assist_content.setCurrentIndex(0)
            self.current_assist_tab = 'shellgen'
        elif tab_name == 'java_encode':
            self.btn_java_encode.setChecked(True)
            self.assist_content.setCurrentIndex(1)
            self.current_assist_tab = 'java_encode'

    def closeEvent(self, event):
        """处理窗口关闭事件，安全地终止工作线程"""
        logging.info("正在关闭应用程序，请稍候...")
        
        # 停止所有定时器
        self.search_timer.stop()
        self.config_save_timer.stop()
        self.memory_optimize_timer.stop()
        
        # 停止所有工作线程
        self.search_thread.quit()
        self.icon_loader_thread.quit()
        self.tool_launcher_thread.quit()
        self.config_saver_thread.quit()
        self.process_monitor_worker.stop_monitoring()
        self.process_monitor_thread.quit()
        
        # 等待线程安全退出
        threads_to_wait = [
            (self.search_thread, "搜索线程"),
            (self.icon_loader_thread, "图标加载线程"),
            (self.tool_launcher_thread, "工具启动线程"),
            (self.config_saver_thread, "配置保存线程"),
            (self.pip_installer_thread, "Pip安装线程"),
            (self.process_monitor_thread, "进程监控线程")
        ]
        
        for thread, name in threads_to_wait:
            if not thread.wait(1000):  # 等待1秒
                logging.warning(f"{name}未能及时停止。")
        
        # 清空缓存
        self.cache_manager.clear()
        
        super().closeEvent(event)

    def handle_installation_required(self, tool, target):
        """处理Python依赖安装请求"""
        self.startPipInstall.emit(tool, target)

    def handle_installation_started(self, tool_name):
        """处理安装开始事件"""
        self.install_progress_bar.setVisible(True)
        self.install_progress_bar.setRange(0, 0)  # 设置为不确定模式
        self.status_label.setText(f"为 {tool_name} 开始安装依赖...")

    def handle_installation_progress(self, tool_name, message):
        """处理安装进度更新"""
        self.status_label.setText(f"[{tool_name}] {message}")

    def handle_installation_finished(self, tool_name, success, error_msg, tool):
        """处理安装完成事件"""
        self.install_progress_bar.setVisible(False)
        self.install_progress_bar.setRange(0, 100) # 重置
        if success:
            self.status_label.setText(f"✅ {tool_name} 依赖安装成功，正在重新启动...")
            # 重新启动，跳过依赖检查
            self.startToolLaunch.emit(tool, False)
        else:
            self.status_label.setText(f"❌ {tool_name} 依赖安装失败: {error_msg}")
            QMessageBox.critical(self, "安装失败", f"为 {tool_name} 安装依赖失败: \n{error_msg}")

if __name__ == "__main__":
    logging.info("程序开始运行...")
    app = QApplication(sys.argv)
    logging.info("创建 QApplication 实例...")
    window = MainWindow()
    logging.info("创建主窗口...")
    window.show()
    logging.info("显示主窗口...")
    sys.exit(app.exec()) 