"""
优化管理器 - 提供可选的优化功能
"""

from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class OptimizationManager:
    """优化管理器"""
    
    def __init__(self):
        self._optimizations = {
            "composition": {"name": "构图优化", "description": "自动添加构图关键词", "enabled": False},
            "lighting": {"name": "光影优化", "description": "自动添加光影关键词", "enabled": False},
            "color": {"name": "色彩优化", "description": "自动添加色彩关键词", "enabled": False},
            "quality": {"name": "质量优化", "description": "自动添加质量关键词", "enabled": True, "keywords": ["highly detailed", "sharp focus"]}
        }
    
    def get_optimizations(self) -> Dict:
        return self._optimizations
    
    def toggle_optimization(self, key: str) -> bool:
        if key in self._optimizations:
            self._optimizations[key]["enabled"] = not self._optimizations[key]["enabled"]
            return self._optimizations[key]["enabled"]
        return False
    
    def get_enabled_optimizations(self) -> List[str]:
        return [k for k, v in self._optimizations.items() if v["enabled"]]
    
    def apply_optimizations(self, prompt: str, context: Dict = None) -> Tuple[str, List[str]]:
        optimized = prompt
        applied = []
        
        if self._optimizations["composition"]["enabled"]:
            from .composition import composition_manager
            rec = composition_manager.recommend(subject=context.get("subject", ""))
            if rec.get("recommended"):
                keywords = rec["recommended"][0].get("keywords", [])[:2]
                if keywords:
                    optimized += ", " + ", ".join(keywords)
                    applied.append("构图")
        
        if self._optimizations["lighting"]["enabled"]:
            from .lighting import lighting_manager
            rec = lighting_manager.recommend(scene=context.get("scene", ""))
            if rec.get("recommended"):
                keywords = rec["recommended"][0].get("keywords", [])[:2]
                if keywords:
                    optimized += ", " + ", ".join(keywords)
                    applied.append("光影")
        
        if self._optimizations["color"]["enabled"]:
            from .color import color_manager
            rec = color_manager.recommend(scene=context.get("scene", ""))
            if rec.get("recommended"):
                optimized += ", " + ", ".join(rec["recommended"][:2])
                applied.append("色彩")
        
        if self._optimizations["quality"]["enabled"]:
            keywords = self._optimizations["quality"].get("keywords", [])
            optimized += ", " + ", ".join(keywords)
            applied.append("质量")
        
        return optimized, applied


optimization_manager = OptimizationManager()
