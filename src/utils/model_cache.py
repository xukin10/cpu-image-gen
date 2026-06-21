"""
模型缓存模块 - 性能优化
"""

import torch
import os
from diffusers import AutoPipelineForText2Image, StableDiffusionPipeline
from typing import Optional, Dict, Any
import logging
import gc

logger = logging.getLogger(__name__)


class ModelCache:
    """模型缓存管理器"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._max_cache_size = 2  # 最多缓存2个模型
    
    def get_model(self, model_name: str, config: Dict = None) -> Optional[Any]:
        """获取模型，优先从缓存"""
        if model_name in self._cache:
            logger.info(f"从缓存加载模型: {model_name}")
            return self._cache[model_name]
        
        # 加载新模型
        logger.info(f"加载新模型: {model_name}")
        pipe = self._load_model(model_name)
        
        if pipe is None:
            return None
        
        # 缓存管理：如果超过最大数量，移除最早的
        if len(self._cache) >= self._max_cache_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            gc.collect()
        
        self._cache[model_name] = pipe
        return pipe
    
    def _load_model(self, model_name: str) -> Optional[Any]:
        """加载模型"""
        try:
            torch.set_num_threads(min(16, os.cpu_count() or 4))
            
            # 检查是否是中文模型
            if "IDEA-CCNL" in model_name or "Taiyi" in model_name:
                # 中文模型使用 StableDiffusionPipeline
                pipe = StableDiffusionPipeline.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    safety_checker=None,
                    local_files_only=True,
                )
            else:
                # 其他模型使用 AutoPipeline
                pipe = AutoPipelineForText2Image.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    local_files_only=True,
                )
            pipe = pipe.to("cpu")
            pipe.enable_attention_slicing()
            
            return pipe
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            return None
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        gc.collect()
    
    def remove(self, model_name: str):
        """移除指定模型"""
        if model_name in self._cache:
            del self._cache[model_name]
            gc.collect()
    
    @property
    def cached_models(self):
        """获取已缓存的模型列表"""
        return list(self._cache.keys())


# 全局模型缓存实例
model_cache = ModelCache()
