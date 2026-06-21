"""
分层控制系统 - 让用户渐进式掌控生图模型
"""

import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class LayerConfig:
    """层级配置"""
    name: str
    description: str
    controls: List[str]
    learn: str


@dataclass
class ControlConfig:
    """控件配置"""
    label: str
    type: str
    options: List[str] = field(default_factory=list)
    min: int = 0
    max: int = 100
    default: Any = None
    description: str = ""


class LayerManager:
    """分层管理器"""
    
    def __init__(self):
        self._config = None
        self._current_layer = 1
    
    @property
    def config(self) -> Dict:
        if self._config is None:
            self._load_config()
        return self._config
    
    def _load_config(self):
        """加载配置"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "configs", "layers.json"
        )
        with open(config_path, "r", encoding="utf-8") as f:
            self._config = json.load(f)
    
    def get_layer(self, layer_num: int) -> Optional[LayerConfig]:
        """获取层级配置"""
        layer_data = self.config.get("layers", {}).get(str(layer_num))
        if not layer_data:
            return None
        
        return LayerConfig(
            name=layer_data["name"],
            description=layer_data["description"],
            controls=layer_data["controls"],
            learn=layer_data["learn"]
        )
    
    def get_controls(self, layer_num: int) -> List[Dict]:
        """获取层级的控件列表"""
        layer = self.get_layer(layer_num)
        if not layer:
            return []
        
        controls = []
        all_controls = self.config.get("layer_controls", {})
        
        for control_key in layer.controls:
            if control_key == "all":
                # 专家模式：返回所有控件
                for key, config in all_controls.items():
                    controls.append({"key": key, **config})
                break
            elif control_key in all_controls:
                controls.append({"key": control_key, **all_controls[control_key]})
        
        return controls
    
    def get_performance_comparison(self) -> Dict:
        """获取性能对比信息"""
        return self.config.get("performance_comparison", {})
    
    def set_layer(self, layer_num: int):
        """设置当前层级"""
        if 1 <= layer_num <= 4:
            self._current_layer = layer_num
    
    def get_current_layer(self) -> int:
        """获取当前层级"""
        return self._current_layer
    
    def get_layer_info(self) -> Dict:
        """获取当前层级的完整信息"""
        layer = self.get_layer(self._current_layer)
        controls = self.get_controls(self._current_layer)
        performance = self.get_performance_comparison()
        
        return {
            "layer": self._current_layer,
            "name": layer.name if layer else "",
            "description": layer.description if layer else "",
            "learn": layer.learn if layer else "",
            "controls": controls,
            "performance": performance
        }
    
    def format_prompt_with_layer(self, prompt: str, layer: int, params: Dict = None) -> str:
        """根据层级格式化 prompt"""
        if params is None:
            params = {}
        
        # 基础 prompt
        result = prompt
        
        # 根据层级添加参数
        if layer >= 3:
            # 高级模式：添加负面提示
            if "negative" in params:
                result += f" [negative: {params['negative']}]"
        
        if layer >= 4:
            # 专家模式：添加所有参数
            if "model" in params:
                result += f" [model: {params['model']}]"
            if "upscale" in params and params["upscale"]:
                result += " [upscale: 2x]"
        
        return result
    
    def get_help_text(self, layer: int) -> str:
        """获取层级帮助文本"""
        layer_info = self.get_layer(layer)
        if not layer_info:
            return ""
        
        help_text = f"【{layer_info.name}模式】{layer_info.description}\n\n"
        help_text += f"你将学到：{layer_info.learn}\n\n"
        help_text += "可用控件：\n"
        
        controls = self.get_controls(layer)
        for control in controls:
            help_text += f"  - {control['label']}: {control.get('description', '')}\n"
        
        return help_text


# 全局实例
layer_manager = LayerManager()
