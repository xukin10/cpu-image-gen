"""
色彩知识库 - 帮助用户理解什么是好色彩
"""

import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ColorManager:
    """色彩管理器"""
    
    def __init__(self):
        self._config = None
    
    @property
    def config(self) -> Dict:
        if self._config is None:
            self._load_config()
        return self._config
    
    def _load_config(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "configs", "color.json"
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except Exception as e:
            logger.error(f"加载色彩配置失败: {e}")
            self._config = {"color_theory": {}, "color_by_scene": {}}
    
    def get_colors_for_scene(self, scene: str) -> Dict:
        scene_map = self.config.get("color_by_scene", {})
        for scene_type, recommendations in scene_map.items():
            if scene_type in scene.lower():
                return {"recommended": recommendations.get("best", []), "tips": recommendations.get("tips", "")}
        return {"recommended": [], "tips": ""}
    
    def recommend(self, scene: str = "") -> Dict:
        scene_colors = self.get_colors_for_scene(scene)
        return {"recommended": scene_colors.get("recommended", []), "tips": scene_colors.get("tips", "")}


color_manager = ColorManager()
