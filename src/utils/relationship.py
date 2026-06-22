"""
词汇关系管理器 - 建立词汇之间的关系
"""

import json
import os
from typing import Dict, List, Set, Tuple
import logging

logger = logging.getLogger(__name__)


class RelationshipManager:
    """词汇关系管理器"""
    
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
            "configs", "relationships.json"
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._config = json.load(f)
        except Exception as e:
            logger.error(f"加载关系配置失败: {e}")
            self._config = {"relationships": {}}
    
    def get_relationships(self, word: str) -> Dict:
        """获取词汇的所有关系"""
        return self.config.get("relationships", {}).get(word, {})
    
    def get_synergies(self, word: str) -> List[str]:
        """获取协同词汇"""
        rels = self.get_relationships(word)
        return rels.get("synergy", [])
    
    def get_conflicts(self, word: str) -> List[str]:
        """获取冲突词汇"""
        rels = self.get_relationships(word)
        return rels.get("conflict", [])
    
    def get_contrasts(self, word: str) -> List[str]:
        """获取对比词汇"""
        rels = self.get_relationships(word)
        return rels.get("contrast", [])
    
    def get_contains(self, word: str) -> List[str]:
        """获取包含词汇"""
        rels = self.get_relationships(word)
        return rels.get("contains", [])
    
    def get_scene_hints(self, word: str) -> List[str]:
        """获取场景提示"""
        rels = self.get_relationships(word)
        return rels.get("scene_hints", [])
    
    def check_conflicts(self, words: List[str]) -> List[Tuple[str, str, str]]:
        """检查词汇之间的冲突"""
        conflicts = []
        for i, w1 in enumerate(words):
            for w2 in words[i+1:]:
                # 检查 w1 是否与 w2 冲突
                w1_conflicts = self.get_conflicts(w1)
                if w2 in w1_conflicts or any(c in w2 for c in w1_conflicts):
                    conflicts.append((w1, w2, "conflict"))
                # 检查 w2 是否与 w1 冲突
                w2_conflicts = self.get_conflicts(w2)
                if w1 in w2_conflicts or any(c in w1 for c in w2_conflicts):
                    conflicts.append((w2, w1, "conflict"))
        return conflicts
    
    def find_synergies(self, words: List[str]) -> List[str]:
        """找到与给定词汇协同的词汇"""
        synergies = set()
        for word in words:
            for synergy in self.get_synergies(word):
                if synergy not in words:
                    synergies.add(synergy)
        return list(synergies)
    
    def suggest_composition(self, words: List[str]) -> List[str]:
        """根据词汇建议构图"""
        composition_rules = self.config.get("composition_rules", {})
        
        for rule_name, rule in composition_rules.items():
            needs = rule.get("needs", [])
            if any(n in " ".join(words) for n in needs):
                return rule.get("recommended", [])
        
        return ["rule_of_thirds"]  # 默认


relationship_manager = RelationshipManager()
