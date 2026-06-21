"""
核心配置管理模块
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")


def safe_load_json(file_path: str) -> Dict:
    """安全加载 JSON 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {file_path}")
        raise FileNotFoundError(f"配置文件不存在: {file_path}。请确保项目结构完整。")
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {file_path} - {e}")
        raise ValueError(f"配置文件格式错误: {file_path}。请检查 JSON 格式。")
    except Exception as e:
        logger.error(f"加载配置文件失败: {file_path} - {e}")
        raise


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, configs_dir: str = None):
        self.configs_dir = configs_dir or CONFIGS_DIR
        self._cache = {}
        self._last_modified = {}
    
    def load(self, filename: str) -> Dict:
        """加载配置文件，带缓存"""
        file_path = os.path.join(self.configs_dir, filename)
        
        # 检查文件修改时间
        try:
            current_modified = os.path.getmtime(file_path)
        except OSError:
            current_modified = 0
        
        # 如果文件未修改，返回缓存
        if filename in self._cache and self._last_modified.get(filename) == current_modified:
            return self._cache[filename]
        
        # 加载文件
        config = safe_load_json(file_path)
        self._cache[filename] = config
        self._last_modified[filename] = current_modified
        
        return config
    
    def get(self, filename: str, key: str = None, default: Any = None) -> Any:
        """获取配置值"""
        config = self.load(filename)
        if key:
            return config.get(key, default)
        return config
    
    def reload(self, filename: str = None):
        """重新加载配置"""
        if filename:
            if filename in self._cache:
                del self._cache[filename]
                del self._last_modified[filename]
        else:
            self._cache.clear()
            self._last_modified.clear()


# 全局配置管理器
config_manager = ConfigManager()
