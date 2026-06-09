"""配置管理：持久化存储用户设置（如目录路径等）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.utils.logger import get_logger

logger = get_logger("ConfigManager")

_CONFIG_DIR = Path.home() / ".my_toolbox"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


class ConfigManager:
    """管理应用配置的持久化存储。"""

    _instance: Optional["ConfigManager"] = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config: Dict[str, Any] = {}
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        """加载配置文件。"""
        try:
            if _CONFIG_FILE.exists():
                self._config = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
            else:
                self._config = self._get_default_config()
        except Exception as e:
            logger.exception("加载配置失败，使用默认配置")
            self._config = self._get_default_config()

    def _save(self) -> None:
        """保存配置文件。"""
        try:
            _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            _CONFIG_FILE.write_text(json.dumps(self._config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.exception("保存配置失败")

    def _get_default_config(self) -> Dict[str, Any]:
        """返回默认配置。"""
        return {
            "paths": {
                "batch_rename": {
                    "source_dir": "",
                    "output_dir": ""
                },
                "pdf_merge": {
                    "source_dir": "",
                    "output_dir": ""
                },
                "word_to_pdf": {
                    "source_dir": "",
                    "output_dir": ""
                },
                "pdf_metadata": {
                    "source_dir": ""
                }
            }
        }

    def get_path(self, plugin_id: str, path_type: str) -> str:
        """获取指定插件的路径设置。"""
        return self._config.get("paths", {}).get(plugin_id, {}).get(path_type, "")

    def set_path(self, plugin_id: str, path_type: str, value: str) -> None:
        """设置指定插件的路径设置。"""
        if "paths" not in self._config:
            self._config["paths"] = {}
        if plugin_id not in self._config["paths"]:
            self._config["paths"][plugin_id] = {}
        self._config["paths"][plugin_id][path_type] = value
        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值。"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值。"""
        self._config[key] = value
        self._save()
