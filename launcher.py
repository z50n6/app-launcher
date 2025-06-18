import sys
import os
import json
import subprocess
import webbrowser
import time
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
from PyQt6.QtCore import Qt, QUrl, QTimer, QThread, pyqtSignal, QSize, QRect, QPoint, QSettings, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon, QPixmap, QAction, QKeySequence, QDesktopServices, QPainter, QBrush, QPen
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage

print("开始导入模块...")

class Config:
    """配置管理类"""
    def __init__(self):
        print("初始化配置...")
        self.settings = QSettings("AppLauncher", "AppLauncher")
        self.theme_list = ["modern_light", "modern_dark", "light", "dark", "elegant", "cyber", "minimal", "soft"]
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        print("加载配置...")
        self.categories = self.settings.value("categories", ["信息收集", "漏洞扫描", "漏洞利用", "后渗透", "流量与代理", "编码与解码"])
        self.tools = self.settings.value("tools", [])
        self.theme = self.settings.value("theme", "light")
        self.view_mode = self.settings.value("view_mode", "list")
        self.favorites = self.settings.value("favorites", [])  # 收藏的工具
        self.recent_tools = self.settings.value("recent_tools", [])  # 最近使用的工具
        self.show_status_bar = self.settings.value("show_status_bar", True)  # 显示状态栏
        self.auto_refresh = self.settings.value("auto_refresh", True)  # 自动刷新
        self.search_history = self.settings.value("search_history", [])  # 搜索历史
        print(f"加载的配置: categories={self.categories}, tools={len(self.tools)}")
    
    def save_config(self):
        """保存配置"""
        print("保存配置...")
        self.settings.setValue("categories", self.categories)
        self.settings.setValue("tools", self.tools)
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("view_mode", self.view_mode)
        self.settings.setValue("favorites", self.favorites)
        self.settings.setValue("recent_tools", self.recent_tools)
        self.settings.setValue("show_status_bar", self.show_status_bar)
        self.settings.setValue("auto_refresh", self.auto_refresh)
        self.settings.setValue("search_history", self.search_history)
        self.settings.sync()
    
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

print("定义配置类完成...")

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

print("定义工具类完成...")

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
        self.webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))
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
        self.setWindowTitle("添加工具")
        self.setMinimumWidth(600)
        self.categories = categories
        
        # 设置对话框特定样式，确保按钮可见
        self.setStyleSheet("""
            QDialog {
                background: #ffffff;
                color: #2c3e50;
                font-family: 'Microsoft YaHei', '微软雅黑', Arial;
            }
            QLineEdit, QTextEdit, QComboBox {
                background: #f8f9fa;
                color: #2c3e50;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border: 2px solid #007bff;
                background: #ffffff;
            }
            QPushButton {
                background: linear-gradient(135deg, #007bff, #0056b3);
                color: #ffffff;
                border-radius: 8px;
                padding: 10px 16px;
                font-weight: bold;
                font-size: 13px;
                border: none;
                min-width: 80px;
            }
            QPushButton:hover {
                background: linear-gradient(135deg, #0056b3, #004085);
            }
            QPushButton:pressed {
                background: linear-gradient(135deg, #004085, #002752);
            }
            QPushButton:disabled {
                background: #6c757d;
                color: #ffffff;
            }
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                font-size: 13px;
            }
            QDialogButtonBox QPushButton {
                min-width: 100px;
                margin: 5px;
            }
        """)
        
        layout = QFormLayout(self)
        
        # 工具名称
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("请输入工具名称")
        layout.addRow("工具名称:", self.name_edit)
        
        # 工具类型
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            "GUI应用", "命令行", "java8图形化", "java11图形化", 
            "java8", "java11", "python", "powershell", "批处理", "网页", "文件夹"
        ])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        layout.addRow("工具类型:", self.type_combo)
        
        # 工具路径
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("请输入工具路径或URL")
        self.path_btn = QPushButton("浏览...")
        self.path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.path_btn)
        layout.addRow("工具路径:", path_layout)
        
        # 图标选择
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit()
        self.icon_edit.setPlaceholderText("选择图标文件（可选）")
        self.icon_btn = QPushButton("选择...")
        self.icon_btn.clicked.connect(self.browse_icon)
        icon_layout.addWidget(self.icon_edit)
        icon_layout.addWidget(self.icon_btn)
        layout.addRow("图标选择:", icon_layout)
        
        # 工具分类
        self.category_combo = QComboBox()
        self.category_combo.addItems(categories)
        self.category_combo.setEditable(True)
        layout.addRow("工具分类:", self.category_combo)
        
        # 工具启动参数
        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("请输入启动参数（可选）")
        layout.addRow("启动参数:", self.args_edit)
        
        # 工具描述
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(100)
        self.desc_edit.setPlaceholderText("请输入工具描述（可选）")
        layout.addRow("工具描述:", self.desc_edit)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal, self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
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

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        print("初始化主窗口...")
        super().__init__()
        self.config = Config()
        self.init_ui()
        self.load_data()
        print("主窗口初始化完成")
    
    def init_ui(self):
        """初始化界面"""
        print("开始初始化界面...")
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
        splitter.setHandleWidth(1)  # 设置分割线宽度为1像素
        splitter.setChildrenCollapsible(False)  # 防止子部件被完全折叠
        layout.addWidget(splitter)
        
        # 左侧面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)  # 减少边距
        left_layout.setSpacing(5)  # 减少间距
        
        # 分类树
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderLabel("")
        self.category_tree.setMinimumWidth(200)
        self.category_tree.setMaximumWidth(300)
        self.category_tree.itemClicked.connect(self.on_category_clicked)
        self.category_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.category_tree.customContextMenuRequested.connect(self.show_category_context_menu)
        left_layout.addWidget(self.category_tree)
        
        # 右侧面板
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距，让内容占满整个区域
        right_layout.setSpacing(0)  # 移除间距
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工具...")
        self.search_input.textChanged.connect(self.search_tools)
        right_layout.addWidget(self.search_input)
        
        # 创建堆叠式布局
        self.right_stack = QStackedWidget()
        self.right_stack.setContentsMargins(0, 0, 0, 0)  # 移除边距
        right_layout.addWidget(self.right_stack)
        
        # 工具列表页面
        self.tools_page = QWidget()
        tools_layout = QVBoxLayout(self.tools_page)
        tools_layout.setContentsMargins(5, 5, 5, 5)  # 保持工具列表的边距
        tools_layout.setSpacing(5)  # 保持工具列表的间距
        
        # 工具列表/网格
        self.tools_widget = QWidget()
        self.tools_layout = QVBoxLayout(self.tools_widget)
        self.tools_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        
        # 使用QListWidget，一行一个工具
        self.tools_list = QListWidget()
        self.tools_list.setViewMode(QListWidget.ViewMode.ListMode)
        self.tools_list.setSpacing(4)  # 设置间距
        self.tools_list.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.tools_list.setMovement(QListWidget.Movement.Static)
        self.tools_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tools_list.customContextMenuRequested.connect(self.show_context_menu)
        self.tools_list.itemDoubleClicked.connect(self.launch_tool)
        
        # 设置样式
        self.tools_list.setStyleSheet("""
            QListWidget {
                background: #ffffff;
                border: 1px solid #e1e8ed;
                border-radius: 8px;
                outline: none;
                padding: 8px;
            }
            QListWidget::item {
                background: #ffffff;
                border: 1px solid #e1e8ed;
                border-radius: 6px;
                padding: 8px;
                margin: 2px;
                min-height: 50px;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                border: 1px solid #1da1f2;
            }
            QListWidget::item:hover {
                background: #f8f9fa;
                border: 1px solid #1da1f2;
            }
        """)
        
        self.tools_layout.addWidget(self.tools_list)
        
        # 添加分页控件
        pagination_widget = QWidget()
        pagination_layout = QHBoxLayout(pagination_widget)
        pagination_layout.setContentsMargins(5, 5, 5, 5)
        
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self.prev_page)
        self.prev_btn.setEnabled(False)
        
        self.page_label = QLabel("第 1 / 1 页   共 0 个工具")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        
        self.tools_layout.addWidget(pagination_widget)
        tools_layout.addWidget(self.tools_widget)
        
        # CyberChef页面
        self.cyberchef_page = QWidget()
        cyberchef_layout = QVBoxLayout(self.cyberchef_page)
        cyberchef_layout.setContentsMargins(0, 0, 0, 0)  # 移除边距，让CyberChef占满整个区域
        cyberchef_layout.setSpacing(0)  # 移除间距
        self.cyberchef_webview = QWebEngineView()
        self.cyberchef_webview.setMinimumSize(800, 600)  # 设置最小尺寸
        
        # 设置CyberChef文件夹路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        cyberchef_dir = os.path.join(current_dir, "CyberChef")
        index_path = os.path.join(cyberchef_dir, "index.html")
        
        print(f"当前目录: {current_dir}")
        print(f"CyberChef目录: {cyberchef_dir}")
        print(f"index.html路径: {index_path}")
        print(f"CyberChef目录是否存在: {os.path.exists(cyberchef_dir)}")
        print(f"index.html是否存在: {os.path.exists(index_path)}")
        
        # 检查并加载CyberChef
        if os.path.exists(index_path):
            print(f"正在加载本地CyberChef: {index_path}")
            url = QUrl.fromLocalFile(index_path)
            print(f"加载URL: {url.toString()}")
            self.cyberchef_webview.setUrl(url)
        else:
            print("未找到本地CyberChef，使用在线版本")
            self.cyberchef_webview.setUrl(QUrl("https://gchq.github.io/CyberChef/"))
        
        # 连接加载完成信号
        self.cyberchef_webview.loadFinished.connect(self.on_cyberchef_loaded)
        
        cyberchef_layout.addWidget(self.cyberchef_webview)
        
        # 添加页面到堆叠式布局
        self.right_stack.addWidget(self.tools_page)
        self.right_stack.addWidget(self.cyberchef_page)
        
        # 添加到分割器
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置样式
        self.apply_theme()
        print("界面初始化完成")
    
    def create_menu(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("文件")
        
        add_tool_action = QAction("添加工具", self)
        add_tool_action.setShortcut(QKeySequence("Ctrl+N"))
        add_tool_action.triggered.connect(self.add_tool)
        file_menu.addAction(add_tool_action)
        
        add_category_action = QAction("添加分类", self)
        add_category_action.setShortcut(QKeySequence("Ctrl+Shift+N"))
        add_category_action.triggered.connect(self.add_category)
        file_menu.addAction(add_category_action)
        
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
        
        theme_menu.addSeparator()
        
        # 经典主题
        classic_light_action = QAction("☀️ 经典浅色", self)
        classic_light_action.triggered.connect(partial(self.set_theme, "light"))
        theme_menu.addAction(classic_light_action)
        
        classic_dark_action = QAction("🌑 经典深色", self)
        classic_dark_action.triggered.connect(partial(self.set_theme, "dark"))
        theme_menu.addAction(classic_dark_action)
        
        theme_menu.addSeparator()
        
        # 特殊主题
        elegant_action = QAction("✨ 优雅主题", self)
        elegant_action.triggered.connect(partial(self.set_theme, "elegant"))
        theme_menu.addAction(elegant_action)
        
        cyber_action = QAction("🤖 赛博朋克", self)
        cyber_action.triggered.connect(partial(self.set_theme, "cyber"))
        theme_menu.addAction(cyber_action)
        
        minimal_action = QAction("📝 极简风格", self)
        minimal_action.triggered.connect(partial(self.set_theme, "minimal"))
        theme_menu.addAction(minimal_action)
        
        soft_action = QAction("🌸 柔和主题", self)
        soft_action.triggered.connect(partial(self.set_theme, "soft"))
        theme_menu.addAction(soft_action)
        
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
        
        # 收藏工具
        favorites_action = QAction("收藏工具", self)
        favorites_action.triggered.connect(self.show_favorites)
        stats_menu.addAction(favorites_action)
        
        stats_menu.addSeparator()
        
        # 刷新统计
        refresh_stats_action = QAction("刷新统计", self)
        refresh_stats_action.setShortcut(QKeySequence("F5"))
        refresh_stats_action.triggered.connect(self.refresh_data)
        stats_menu.addAction(refresh_stats_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu("帮助")
        
        about_action = QAction("关于", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
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
        """刷新数据"""
        self.update_status_stats()
        current_item = self.category_tree.currentItem()
        if current_item:
            self.update_tools_list(current_item.text(0))
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
        """显示关于对话框"""
        QMessageBox.about(self, "关于 AppLauncher", 
                         "AppLauncher - 智能程序启动与编码助手\n\n"
                         "版本: 2.0\n"
                         "功能: 工具管理、分类组织、快速启动、CyberChef集成\n\n"
                         "支持多种工具类型:\n"
                         "• GUI应用、命令行工具\n"
                         "• Java、Python、PowerShell脚本\n"
                         "• 网页链接、文件夹\n"
                         "• 批处理文件\n\n"
                         "快捷键:\n"
                         "• Ctrl+N: 添加工具\n"
                         "• Ctrl+F: 搜索\n"
                         "• F5: 刷新\n"
                         "• F11: 全屏切换\n\n"
                         "开发者:\n"
                         "• GitHub: https://github.com/z50n6")
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态信息标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
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
        """加载数据"""
        self.update_category_tree()
        self.current_page = 1
        self.update_tools_list()
    
    def update_category_tree(self):
        """更新分类树"""
        self.category_tree.clear()
        # 只显示一级分类，不显示子分类
        for category in self.config.categories:
            item = QTreeWidgetItem([category])
            item.setFont(0, QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
            self.category_tree.addTopLevelItem(item)
    
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
            "java8": "☕",
            "java11": "☕",
            "python": "🐍",
            "powershell": "💻",
            "batch": "📜",
            "url": "🌐",
            "folder": "📁",
            "placeholder": "📂"
        }
        return icon_map.get(tool.tool_type, "🔧")
    
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
        print(f"点击分类: {category_name}")
        if category_name == "编码与解码":
            print("切换到CyberChef页面")
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
    
    def launch_tool(self, item):
        """启动工具"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        # 如果是占位符工具，提示用户
        if tool.tool_type == "placeholder":
            QMessageBox.information(self, "提示", "这是一个空分类的占位符，请添加实际工具到此分类。")
            return
            
        try:
            if tool.tool_type == "url":
                # 网页类型
                QDesktopServices.openUrl(QUrl(tool.path))
            elif tool.tool_type == "folder":
                # 文件夹类型
                QDesktopServices.openUrl(QUrl.fromLocalFile(tool.path))
            elif tool.tool_type in ["java8_gui", "java11_gui"]:
                # Java图形化应用
                java_cmd = "java" if tool.tool_type == "java8_gui" else "java"
                cmd = [java_cmd, "-jar", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type in ["java8", "java11"]:
                # Java命令行应用
                java_cmd = "java" if tool.tool_type == "java8" else "java"
                cmd = [java_cmd, "-jar", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type == "python":
                # Python脚本
                cmd = ["python", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type == "powershell":
                # PowerShell脚本
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type == "batch":
                # 批处理文件
                cmd = [tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            else:
                # 默认可执行文件
                cmd = [tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            
            # 更新启动次数和最后启动时间
            tool.launch_count += 1
            tool.last_launch = datetime.now().isoformat()
            
            # 添加到最近使用
            self.config.add_to_recent(tool.name)
            
            # 保存配置并更新界面
            self.config.save_config()
            self.update_status_stats()
            
            # 更新状态栏
            self.status_label.setText(f"已启动: {tool.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
            self.status_label.setText(f"启动失败: {tool.name}")
    
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
                print(f"编辑时添加新分类: {new_category}")
            
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
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config.tools.remove(tool.to_dict())
            self.config.save_config()
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def open_tool_folder(self, item):
        """打开工具所在文件夹"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        path = os.path.dirname(tool.path)
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    
    def open_tool_cmd(self, item):
        """打开工具命令行"""
        tool = item.data(Qt.ItemDataRole.UserRole)
        if not tool:
            return
            
        path = os.path.dirname(tool.path)
        if os.path.exists(path):
            subprocess.Popen(["cmd", "/k", f"cd /d {path}"])
    
    def show_cyberchef(self):
        """显示CyberChef"""
        self.right_stack.setCurrentWidget(self.cyberchef_page)
    
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
            QPushButton { 
                background: linear-gradient(135deg, #1da1f2, #0d8bd9); color: #ffffff; 
                border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px;
                border: none;
            }
            QPushButton:hover { 
                background: linear-gradient(135deg, #0d8bd9, #0c7bb8); 
            }
            QPushButton:pressed { 
                background: linear-gradient(135deg, #0c7bb8, #0b6aa7); 
            }
            QSplitter::handle { background: #e1e8ed; border-radius: 1px; }
            QListWidget { 
                background: #ffffff; 
                border: 1px solid #e1e8ed; 
                border-radius: 8px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #ffffff; 
                border: 1px solid #e1e8ed; 
                border-radius: 8px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: linear-gradient(135deg, #1da1f2, #0d8bd9); 
                color: #ffffff; 
                border: 1px solid #0d8bd9;
            }
            QListWidget::item:hover { 
                background: #f7f9fa; 
                border: 1px solid #1da1f2; 
                transform: translateY(-2px);
            }
            QListWidget::item:alternate { 
                background: #fafbfc; 
            }
            QListWidget::item:alternate:hover { 
                background: #f0f4f8; 
            }
            QStatusBar { background: #ffffff; color: #657786; border-top: 1px solid #e1e8ed; }
            QMenuBar { background: #ffffff; color: #2c3e50; border-bottom: 1px solid #e1e8ed; }
            QMenuBar::item:selected { background: #f7f9fa; border-radius: 4px; }
            QMenu { background: #ffffff; color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 6px; padding: 4px; }
            QMenu::item:selected { background: #f7f9fa; border-radius: 4px; }
            QDialog { background: #fafbfc; }
            QDialog QPushButton { 
                background: linear-gradient(135deg, #1da1f2, #0d8bd9); color: #ffffff; 
                border-radius: 6px; padding: 8px 16px; font-weight: 600; font-size: 13px;
                border: none; min-width: 80px;
            }
            QDialog QPushButton:hover { 
                background: linear-gradient(135deg, #0d8bd9, #0c7bb8); 
            }
            QDialog QPushButton:pressed { 
                background: linear-gradient(135deg, #0c7bb8, #0b6aa7); 
            }
            QDialog QLineEdit, QDialog QTextEdit, QDialog QComboBox {
                background: #ffffff; color: #2c3e50; border: 1px solid #e1e8ed; border-radius: 6px;
                padding: 8px; font-size: 13px;
            }
            QDialog QLineEdit:focus, QDialog QTextEdit:focus, QDialog QComboBox:focus {
                border: 2px solid #1da1f2; background: #ffffff;
            }
            QDialog QLabel { color: #2c3e50; font-weight: 600; font-size: 13px; }
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
            QPushButton { 
                background: linear-gradient(135deg, #00d4ff, #0099cc); color: #ffffff; 
                border-radius: 8px; padding: 10px 16px; font-weight: bold; font-size: 13px;
                border: none;
            }
            QPushButton:hover { 
                background: linear-gradient(135deg, #0099cc, #006699); 
                transform: translateY(-1px);
            }
            QPushButton:pressed { 
                background: linear-gradient(135deg, #006699, #004466); 
                transform: translateY(0px);
            }
            QSplitter::handle { background: #404040; border-radius: 2px; }
            QListWidget { 
                background: #2d2d2d; 
                border: 2px solid #404040; 
                border-radius: 8px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #2d2d2d; 
                border: 1px solid #404040; 
                border-radius: 8px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: linear-gradient(135deg, #00d4ff, #0099cc); 
                color: #ffffff; 
                border: 1px solid #0099cc;
            }
            QListWidget::item:hover { 
                background: #333333; 
                border: 1px solid #00d4ff; 
                transform: translateY(-2px);
            }
            QListWidget::item:alternate { 
                background: #333333; 
            }
            QListWidget::item:alternate:hover { 
                background: #383838; 
            }
            QStatusBar { background: #2d2d2d; color: #b0b0b0; border-top: 1px solid #404040; }
            QMenuBar { background: #1a1a1a; color: #e0e0e0; border-bottom: 1px solid #404040; }
            QMenuBar::item:selected { background: #333333; border-radius: 4px; }
            QMenu { background: #2d2d2d; color: #e0e0e0; border: 1px solid #404040; border-radius: 8px; padding: 4px; }
            QMenu::item:selected { background: #333333; border-radius: 4px; }
            """
        elif theme == "elegant":
            qss = """
            QMainWindow { background: #fafafa; }
            QWidget { background: #fafafa; color: #2c3e50; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #ffffff; color: #2c3e50; border: 1px solid #d1d5db; border-radius: 6px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 1px solid #8b5cf6; background: #ffffff; 
            }
            QPushButton { 
                background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: #ffffff; 
                border-radius: 6px; padding: 8px 16px; font-weight: 500; font-size: 13px;
                border: none;
            }
            QPushButton:hover { 
                background: linear-gradient(135deg, #7c3aed, #6d28d9); 
            }
            QSplitter::handle { background: #e5e7eb; border-radius: 1px; }
            QListWidget { 
                background: #ffffff; 
                border: 1px solid #d1d5db; 
                border-radius: 8px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #ffffff; 
                border: 1px solid #d1d5db; 
                border-radius: 8px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: linear-gradient(135deg, #8b5cf6, #7c3aed); 
                color: #ffffff; 
                border: 1px solid #7c3aed;
            }
            QListWidget::item:hover { 
                background: #f3f4f6; 
                border: 1px solid #8b5cf6; 
                transform: translateY(-2px);
            }
            QListWidget::item:alternate { 
                background: #fafafa; 
            }
            QListWidget::item:alternate:hover { 
                background: #f0f0f0; 
            }
            QStatusBar { background: #ffffff; color: #6b7280; border-top: 1px solid #e5e7eb; }
            QMenuBar { background: #ffffff; color: #2c3e50; border-bottom: 1px solid #e5e7eb; }
            QMenuBar::item:selected { background: #f3f4f6; border-radius: 4px; }
            QMenu { background: #ffffff; color: #2c3e50; border: 1px solid #e5e7eb; border-radius: 6px; padding: 4px; }
            QMenu::item:selected { background: #f3f4f6; border-radius: 4px; }
            """
        elif theme == "cyber":
            qss = """
            QMainWindow { background: #0a0a0a; }
            QWidget { background: #0a0a0a; color: #00ff00; font-family: 'Consolas', 'Microsoft YaHei', monospace; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { 
                background: #1a1a1a; color: #00ff00; border: 2px solid #00ff00; border-radius: 4px; 
                padding: 8px; font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { 
                border: 2px solid #00ffff; background: #1a1a1a; 
            }
            QPushButton { 
                background: linear-gradient(135deg, #00ff00, #00cc00); color: #000000; 
                border-radius: 4px; padding: 8px 16px; font-weight: bold; font-size: 13px;
                border: 1px solid #00ff00;
            }
            QPushButton:hover { 
                background: linear-gradient(135deg, #00ffff, #00cccc); color: #000000; 
                border: 1px solid #00ffff;
            }
            QSplitter::handle { background: #00ff00; border-radius: 1px; }
            QListWidget { 
                background: #1a1a1a; 
                border: 2px solid #00ff00; 
                border-radius: 6px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #1a1a1a; 
                border: 1px solid #00ff00; 
                border-radius: 4px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: linear-gradient(135deg, #00ff00, #00cc00); 
                color: #000000; 
                border: 1px solid #00ff00;
            }
            QListWidget::item:hover { 
                background: #2a2a2a; 
                border: 1px solid #00ffff; 
                transform: translateY(-2px);
            }
            QListWidget::item:alternate { 
                background: #222222; 
            }
            QListWidget::item:alternate:hover { 
                background: #2a2a2a; 
            }
            QStatusBar { background: #1a1a1a; color: #00ff00; border-top: 1px solid #00ff00; }
            QMenuBar { background: #0a0a0a; color: #00ff00; border-bottom: 1px solid #00ff00; }
            QMenuBar::item:selected { background: #1a1a1a; border-radius: 2px; }
            QMenu { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; border-radius: 4px; padding: 4px; }
            QMenu::item:selected { background: #2a2a2a; border-radius: 2px; }
            """
        elif theme == "light":
            qss = """
            QMainWindow { background: #f8f9fa; }
            QWidget { background: #f8f9fa; color: #222; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { background: #fff; color: #222; border-radius: 6px; }
            QPushButton { background: #3498db; color: #fff; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background: #2980b9; }
            QSplitter::handle { background: #e9ecef; }
            QListWidget { 
                background: #ffffff; 
                border: 1px solid #e9ecef; 
                border-radius: 6px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #ffffff; 
                border: 1px solid #e9ecef; 
                border-radius: 6px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: #3498db; 
                color: #fff; 
                border: 1px solid #2980b9;
            }
            QListWidget::item:hover { 
                background: #e3f2fd; 
                border: 1px solid #bbdefb; 
            }
            QListWidget::item:alternate { 
                background: #fafafa; 
            }
            QListWidget::item:alternate:hover { 
                background: #e8f4fd; 
            }
            """
        elif theme == "dark":
            qss = """
            QMainWindow { background: #23272e; }
            QWidget { background: #23272e; color: #e0e0e0; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { background: #2c3e50; color: #e0e0e0; border-radius: 6px; }
            QPushButton { background: #2980b9; color: #fff; border-radius: 6px; padding: 6px 12px; }
            QPushButton:hover { background: #3498db; }
            QSplitter::handle { background: #444; }
            QTreeWidget { 
                background: #2c3e50; 
                border: 1px solid #34495e; 
                border-radius: 6px;
                outline: none;
            }
            QTreeWidget::item { 
                padding: 10px 12px; 
                margin: 2px 6px; 
                border-radius: 6px; 
                background: #2c3e50; 
                border: 1px solid transparent;
                min-height: 18px;
            }
            QTreeWidget::item:selected { 
                background: #3498db; 
                color: #fff; 
                border: 1px solid #2980b9;
            }
            QTreeWidget::item:hover { 
                background: #34495e; 
                border: 1px solid #4a5f7a; 
            }
            QTreeWidget::item:alternate { 
                background: #34495e; 
            }
            QTreeWidget::item:alternate:hover { 
                background: #3d5a7a; 
            }
            QTreeWidget::branch:has-children:!has-siblings:closed, QTreeWidget::branch:closed:has-children:has-siblings { image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDZMMTAgNkw2IDEwTDQgNloiIGZpbGw9IiNlMGUwZTAiLz4KPC9zdmc+); }
            QTreeWidget::branch:open:has-children:!has-siblings, QTreeWidget::branch:open:has-children:has-siblings { image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw4IDZMMTAgNkw2IDEwTDQgNloiIGZpbGw9IiNlMGUwZTAiIHRyYW5zZm9ybT0icm90YXRlKDkwKSIvPgo8L3N2Zz4=); }
            """
        elif theme == "soft":
            qss = """
            QMainWindow { background: #f6f5f3; }
            QWidget { background: #f6f5f3; color: #444; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { background: #fff8e1; color: #444; border-radius: 8px; border: 1px solid #ffe0b2; }
            QPushButton { background: #ffd180; color: #6d4c41; border-radius: 8px; padding: 6px 12px; }
            QPushButton:hover { background: #ffe0b2; }
            QSplitter::handle { background: #ffe0b2; }
            QListWidget { 
                background: #fff8e1; 
                border: 1px solid #ffe0b2; 
                border-radius: 8px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #fff8e1; 
                border: 1px solid #ffe0b2; 
                border-radius: 8px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: #ffd180; 
                color: #6d4c41; 
                border: 1px solid #ffb74d;
            }
            QListWidget::item:hover { 
                background: #fff3e0; 
                border: 1px solid #ffe0b2; 
            }
            QListWidget::item:alternate { 
                background: #fffde7; 
            }
            QListWidget::item:alternate:hover { 
                background: #fff8e1; 
            }
            """
        elif theme == "minimal":
            qss = """
            QMainWindow { background: #fff; }
            QWidget { background: #fff; color: #222; font-family: 'Microsoft YaHei', '微软雅黑', Arial; }
            QLineEdit, QTextEdit, QComboBox, QMenu, QListWidget, QTreeWidget { background: #fff; color: #222; border: 1px solid #eee; border-radius: 4px; }
            QPushButton { background: #eee; color: #222; border-radius: 4px; padding: 6px 12px; }
            QPushButton:hover { background: #e0e0e0; }
            QSplitter::handle { background: #eee; }
            QListWidget { 
                background: #ffffff; 
                border: 1px solid #eee; 
                border-radius: 4px;
                outline: none;
                padding: 10px;
            }
            QListWidget::item { 
                background: #ffffff; 
                border: 1px solid #eee; 
                border-radius: 4px; 
                padding: 8px; 
                margin: 4px;
                min-height: 60px;
            }
            QListWidget::item:selected { 
                background: #f5f5f5; 
                color: #222; 
                border: 1px solid #ddd;
            }
            QListWidget::item:hover { 
                background: #fafafa; 
                border: 1px solid #eee; 
            }
            QListWidget::item:alternate { 
                background: #fafafa; 
            }
            QListWidget::item:alternate:hover { 
                background: #f5f5f5; 
            }
            """
        else:
            qss = ""
        self.setStyleSheet(qss)
    
    def export_config(self):
        """导出配置"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({
                        "categories": self.config.categories,
                        "tools": self.config.tools,
                        "theme": self.config.theme,
                        "view_mode": self.config.view_mode
                    }, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "成功", "配置导出成功")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def import_config(self):
        """导入配置"""
        path, _ = QFileDialog.getOpenFileName(
            self, "导入配置", "", "JSON文件 (*.json)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.config.categories = data.get("categories", [])
                self.config.tools = data.get("tools", [])
                self.config.theme = data.get("theme", "light")
                self.config.view_mode = data.get("view_mode", "list")
                self.config.save_config()
                self.load_data()
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
        """窗口大小变化事件"""
        super().resizeEvent(event)
        # 确保CyberChef页面能够正确适应窗口大小
        if self.right_stack.currentWidget() == self.cyberchef_page:
            self.cyberchef_webview.resize(self.cyberchef_page.size())

    def on_cyberchef_loaded(self, success):
        """CyberChef加载完成后的处理"""
        if success:
            print("CyberChef加载成功")
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
            print("CyberChef加载失败")
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
                print(f"添加新分类: {new_category}")
            
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
        """显示总工具数统计"""
        total_tools = len(self.config.tools)
        total_categories = len(self.config.categories)
        total_launches = sum(tool.get("launch_count", 0) for tool in self.config.tools)
        
        stats_text = f"📊 工具统计\n\n"
        stats_text += f"总工具数: {total_tools}\n"
        stats_text += f"总分类数: {total_categories}\n"
        stats_text += f"总启动次数: {total_launches}\n"
        
        if total_tools > 0:
            avg_launches = total_launches / total_tools
            stats_text += f"平均启动次数: {avg_launches:.1f}\n"
        
        QMessageBox.information(self, "工具统计", stats_text)
    
    def show_recent_tools(self):
        """显示最近启动的工具"""
        if not self.config.recent_tools:
            QMessageBox.information(self, "最近启动的工具", "暂无最近启动的工具")
            return
        
        # 创建对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("🕒 最近启动的工具")
        dialog.setMinimumSize(400, 300)
        dialog.setModal(True)
        
        # 创建布局
        layout = QVBoxLayout(dialog)
        
        # 创建说明标签
        info_label = QLabel("点击工具名称可直接启动")
        info_label.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 10px;")
        layout.addWidget(info_label)
        
        # 创建工具列表
        list_widget = QListWidget()
        list_widget.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
            }
            QListWidget::item:hover {
                background-color: #f0f8ff;
            }
            QListWidget::item:selected {
                background-color: #e6f3ff;
                color: black;
            }
        """)
        
        # 添加最近使用的工具
        for i, tool_name in enumerate(self.config.recent_tools[:20], 1):  # 显示最近20个
            item = QListWidgetItem(f"{i:2d}. 📱 {tool_name}")
            item.setData(Qt.ItemDataRole.UserRole, tool_name)  # 存储工具名称
            list_widget.addItem(item)
        
        # 连接双击事件
        list_widget.itemDoubleClicked.connect(lambda item: self.launch_recent_tool(item, dialog))
        
        layout.addWidget(list_widget)
        
        # 创建按钮
        button_layout = QHBoxLayout()
        
        close_button = QPushButton("关闭")
        close_button.clicked.connect(dialog.accept)
        button_layout.addWidget(close_button)
        
        clear_button = QPushButton("清空历史")
        clear_button.clicked.connect(lambda: self.clear_recent_history(dialog))
        button_layout.addWidget(clear_button)
        
        layout.addLayout(button_layout)
        
        # 显示对话框
        dialog.exec()
    
    def launch_recent_tool(self, item, dialog):
        """启动最近使用的工具"""
        tool_name = item.data(Qt.ItemDataRole.UserRole)
        if tool_name:
            # 查找对应的工具
            for tool_data in self.config.tools:
                if tool_data["name"] == tool_name:
                    tool = Tool.from_dict(tool_data)
                    try:
                        # 启动工具
                        self._execute_tool(tool)
                        # 更新最近使用记录
                        self.config.add_to_recent(tool_name)
                        self.config.save_config()
                        # 关闭对话框
                        dialog.accept()
                        self.status_label.setText(f"已启动: {tool_name}")
                        return
                    except Exception as e:
                        QMessageBox.warning(self, "启动失败", f"启动工具 '{tool_name}' 失败:\n{str(e)}")
                        return
            
            QMessageBox.warning(self, "工具不存在", f"工具 '{tool_name}' 已不存在")
    
    def clear_recent_history(self, dialog):
        """清空最近使用历史"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空最近使用历史吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.config.recent_tools.clear()
            self.config.save_config()
            dialog.accept()
            QMessageBox.information(self, "清空完成", "最近使用历史已清空")
    
    def _execute_tool(self, tool):
        """执行工具启动"""
        import subprocess
        import os
        
        if tool.tool_type == "exe":
            # 可执行文件
            if tool.args:
                subprocess.Popen([tool.path] + tool.args.split())
            else:
                subprocess.Popen([tool.path])
        elif tool.tool_type == "java":
            # Java程序
            cmd = ["java", "-jar", tool.path]
            if tool.args:
                cmd.extend(tool.args.split())
            subprocess.Popen(cmd)
        elif tool.tool_type == "python":
            # Python脚本
            cmd = ["python", tool.path]
            if tool.args:
                cmd.extend(tool.args.split())
            subprocess.Popen(cmd)
        elif tool.tool_type == "powershell":
            # PowerShell脚本
            cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", tool.path]
            if tool.args:
                cmd.extend(tool.args.split())
            subprocess.Popen(cmd)
        elif tool.tool_type == "url":
            # 网页链接
            import webbrowser
            webbrowser.open(tool.path)
        elif tool.tool_type == "folder":
            # 文件夹
            os.startfile(tool.path)
        elif tool.tool_type == "batch":
            # 批处理文件
            subprocess.Popen([tool.path], shell=True)
        else:
            # 默认作为可执行文件处理
            subprocess.Popen([tool.path])
    
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
        """搜索工具"""
        self.tools_list.clear()
        
        if not text:
            # 如果没有搜索文本，显示当前选中分类的工具
            current_item = self.category_tree.currentItem()
            if current_item:
                category_name = current_item.text(0)
                if category_name != "编码与解码":
                    self.update_tools_list(category_name)
            return
        
        # 搜索所有工具
        for tool_data in self.config.tools:
            tool = Tool.from_dict(tool_data)
            if (text.lower() in tool.name.lower() or
                text.lower() in tool.description.lower() or
                text.lower() in tool.category.lower() or
                text.lower() in tool.subcategory.lower()):
                
                # 创建搜索结果的工具项
                self._create_search_tool_item(tool)
    
    def _create_search_tool_item(self, tool):
        """创建搜索结果的工具项"""
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
    
    def launch_tool_card(self, tool):
        """启动工具卡片"""
        try:
            if tool.tool_type == "url":
                # 网页类型
                QDesktopServices.openUrl(QUrl(tool.path))
            elif tool.tool_type == "folder":
                # 文件夹类型
                QDesktopServices.openUrl(QUrl.fromLocalFile(tool.path))
            elif tool.tool_type in ["java8_gui", "java11_gui"]:
                # Java图形化应用
                java_cmd = "java" if tool.tool_type == "java8_gui" else "java"
                cmd = [java_cmd, "-jar", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type in ["java8", "java11"]:
                # Java命令行应用
                java_cmd = "java" if tool.tool_type == "java8" else "java"
                cmd = [java_cmd, "-jar", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type == "python":
                # Python脚本
                cmd = ["python", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type == "powershell":
                # PowerShell脚本
                cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            elif tool.tool_type == "batch":
                # 批处理文件
                cmd = [tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            else:
                # 默认可执行文件
                cmd = [tool.path]
                if tool.args:
                    cmd.extend(tool.args.split())
                subprocess.Popen(cmd)
            
            # 更新启动次数和最后启动时间
            tool.launch_count += 1
            tool.last_launch = datetime.now().isoformat()
            
            # 添加到最近使用
            self.config.add_to_recent(tool.name)
            
            # 保存配置并更新界面
            self.config.save_config()
            self.update_status_stats()
            
            # 更新状态栏
            self.status_label.setText(f"已启动: {tool.name}")
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动失败: {str(e)}")
            self.status_label.setText(f"启动失败: {tool.name}")
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.tools_list.itemAt(position)
        if not item:
            return
        
        menu = QMenu()
        
        # 工具节点
        tool = item.data(Qt.ItemDataRole.UserRole)
        if tool and tool.tool_type == "placeholder":
            # 占位符工具，显示特殊菜单
            add_tool_action = QAction("添加工具到此分类", self)
            add_tool_action.triggered.connect(partial(self.add_tool_to_subcategory, tool.subcategory))
            menu.addAction(add_tool_action)
            
            delete_action = QAction("删除此空分类", self)
            delete_action.triggered.connect(partial(self.delete_placeholder_subcategory, tool))
            menu.addAction(delete_action)
        else:
            # 普通工具，显示完整的工具菜单
            launch_action = QAction("启动", self)
            launch_action.triggered.connect(partial(self.launch_tool, item))
            menu.addAction(launch_action)
            
            # 收藏功能
            if tool.name in self.config.favorites:
                unfavorite_action = QAction("取消收藏", self)
                unfavorite_action.triggered.connect(partial(self.remove_favorite, tool.name))
                menu.addAction(unfavorite_action)
            else:
                favorite_action = QAction("添加到收藏", self)
                favorite_action.triggered.connect(partial(self.add_favorite, tool.name))
                menu.addAction(favorite_action)
            
            menu.addSeparator()
            
            edit_action = QAction("编辑", self)
            edit_action.triggered.connect(partial(self.edit_tool, item))
            menu.addAction(edit_action)
            
            delete_action = QAction("删除", self)
            delete_action.triggered.connect(partial(self.delete_tool, item))
            menu.addAction(delete_action)
            
            menu.addSeparator()
            
            open_folder_action = QAction("打开所在文件夹", self)
            open_folder_action.triggered.connect(partial(self.open_tool_folder, item))
            menu.addAction(open_folder_action)
            
            open_cmd_action = QAction("打开命令行", self)
            open_cmd_action.triggered.connect(partial(self.open_tool_cmd, item))
            menu.addAction(open_cmd_action)
        
        menu.exec(self.tools_list.viewport().mapToGlobal(position))
    
    def edit_tool_card(self, tool):
        """编辑工具卡片"""
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
                print(f"编辑时添加新分类: {new_category}")
            
            # 更新工具数据
            index = self.config.tools.index(tool.to_dict())
            self.config.tools[index] = tool_data
            self.config.save_config()
            self.update_category_tree()  # 更新分类树
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def delete_tool_card(self, tool):
        """删除工具卡片"""
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工具 '{tool.name}' 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config.tools.remove(tool.to_dict())
            self.config.save_config()
            self.update_tools_list()  # 重新加载当前分类的工具
    
    def open_tool_folder_card(self, tool):
        """打开工具所在文件夹"""
        path = os.path.dirname(tool.path)
        if os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
    
    def open_tool_cmd_card(self, tool):
        """打开工具命令行"""
        path = os.path.dirname(tool.path)
        if os.path.exists(path):
            subprocess.Popen(["cmd", "/k", f"cd /d {path}"])
    
    def add_tool(self):
        """添加工具"""
        dialog = AddToolDialog(self.config.categories, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tool_data = dialog.get_tool_data()
            
            # 检查是否添加了新分类
            new_category = tool_data["category"]
            if new_category not in self.config.categories:
                self.config.categories.append(new_category)
                print(f"添加新分类: {new_category}")
            
            self.config.tools.append(tool_data)
            self.config.save_config()
            self.update_category_tree()  # 更新分类树
            
            # 如果当前选中的是工具所属的分类，则刷新工具列表
            current_item = self.category_tree.currentItem()
            if current_item and current_item.text(0) == tool_data["category"]:
                self.update_tools_list(tool_data["category"])
    
    def add_category(self):
        """添加分类"""
        category, ok = QInputDialog.getText(
            self, "添加分类", "请输入分类名称:"
        )
        if ok and category:
            if category not in self.config.categories:
                self.config.categories.append(category)
                self.config.save_config()
                self.update_category_tree()
            else:
                QMessageBox.warning(self, "错误", "该分类已存在")
    
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

if __name__ == "__main__":
    print("程序开始运行...")
    app = QApplication(sys.argv)
    print("创建 QApplication 实例...")
    window = MainWindow()
    print("创建主窗口...")
    window.show()
    print("显示主窗口...")
    sys.exit(app.exec()) 