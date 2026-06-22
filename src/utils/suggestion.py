"""
智能建议系统 - 协作而非替代
"""

from typing import Dict, List, Tuple
import json
import os
import logging

logger = logging.getLogger(__name__)


class SuggestionSystem:
    """智能建议系统"""
    
    def __init__(self):
        self._user_preferences = {}
    
    def analyze_prompt(self, prompt: str) -> Dict:
        analysis = {
            "has_composition": False,
            "has_lighting": False,
            "has_color": False,
            "subject_type": "unknown",
            "scene_type": "unknown"
        }
        
        prompt_lower = prompt.lower()
        
        composition_keywords = ["rule of thirds", "symmetrical", "leading lines", "centered"]
        analysis["has_composition"] = any(k in prompt_lower for k in composition_keywords)
        
        lighting_keywords = ["light", "shadow", "glow", "neon", "backlit"]
        analysis["has_lighting"] = any(k in prompt_lower for k in lighting_keywords)
        
        color_keywords = ["warm", "cool", "vibrant", "muted", "color"]
        analysis["has_color"] = any(k in prompt_lower for k in color_keywords)
        
        if any(k in prompt_lower for k in ["portrait", "person", "face", "girl", "boy"]):
            analysis["subject_type"] = "portrait"
        elif any(k in prompt_lower for k in ["dragon", "monster", "creature"]):
            analysis["subject_type"] = "creature"
        elif any(k in prompt_lower for k in ["building", "architecture", "castle"]):
            analysis["subject_type"] = "architecture"
        
        if any(k in prompt_lower for k in ["forest", "mountain", "landscape"]):
            analysis["scene_type"] = "nature"
        elif any(k in prompt_lower for k in ["city", "urban", "street"]):
            analysis["scene_type"] = "urban"
        elif any(k in prompt_lower for k in ["horror", "scary", "dark"]):
            analysis["scene_type"] = "horror"
        elif any(k in prompt_lower for k in ["cyber", "neon", "futuristic"]):
            analysis["scene_type"] = "cyberpunk"
        
        return analysis
    
    def generate_suggestions(self, prompt: str, analysis: Dict) -> List[Dict]:
        suggestions = []
        
        if not analysis["has_composition"]:
            from .composition import composition_manager
            rec = composition_manager.recommend(subject=analysis["subject_type"])
            if rec.get("recommended"):
                rule = rec["recommended"][0]
                suggestions.append({"type": "composition", "name": rule["name"], "keywords": rule["keywords"][:2], "reason": "增强画面层次"})
        
        if not analysis["has_lighting"]:
            from .lighting import lighting_manager
            rec = lighting_manager.recommend(scene=analysis["scene_type"])
            if rec.get("recommended"):
                light = rec["recommended"][0]
                suggestions.append({"type": "lighting", "name": light["name"], "keywords": light["keywords"][:2], "reason": light.get("effect", "增强画面氛围")})
        
        if not analysis["has_color"]:
            from .color import color_manager
            rec = color_manager.recommend(scene=analysis["scene_type"])
            if rec.get("recommended"):
                suggestions.append({"type": "color", "name": "色彩优化", "keywords": rec["recommended"][:2], "reason": rec.get("tips", "增强画面色彩")})
        
        return suggestions
    
    def apply_suggestions(self, prompt: str, suggestions: List[Dict], accepted: List[str]) -> Tuple[str, List[str]]:
        optimized = prompt
        applied = []
        for suggestion in suggestions:
            if suggestion["type"] in accepted:
                keywords = suggestion.get("keywords", [])
                if keywords:
                    optimized += ", " + ", ".join(keywords)
                    applied.append(suggestion["name"])
        return optimized, applied
    
    def record_preference(self, suggestion_type: str, accepted: bool):
        if suggestion_type not in self._user_preferences:
            self._user_preferences[suggestion_type] = {"accepted": 0, "rejected": 0}
        if accepted:
            self._user_preferences[suggestion_type]["accepted"] += 1
        else:
            self._user_preferences[suggestion_type]["rejected"] += 1


suggestion_system = SuggestionSystem()
