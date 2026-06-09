# 插件开发规范

本文档指导开发者为本工具集框架编写插件，确保所有插件在架构、样式、交互上与框架保持一致。

---

## 1. 目录结构

```
plugins/
└── your_plugin/           # 目录名 = 插件目录名，小写下划线
    ├── __init__.py         # 空文件
    ├── plugin.json         # 元信息（必须）
    └── widget.py           # 插件主代码（推荐单一文件）
```

**规则：**
- 目录名使用小写字母 + 下划线，如 `batch_rename`、`pdf_merge`
- 每个插件一个目录，不允许跨目录依赖
- 不在 `plugins/` 根目录放代码文件

---

## 2. plugin.json 格式

```json
{
    "id": "batch_rename",
    "name": "批量改后缀",
    "category": "文档工具",
    "version": "1.0.0",
    "author": "dev",
    "description": "批量修改文件后缀名",
    "entry_point": "batch_rename.widget:BatchRenamePlugin"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 唯一标识，小写下划线，与目录名一致 |
| `name` | string | 显示名称，中文可 |
| `category` | string | 分类名，决定在侧边栏中的归属 |
| `version` | string | 语义化版本 |
| `author` | string | 作者 |
| `description` | string | 一句话描述 |
| `entry_point` | string | `模块路径:类名`，模块相对于 `plugins/` |

### 现有分类

| 分类名 | 图标 | 说明 |
|--------|------|------|
| 文档工具 | 📄 | 文件处理相关 |
| 图片工具 | 🖼️ | 图片处理相关 |
| 网络工具 | 🌐 | 网络相关 |
| 系统工具 | ⚙️ | 系统操作相关 |
| 示例工具 | 🧪 | 演示/测试用 |

如需新增分类，在 `app/main_window.py` 的 `CATEGORY_ICONS` 字典中添加映射。

---

## 3. 插件类规范

### 3.1 继承 BasePlugin

```python
from app.base_plugin import BasePlugin

class YourPlugin(BasePlugin):
    plugin_id = "your_plugin"        # 必须，与 plugin.json 的 id 一致
    plugin_name = "你的插件"          # 必须，与 plugin.json 的 name 一致
```

### 3.2 必须实现的方法

```python
def get_widget(self) -> QWidget:
    """返回主工作区组件（右侧下方）。框架只在首次切换到此插件时调用一次。"""
    ...
```

```python
def get_control_widget(self) -> Optional[QWidget]:
    """返回操作栏组件（右侧上方），可返回 None 表示不需要。"""
    ...
```

### 3.3 可选覆盖的生命周期方法

```python
def on_activate(self) -> None:
    """插件被切换到时调用。适合注册服务、连接事件。"""
    pass

def on_deactivate(self) -> None:
    """插件被切换走时调用。适合清理临时状态。"""
    pass
```

### 3.4 框架注入的属性

加载完成后，框架自动注入：

```python
self.manager    # PluginManager 实例 — 服务注册/查找、获取其他插件
self.event_bus  # EventBus 实例 — 事件发布/订阅
```

---

## 4. UI 开发规范

### 4.1 布局边距与间距

```python
# 主容器
root.setContentsMargins(24, 16, 24, 16)  # 左 上 右 下
root.setSpacing(12)                        # 垂直间距

# GroupBox 内部
inner.setContentsMargins(12, 10, 12, 8)
inner.setSpacing(6)
```

### 4.2 标题层级

```python
# 主标题（每个插件一个）
title = QLabel("✏️  批量改后缀")
title.setObjectName("title")        # → font-size: 20px; font-weight: bold

# 副标题 / 描述
subtitle = QLabel("选择目录或多选文件...")
subtitle.setObjectName("subtitle")  # → font-size: 13px; color: text_tertiary

# 区块标题（操作栏内）
section = QLabel("控制面板")
section.setObjectName("sectionTitle")  # → font-size: 14px; font-weight: bold
```

**不要**在插件代码中设置 `font-size`、`color`、`background` 等样式。
所有颜色、字体由主题系统 (`app/themes.py`) 统一控制。

### 4.3 按钮规范

```python
# 主操作按钮（强调色，每组最多 1-2 个）
btn = QPushButton("🚀 执行")
btn.setObjectName("primary")     # → accent 背景，白色文字

# 危险操作按钮
btn = QPushButton("🗑 删除")
btn.setObjectName("danger")      # → 红色背景

# 普通按钮（不设 objectName，使用默认样式）
btn = QPushButton("清空")

# 按钮高度
btn.setFixedHeight(30)           # 标准高度
btn.setFixedHeight(28)           # 紧凑模式（列表操作区）
```

### 4.4 输入控件

```python
# 文本输入
input = QLineEdit()
input.setPlaceholderText("提示文字")
input.setFixedHeight(30)

# 多行文本 / 日志输出
output = QTextEdit()
output.setReadOnly(True)

# 数字输入
spin = QSpinBox()
spin.setFixedHeight(30)
```

### 4.5 分组容器

```python
group = QGroupBox("后缀设置")
# 框架自动处理：边框、圆角、标题样式
```

---

## 5. 交互规范

### 5.1 长时间操作 → 加载状态

**必须**为超过 0.5 秒的操作提供视觉反馈：

```python
from app.utils.ui_helpers import ButtonSpinner

# 初始化（在 get_widget 中）
self._btn_exec = QPushButton("🚀 执行")
self._spinner = ButtonSpinner(self._btn_exec, "处理中", "🚀 执行")

# 操作开始时
self._spinner.start()     # 按钮禁用 + 显示转圈动画

# 操作结束时
self._spinner.stop("🚀 执行")   # 恢复可用 + 恢复文字
```

`ButtonSpinner` 的文字帧动画：`⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏`，100ms 一帧。

### 5.2 操作完成 → 打开文件/目录

操作产生文件输出后，提供访问入口：

```python
from app.utils.ui_helpers import open_in_file_manager, open_file

# 在文件管理器中打开所在目录（并选中文件）
open_in_file_manager(output_path)

# 用系统默认程序打开文件
open_file(output_path)

# UI 上：操作完成后显示按钮
self._btn_open_dir = QPushButton("📁 打开所在目录")
self._btn_open_dir.setVisible(False)           # 初始隐藏
self._btn_open_dir.clicked.connect(lambda: open_in_file_manager(path))
# 完成后:
self._btn_open_dir.setVisible(True)
```

### 5.3 危险操作 → 确认对话框

```python
reply = QMessageBox.question(
    None, "确认",
    "即将执行 XXX，确认？",
    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
)
if reply != QMessageBox.StandardButton.Yes:
    return
```

### 5.4 文件选择

```python
# 选择目录
d = QFileDialog.getExistingDirectory(None, "选择目录")

# 多选文件
files, _ = QFileDialog.getOpenFileNames(None, "选择文件", "", "PDF (*.pdf)")
```

---

## 6. 插件间通信

### 6.1 事件总线

```python
# 发布事件
self.event_bus.emit("event_name", {"key": "value"})

# 订阅事件（通常在 on_activate 中连接）
self.event_bus.event_triggered.connect(self._on_event)

def _on_event(self, event_name: str, data: dict) -> None:
    if event_name == "event_name":
        msg = data.get("key", "")
        ...
```

### 6.2 服务注册

```python
from app.services import ITextFormatter  # 预定义接口，或自定义 ABC

# 注册（在 on_activate 中）
self.manager.register_service(ITextFormatter, self._formatter_impl)

# 使用
formatter = self.manager.get_service(ITextFormatter)
if formatter:
    result = formatter.format_text("hello")
```

**约束：** 插件之间禁止直接 import，只通过 manager / event_bus 交互。

---

## 7. 日志

```python
from app.utils.logger import get_logger

logger = get_logger("YourPlugin")

logger.info("操作完成: %d 个文件", count)
logger.exception("操作失败")  # 自动记录异常堆栈
```

日志同时输出到控制台和 `logs/app.log`。

---

## 8. 异常处理

框架已对 `get_widget()` 和 `get_control_widget()` 做了 try-except 保护，
单个插件崩溃不会影响其他插件或主窗口。

但插件内部仍应自行处理预期异常：

```python
try:
    result = do_something()
except SpecificError as e:
    self._set_status(f"❌ {e}")
    logger.exception("操作失败")
    return
```

不要让未预期的异常静默吞掉——至少要 `logger.exception()` 记录。

---

## 9. 禁止事项

| ❌ 不允许 | ✅ 正确做法 |
|-----------|-------------|
| 在 widget 中硬编码 `color`、`background` 等样式 | 使用 `setObjectName()` 走主题系统 |
| 直接 import 其他插件模块 | 通过 `self.manager` / `self.event_bus` 交互 |
| 在 `get_widget()` 中执行耗时操作 | 在用户点击按钮后执行，配合 `ButtonSpinner` |
| 阻塞主线程（如 `time.sleep`） | 如需异步，用 `QThread` + `Signal` 回调 |
| 修改框架文件（`app/` 下的文件） | 只修改 `plugins/` 下自己的文件 |
| 在 `plugin.json` 中使用不在现有分类中的随意分类名 | 先在 `main_window.py` 的 `CATEGORY_ICONS` 中注册 |

---

## 10. 完整插件模板

```python
"""My Plugin 插件。"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from app.base_plugin import BasePlugin
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner

logger = get_logger("MyPlugin")


class MyPlugin(BasePlugin):
    plugin_id = "my_plugin"
    plugin_name = "我的插件"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._status_label: Optional[QLabel] = None
        self._btn_run: Optional[QPushButton] = None
        self._spinner: Optional[ButtonSpinner] = None

    def get_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # 标题
        title = QLabel("🔧  我的插件")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("插件功能描述")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        # 内容区 ...

        # 底部
        bottom = QHBoxLayout()
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        bottom.addWidget(self._status_label)
        bottom.addStretch()

        self._btn_run = QPushButton("🚀 运行")
        self._btn_run.setObjectName("primary")
        self._btn_run.setFixedHeight(30)
        self._btn_run.clicked.connect(self._on_run)
        bottom.addWidget(self._btn_run)

        self._spinner = ButtonSpinner(self._btn_run, "处理中", "🚀 运行")

        root.addLayout(bottom)
        self._widget = w
        return w

    def get_control_widget(self) -> Optional[QWidget]:
        return None

    def on_activate(self) -> None:
        logger.info("已激活")

    def on_deactivate(self) -> None:
        logger.info("已停用")

    def _on_run(self) -> None:
        self._spinner.start()
        try:
            # ... 业务逻辑 ...
            self._set_status("✅ 完成")
        except Exception as e:
            self._set_status(f"❌ {e}")
            logger.exception("运行失败")
        finally:
            self._spinner.stop()

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)
```
