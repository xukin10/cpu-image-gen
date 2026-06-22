"""
构图知识库 - 帮助用户理解什么是好构图
"""

import json
import os
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class CompositionManager:
    """构图管理器"""
    
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
            "configs", "composition.json"
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except Exception as e:
            logger.error(f"加载构图配置失败: {e}")
            self._config = {"composition_rules": {}}
    
    def get_all_rules(self) -> Dict:
        return self.config.get("composition_rules", {})
    
    def get_rule(self, rule_name: str) -> Optional[Dict]:
        return self.config.get("composition_rules", {}).get(rule_name)
    
    def get_rules_for_subject(self, subject: str) -> List[str]:
        subject_map = self.config.get("composition_by_subject", {})
        for subject_type, recommendations in subject_map.items():
            if subject_type in subject.lower():
                return recommendations.get("recommended", [])
        return ["rule_of_thirds"]
    
    def recommend(self, subject: str = "") -> Dict:
        recommended_rules = self.get_rules_for_subject(subject)
        recommendations = []
        for rule_name in recommended_rules[:3]:
            rule = self.get_rule(rule_name)
            if rule:
                recommendations.append({
                    "name": rule["name"],
                    "name_en": rule["name_en"],
                    "keywords": rule["keywords"],
                    "tips": rule.get("tips", [])
                })
        return {"recommended": recommendations}


composition_manager = CompositionManager()
