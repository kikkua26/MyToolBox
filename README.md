# Python 插件化桌面工具集

基于 PySide6 的插件化桌面工具框架，支持多主题切换、分类展开/收起。

## 快速开始

```bash
cd my_toolbox
pip install -r requirements.txt
python main.py
```

## 目录结构

```
my_toolbox/
├── main.py                  # 入口
├── requirements.txt         # PySide6 + pypdf
├── app/
│   ├── main_window.py       # 主窗口（分类侧边栏 + 主题切换）
│   ├── plugin_manager.py    # 插件管理器（分类、服务注册）
│   ├── base_plugin.py       # 插件基类
│   ├── event_bus.py         # 全局事件总线
│   ├── services.py          # 服务接口
│   ├── themes.py            # 主题系统（设计令牌 + QSS 生成器）
│   └── utils/logger.py      # 统一日志
├── plugins/
│   ├── batch_rename/        # 📄 批量改后缀
│   ├── pdf_merge/           # 📄 PDF 合并
│   ├── hello_world/         # 🧪 示例：事件 & 服务
│   └── demo_service/        # 🧪 示例：服务注册
└── resources/icons/
```

## 主题

内置 3 套主题，底部下拉切换：

| 主题 | 风格 |
|------|------|
| 🌙 午夜蓝 | 深蓝夜空（默认） |
| 🧛 德古拉 | 紫暗吸血鬼 |
| ❄️ 北境 | 北极冷调 |

### 添加新主题

在 `app/themes.py` 的 `ThemeTokens` 中定义一组令牌，加入 `THEMES` 字典即可。
样式表从令牌自动派生，无需手写 QSS。

## 内置工具

### 📄 文档工具
- **批量改后缀** — 选择目录或多选文件，批量替换文件后缀
- **PDF 合并** — 选择多个 PDF，拖拽排序后合并

### 🧪 示例工具
- **Hello World** — 事件触发 + 服务调用演示
- **Demo Service** — 服务注册 + 事件监听演示

## 开发新插件

1. `plugins/` 下建目录 + `plugin.json`（含 `category` 字段）
2. 继承 `BasePlugin`，实现 `get_widget()` / `get_control_widget()`
3. 框架自动发现加载

```json
{
    "id": "my_plugin",
    "name": "我的插件",
    "category": "文档工具",
    "version": "1.0.0",
    "entry_point": "my_plugin.widget:MyPlugin"
}
```
