"""
文化实体模块
"""

from typing import Dict, List, Optional, Tuple

from ..utils.config import config_manager


class CulturalEntityResolver:
    """文化实体解析器"""
    
    def __init__(self):
        self._entities = None
    
    @property
    def entities(self) -> Dict:
        if self._entities is None:
            self._entities = config_manager.load("cultural_entities.json")
        return self._entities
    
    def resolve(self, entity_key: str, cultural_context: str = None) -> Optional[Dict]:
        """解析文化实体"""
        entity = self.entities.get(entity_key)
        if not entity:
            return None
        
        variants = entity.get("variants", {})
        
        # 如果有文化上下文且存在对应变体
        if cultural_context and cultural_context in variants:
            return variants[cultural_context]
        
        # 如果只有一个变体，直接返回
        if len(variants) == 1:
            return list(variants.values())[0]
        
        # 返回所有变体供选择
        return {"all_variants": variants, "label": entity.get("label", entity_key)}
    
    def ask_clarification(self, entity_label: str, variants: Dict) -> Optional[Dict]:
        """追问用户选择"""
        print(f"\n>> 检测到「{entity_label}」，请问是哪种类型？")
        variant_list = list(variants.items())
        
        for i, (key, variant) in enumerate(variant_list, 1):
            desc = variant.get("name_en", key)
            print(f"  [{i}] {desc}")
        
        choice = input(">> 请选择 (数字，直接回车跳过): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(variant_list):
            return variant_list[int(choice) - 1][1]
        return None
    
    def get_all_entities(self) -> Dict:
        """获取所有实体"""
        return self.entities
    
    def get_entity_keys(self) -> List[str]:
        """获取所有实体键"""
        return list(self.entities.keys())


# 全局解析器实例
cultural_resolver = CulturalEntityResolver()
