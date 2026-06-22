"""
输入解析模块
"""

import re
from typing import Dict, List, Optional, Tuple

from ..utils.config import config_manager


class InputParser:
    """输入解析器"""
    
    def __init__(self):
        self._load_maps()
    
    def _load_maps(self):
        """加载关键词映射"""
        keywords = config_manager.load("keywords.json")
        
        self.style_map = keywords.get("style", {})
        self.time_map = keywords.get("time", {})
        self.place_map = keywords.get("place", {})
        self.weather_map = keywords.get("weather", {})
        self.light_map = keywords.get("light", {})
        self.view_map = keywords.get("view", {})
        self.quality_map = keywords.get("quality", {})
        self.artist_map = keywords.get("artist", {})
        self.material_map = keywords.get("material", {})
        self.mood_map = keywords.get("mood", {})
        self.cn_to_en = keywords.get("subject_cn_to_en", {})
        
        self.all_maps = [
            self.style_map, self.time_map, self.place_map,
            self.weather_map, self.light_map, self.view_map,
            self.quality_map, self.artist_map, self.material_map,
            self.mood_map
        ]
    
    def detect_cultural_context(self, text: str) -> Optional[str]:
        """检测文化上下文"""
        cultural_markers = {
            "chinese": ["中国", "中式", "国风", "东方", "传统", "华夏", "汉"],
            "western": ["西方", "欧式", "西式", "西洋", "classic", "欧美"],
            "japanese": ["日本", "日式", "和风", "和", "东瀛"],
        }
        
        for culture, markers in cultural_markers.items():
            if any(m in text for m in markers):
                return culture
        return None
    
    def find_entities(self, text: str) -> List[Tuple[str, str]]:
        """查找文本中的文化实体"""
        entity_keywords = config_manager.get("cultural_entities.json", None, {})
        # 从 cultural_entities.json 构建实体关键词映射
        entity_map = {}
        for entity_key, entity_data in entity_keywords.items():
            if "label" in entity_data:
                entity_map[entity_data["label"]] = entity_key
        
        found = []
        matched_entities = set()
        
        for keyword, entity_key in entity_map.items():
            if keyword in text:
                if entity_key in matched_entities:
                    continue
                found = [(k, e) for k, e in found if e != entity_key]
                found.append((keyword, entity_key))
                matched_entities.add(entity_key)
        
        return found
    
    def parse(self, text: str, ask_clarification: bool = True) -> Dict:
        """解析用户输入"""
        from ..entities.cultural import CulturalEntityResolver
        
        result = {
            "subject": "",
            "style": [],
            "time": [],
            "place": [],
            "weather": [],
            "light": [],
            "view": [],
            "quality": ["highly detailed"],
            "artist": [],
            "material": [],
            "mood": [],
            "raw": text,
            "cultural_context": None,
            "resolved_entities": [],
        }
        
        # 检测文化上下文
        result["cultural_context"] = self.detect_cultural_context(text)
        
        # 解析文化实体
        resolver = CulturalEntityResolver()
        found_entities = self.find_entities(text)
        
        for keyword, entity_key in found_entities:
            resolved = resolver.resolve(entity_key, result["cultural_context"])
            if resolved:
                if "all_variants" in resolved:
                    if ask_clarification:
                        clarified = resolver.ask_clarification(
                            resolved["label"], resolved["all_variants"]
                        )
                        if clarified:
                            result["resolved_entities"].append(clarified)
                        else:
                            first_variant = list(resolved["all_variants"].values())[0]
                            result["resolved_entities"].append(first_variant)
                    else:
                        first_variant = list(resolved["all_variants"].values())[0]
                        result["resolved_entities"].append(first_variant)
                else:
                    result["resolved_entities"].append(resolved)
        
        # 解析关键词
        for key, value in self.style_map.items():
            if key in text: result["style"].append(value)
        for key, value in self.time_map.items():
            if key in text: result["time"].append(value)
        for key, value in self.place_map.items():
            if key in text: result["place"].append(value)
        for key, value in self.weather_map.items():
            if key in text: result["weather"].append(value)
        for key, value in self.light_map.items():
            if key in text: result["light"].append(value)
        for key, value in self.view_map.items():
            if key in text: result["view"].append(value)
        for key, value in self.quality_map.items():
            if key in text: result["quality"].append(value)
        for key, value in self.artist_map.items():
            if key in text: result["artist"].append(value)
        for key, value in self.material_map.items():
            if key in text: result["material"].append(value)
        for key, value in self.mood_map.items():
            if key in text: result["mood"].append(value)
        
        # 提取主体（CN_TO_EN 最长匹配优先）
        if not result.get("resolved_entities"):
            cn_keys = sorted([k for k in self.cn_to_en.keys() if len(k) > 1 and k in text], key=len, reverse=True)
            remaining = text
            en_parts = []
            for cn in cn_keys:
                if cn in remaining:
                    val = self.cn_to_en[cn]
                    if val:
                        en_parts.append(val)
                    remaining = remaining.replace(cn, " ", 1)
            # PLACE 多字词
            place_keys = sorted([k for k in self.place_map.keys() if len(k) > 1 and k in remaining], key=len, reverse=True)
            for pk in place_keys:
                if pk in remaining:
                    remaining = remaining.replace(pk, " ", 1)
            # 单字 CN_TO_EN
            for part in remaining.split():
                if len(part) == 1 and part in self.cn_to_en:
                    en_parts.append(self.cn_to_en[part])
            if en_parts:
                subject = " ".join(en_parts)
            else:
                # 回退：清理后剩余文字
                subject = re.sub(r'[,，、。!！?？\s]+', ' ', text).strip()
                subject = re.sub(r'[的了在是和与有下上中里外一个两只三匹些种张台件面条颗瓶杯碗盘把]', ' ', subject)
                subject = re.sub(r'\s+', ' ', subject).strip()
                if not subject.strip():
                    subject = "a scene"
            result["subject"] = subject
        else:
            result["subject"] = ""
        
        return result


# 全局解析器实例
parser = InputParser()
