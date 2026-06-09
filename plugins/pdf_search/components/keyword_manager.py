"""关键词管理器组件：负责关键词和关键词组的管理、持久化和搜索触发。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPalette, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QMenu, QInputDialog, QMessageBox, QFrame
)


class KeywordButtonInfo:
    def __init__(self, name: str, keywords: List[str] = None, is_group: bool = False):
        self.name = name
        self.keywords = keywords if keywords else []
        self.is_group = is_group
        self._button = None


class KeywordManager(QWidget):
    search_requested = Signal(object, int)
    
    def __init__(self, config) -> None:
        super().__init__()
        self._config = config
        self._keyword_info: List[KeywordButtonInfo] = []
        self._status_label: QLabel
        self._keyword_input: QLineEdit
        self._context_spin: QLineEdit
        self._keyword_container: QVBoxLayout
        self._init_ui()
        self._load_keywords()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        main_frame = QFrame()
        main_frame.setObjectName("panel")
        main_layout = QVBoxLayout(main_frame)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        main_layout.addWidget(self._create_quick_search())
        main_layout.addWidget(self._create_keyword_group())
        main_layout.addWidget(self._create_context_group())
        main_layout.addWidget(self._create_search_button())
        main_layout.addWidget(self._create_status_label())
        main_layout.addStretch()
        
        layout.addWidget(main_frame)
    
    def _create_quick_search(self) -> QGroupBox:
        group = QGroupBox("⚡ 快速搜索")
        group.setObjectName("sectionBox")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 8, 10, 8)
        group_layout.setSpacing(8)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("输入关键词，支持空格或逗号分隔")
        self._keyword_input.setFixedHeight(32)
        self._keyword_input.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 0 8px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        self._keyword_input.returnPressed.connect(self._on_quick_search)
        input_row.addWidget(self._keyword_input)
        
        search_btn = QPushButton("搜索")
        search_btn.setFixedSize(64, 32)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)
        search_btn.clicked.connect(self._on_quick_search)
        input_row.addWidget(search_btn)
        group_layout.addLayout(input_row)
        
        return group
    
    def _create_keyword_group(self) -> QGroupBox:
        group = QGroupBox("⭐ 关键词/组")
        group.setObjectName("sectionBox")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(10, 8, 10, 8)
        group_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        
        add_keyword_btn = QPushButton("+ 添加关键词")
        add_keyword_btn.setMinimumWidth(110)
        add_keyword_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecfdf5;
                color: #059669;
                border: 1px solid #10b981;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #d1fae5;
            }
        """)
        add_keyword_btn.clicked.connect(self._on_add_keyword)
        btn_row.addWidget(add_keyword_btn)
        
        add_group_btn = QPushButton("+ 新建分组")
        add_group_btn.setMinimumWidth(100)
        add_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #2563eb;
                border: 1px solid #3b82f6;
                border-radius: 4px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #dbeafe;
            }
        """)
        add_group_btn.clicked.connect(self._on_add_group)
        btn_row.addWidget(add_group_btn)
        
        btn_row.addStretch()
        group_layout.addLayout(btn_row)

        self._keyword_container = QVBoxLayout()
        self._keyword_container.setSpacing(4)
        group_layout.addLayout(self._keyword_container)

        return group
    
    def _create_context_group(self) -> QGroupBox:
        context_group = QGroupBox("📝 前后文设置")
        context_group.setObjectName("sectionBox")
        context_layout = QVBoxLayout(context_group)
        context_layout.setContentsMargins(10, 8, 10, 8)
        context_layout.setSpacing(8)

        context_row = QHBoxLayout()
        context_row.setSpacing(8)
        
        label = QLabel("前后文字数:")
        label.setStyleSheet("font-size: 13px; color: #475569;")
        context_row.addWidget(label)
        
        self._context_spin = QLineEdit()
        self._context_spin.setText("8")
        self._context_spin.setFixedWidth(50)
        self._context_spin.setStyleSheet("""
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                padding: 0 6px;
                font-size: 12px;
                text-align: center;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
                outline: none;
            }
        """)
        context_row.addWidget(self._context_spin)
        
        hint_label = QLabel("(0-50)")
        hint_label.setStyleSheet("font-size: 12px; color: #94a3b8;")
        context_row.addWidget(hint_label)
        
        context_row.addStretch()
        context_layout.addLayout(context_row)
        
        return context_group
    
    def _create_search_button(self) -> QPushButton:
        search_btn = QPushButton("🚀 搜索全部关键词")
        search_btn.setObjectName("primary")
        search_btn.setFixedHeight(36)
        search_btn.setStyleSheet("""
            QPushButton#primary {
                background-color: linear-gradient(135deg, #3b82f6, #1d4ed8);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton#primary:hover {
                background-color: linear-gradient(135deg, #2563eb, #1e40af);
            }
            QPushButton#primary:pressed {
                background-color: linear-gradient(135deg, #1d4ed8, #1e3a8a);
            }
        """)
        search_btn.clicked.connect(self._on_search_all)
        return search_btn
    
    def _create_status_label(self) -> QLabel:
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("status")
        self._status_label.setStyleSheet("""
            QLabel#status {
                font-size: 12px;
                color: #64748b;
                padding: 4px;
            }
        """)
        return self._status_label
    
    def _on_add_keyword(self) -> None:
        dialog = QInputDialog()
        dialog.setWindowTitle("添加关键词")
        dialog.setLabelText("请输入关键词:")
        dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
                border-radius: 8px;
            }
            QLabel {
                font-size: 13px;
                color: #1e293b;
            }
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        
        ok = dialog.exec()
        keyword = dialog.textValue().strip()
        
        if ok and keyword:
            info = KeywordButtonInfo(keyword, [], False)
            self._keyword_info.append(info)
            self._add_keyword_button(info)
            self._save_keywords()
            self.set_status(f"已添加: 🔤 {keyword}")
    
    def _on_add_group(self) -> None:
        name_dialog = QInputDialog()
        name_dialog.setWindowTitle("新建关键词组")
        name_dialog.setLabelText("请输入关键词组名称:")
        name_dialog.setStyleSheet("""
            QDialog { background-color: #ffffff; border-radius: 8px; }
            QLabel { font-size: 13px; color: #1e293b; }
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
        """)
        
        ok1 = name_dialog.exec()
        group_name = name_dialog.textValue().strip()
        
        if ok1 and group_name:
            kw_dialog = QInputDialog()
            kw_dialog.setWindowTitle("添加关键词")
            kw_dialog.setLabelText("请输入关键词（用空格或逗号分隔）:")
            kw_dialog.setStyleSheet("""
                QDialog { background-color: #ffffff; border-radius: 8px; }
                QLabel { font-size: 13px; color: #1e293b; }
                QLineEdit {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                }
            """)
            
            ok2 = kw_dialog.exec()
            keywords_str = kw_dialog.textValue()
            
            if ok2:
                keywords = [k.strip() for k in keywords_str.replace(',', ' ').split()]
                keywords = [k for k in keywords if k]
                
                if keywords:
                    info = KeywordButtonInfo(group_name, keywords, True)
                    self._keyword_info.append(info)
                    self._add_group_button(info)
                    self._save_keywords()
                    self.set_status(f"已创建: 📦 {group_name} ({len(keywords)})")
                else:
                    QMessageBox.warning(self, "提示", "请至少添加一个关键词")
    
    def _add_keyword_button(self, info: KeywordButtonInfo) -> None:
        btn = QPushButton(f"🔤 {info.name}")
        btn.setFixedHeight(30)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #334155;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                text-align: left;
                padding-left: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f8fafc;
                border-color: #cbd5e1;
            }
            QPushButton:pressed {
                background-color: #f1f5f9;
            }
        """)
        btn.clicked.connect(lambda: self._on_keyword_click(info))
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, b=btn, i=info: 
            self._show_keyword_menu(pos, b, i))
        self._keyword_container.addWidget(btn)
        info._button = btn
    
    def _add_group_button(self, info: KeywordButtonInfo) -> None:
        btn = QPushButton(f"📦 {info.name} ({len(info.keywords)})")
        btn.setFixedHeight(30)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #1e40af;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                text-align: left;
                padding-left: 10px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #dbeafe;
                border-color: #93c5fd;
            }
            QPushButton:pressed {
                background-color: #bfdbfe;
            }
        """)
        btn.clicked.connect(lambda: self._on_group_click(info))
        btn.setContextMenuPolicy(Qt.CustomContextMenu)
        btn.customContextMenuRequested.connect(lambda pos, b=btn, i=info: 
            self._show_group_menu(pos, b, i))
        self._keyword_container.addWidget(btn)
        info._button = btn
    
    def _show_keyword_menu(self, pos, button, info):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 80px 6px 24px;
                font-size: 13px;
                color: #334155;
            }
            QMenu::item:hover {
                background-color: #f1f5f9;
            }
        """)
        
        edit_action = QAction("编辑")
        edit_action.triggered.connect(lambda: self._edit_keyword(info))
        menu.addAction(edit_action)
        
        delete_action = QAction("删除")
        delete_action.triggered.connect(lambda: self._delete_keyword(info))
        menu.addAction(delete_action)
        
        menu.exec(button.mapToGlobal(pos))
    
    def _show_group_menu(self, pos, button, info):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 80px 6px 24px;
                font-size: 13px;
                color: #334155;
            }
            QMenu::item:hover {
                background-color: #f1f5f9;
            }
        """)
        
        edit_action = QAction("编辑")
        edit_action.triggered.connect(lambda: self._edit_group(info))
        menu.addAction(edit_action)
        
        delete_action = QAction("删除")
        delete_action.triggered.connect(lambda: self._delete_group(info))
        menu.addAction(delete_action)
        
        menu.exec(button.mapToGlobal(pos))
    
    def _edit_keyword(self, info):
        dialog = QInputDialog()
        dialog.setWindowTitle("编辑关键词")
        dialog.setLabelText("请输入新关键词:")
        dialog.setTextValue(info.name)
        dialog.setStyleSheet("""
            QDialog { background-color: #ffffff; border-radius: 8px; }
            QLabel { font-size: 13px; color: #1e293b; }
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
        """)
        
        ok = dialog.exec()
        new_keyword = dialog.textValue().strip()
        
        if ok and new_keyword:
            info.name = new_keyword
            info._button.setText(f"🔤 {new_keyword}")
            info._button.clicked.disconnect()
            info._button.clicked.connect(lambda: self._on_keyword_click(info))
            self._save_keywords()
            self.set_status(f"已修改: 🔤 {new_keyword}")
    
    def _delete_keyword(self, info):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(f"确定要删除关键词 '{info.name}' 吗？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #ffffff; }
            QLabel { font-size: 13px; color: #1e293b; }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        
        result = msg_box.exec()
        if result == QMessageBox.Yes:
            self._keyword_container.removeWidget(info._button)
            self._keyword_info.remove(info)
            info._button.deleteLater()
            self._save_keywords()
            self.set_status(f"已删除: 🔤 {info.name}")
    
    def _edit_group(self, info):
        name_dialog = QInputDialog()
        name_dialog.setWindowTitle("编辑关键词组")
        name_dialog.setLabelText("请输入新名称:")
        name_dialog.setTextValue(info.name)
        name_dialog.setStyleSheet("""
            QDialog { background-color: #ffffff; border-radius: 8px; }
            QLabel { font-size: 13px; color: #1e293b; }
            QLineEdit {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
        """)
        
        ok1 = name_dialog.exec()
        new_name = name_dialog.textValue().strip()
        
        if ok1 and new_name:
            kw_dialog = QInputDialog()
            kw_dialog.setWindowTitle("编辑关键词")
            kw_dialog.setLabelText("请输入关键词（用空格或逗号分隔）:")
            kw_dialog.setTextValue(", ".join(info.keywords))
            kw_dialog.setStyleSheet("""
                QDialog { background-color: #ffffff; border-radius: 8px; }
                QLabel { font-size: 13px; color: #1e293b; }
                QLineEdit {
                    background-color: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 6px;
                    padding: 6px 8px;
                    font-size: 13px;
                }
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 16px;
                }
            """)
            
            ok2 = kw_dialog.exec()
            new_keywords_str = kw_dialog.textValue()
            
            if ok2:
                new_keywords = [k.strip() for k in new_keywords_str.replace(',', ' ').split()]
                new_keywords = [k for k in new_keywords if k]
                
                if new_keywords:
                    info.name = new_name
                    info.keywords = new_keywords
                    info._button.setText(f"📦 {new_name} ({len(new_keywords)})")
                    info._button.clicked.disconnect()
                    info._button.clicked.connect(lambda: self._on_group_click(info))
                    self._save_keywords()
                    self.set_status(f"已修改: 📦 {new_name}")
                else:
                    QMessageBox.warning(self, "提示", "请至少保留一个关键词")
    
    def _delete_group(self, info):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(f"确定要删除关键词组 '{info.name}' 吗？")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        msg_box.setStyleSheet("""
            QMessageBox { background-color: #ffffff; }
            QLabel { font-size: 13px; color: #1e293b; }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 16px;
            }
        """)
        
        result = msg_box.exec()
        if result == QMessageBox.Yes:
            self._keyword_container.removeWidget(info._button)
            self._keyword_info.remove(info)
            info._button.deleteLater()
            self._save_keywords()
            self.set_status(f"已删除: 📦 {info.name}")
    
    def _on_keyword_click(self, info):
        context_length = int(self._context_spin.text()) if self._context_spin.text().isdigit() else 8
        self.search_requested.emit([info.name], context_length)
        self.set_status(f"正在搜索: 🔤 {info.name}")
    
    def _on_group_click(self, info):
        context_length = int(self._context_spin.text()) if self._context_spin.text().isdigit() else 8
        self.search_requested.emit(info.keywords, context_length)
        self.set_status(f"正在搜索: 📦 {info.name} ({len(info.keywords)} 个)")
    
    def _on_quick_search(self):
        text = self._keyword_input.text().strip()
        if text:
            keywords = [k.strip() for k in text.replace(',', ' ').split()]
            keywords = [k for k in keywords if k]
            if keywords:
                context_length = int(self._context_spin.text()) if self._context_spin.text().isdigit() else 8
                self.search_requested.emit(keywords, context_length)
                self.set_status(f"搜索中: {', '.join(keywords)}")
    
    def _on_search_all(self):
        all_keywords = []
        
        for info in self._keyword_info:
            if info.is_group:
                all_keywords.extend(info.keywords)
            else:
                all_keywords.append(info.name)
        
        if all_keywords:
            context_length = int(self._context_spin.text()) if self._context_spin.text().isdigit() else 8
            self.search_requested.emit(all_keywords, context_length)
            self.set_status(f"搜索全部: {len(all_keywords)} 个关键词")
        else:
            self.set_status("⚠️ 请先添加关键词或关键词组")
    
    def _load_keywords(self):
        try:
            data = self._config.get("pdf_search.keywords", "{}")
            data = json.loads(data)
            
            for keyword in data.get("keywords", []):
                info = KeywordButtonInfo(keyword, [], False)
                self._keyword_info.append(info)
                self._add_keyword_button(info)
            
            for group in data.get("groups", []):
                info = KeywordButtonInfo(group["name"], group["keywords"], True)
                self._keyword_info.append(info)
                self._add_group_button(info)
        except Exception:
            pass
    
    def _save_keywords(self):
        data = {
            "keywords": [],
            "groups": []
        }
        
        for info in self._keyword_info:
            if info.is_group:
                data["groups"].append({
                    "name": info.name,
                    "keywords": info.keywords
                })
            else:
                data["keywords"].append(info.name)
        
        self._config.set(f"pdf_search.keywords", json.dumps(data))
    
    def set_status(self, text: str) -> None:
        self._status_label.setText(text)