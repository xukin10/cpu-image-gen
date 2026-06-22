"""
光影知识库 - 帮助用户理解什么是好光影
"""

import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LightingManager:
    """光影管理器"""
    
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
            "configs", "lighting.json"
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except Exception as e:
            logger.error(f"加载光影配置失败: {e}")
            self._config = {"lighting_rules": {}}
    
    def get_all_rules(self) -> Dict:
        return self.config.get("lighting_rules", {})
    
    def get_rule(self, rule_name: str) -> Optional[Dict]:
        rules = self.config.get("lighting_rules", {})
        for category, rule_data in rules.items():
            if "subcategories" in rule_data:
                if rule_name in rule_data["subcategories"]:
                    return rule_data["subcategories"][rule_name]
            if "effects" in rule_data:
                if rule_name in rule_data["effects"]:
                    return rule_data["effects"][rule_name]
        return None
    
    def get_lighting_for_scene(self, scene: str) -> Dict:
        scene_map = self.config.get("lighting_by_scene", {})
        for scene_type, recommendations in scene_map.items():
            if scene_type in scene.lower():
                return {"recommended": recommendations.get("best", []), "tips": recommendations.get("tips", "")}
        return {"recommended": ["soft_light"], "tips": ""}
    
    def recommend(self, scene: str = "") -> Dict:
        scene_lighting = self.get_lighting_for_scene(scene)
        recommendations = []
        for lighting_name in scene_lighting.get("recommended", [])[:3]:
            rule = self.get_rule(lighting_name)
            if rule:
                recommendations.append({"name": rule["name"], "keywords": rule.get("keywords", []), "effect": rule.get("effect", "")})
        return {"recommended": recommendations, "tips": scene_lighting.get("tips", "")}


lighting_manager = LightingManager()
