"""
图片放大模块 - 使用 OpenCV 实现 CPU 图片放大
"""

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class ImageUpscaler:
    """图片放大器"""
    
    def __init__(self):
        self.methods = {
            "bicubic": cv2.INTER_CUBIC,
            "linear": cv2.INTER_LINEAR,
            "lanczos": cv2.INTER_LANCZOS4,
        }
    
    def upscale(
        self,
        image_path: str,
        scale: int = 2,
        method: str = "bicubic",
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        放大图片
        
        Args:
            image_path: 输入图片路径
            scale: 放大倍数 (2, 3, 4)
            method: 插值方法 (bicubic, linear, lanczos)
            output_path: 输出路径（可选）
            
        Returns:
            输出图片路径
        """
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return None
            
            # 获取插值方法
            interp = self.methods.get(method, cv2.INTER_CUBIC)
            
            # 放大图片
            h, w = img.shape[:2]
            new_h, new_w = h * scale, w * scale
            
            upscaled = cv2.resize(img, (new_w, new_h), interpolation=interp)
            
            # 应用锐化
            upscaled = self._sharpen(upscaled)
            
            # 保存图片
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_upscaled{ext}"
            
            cv2.imwrite(output_path, upscaled)
            logger.info(f"图片放大完成: {image_path} -> {output_path} ({scale}x)")
            
            return output_path
            
        except Exception as e:
            logger.error(f"图片放大失败: {e}")
            return None
    
    def _sharpen(self, img: np.ndarray) -> np.ndarray:
        """应用锐化"""
        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])
        return cv2.filter2D(img, -1, kernel)
    
    def upscale_pil(
        self,
        image: Image.Image,
        scale: int = 2,
        method: str = "bicubic"
    ) -> Image.Image:
        """
        使用 PIL 放大图片
        
        Args:
            image: PIL Image 对象
            scale: 放大倍数
            method: 插值方法
            
        Returns:
            放大后的 PIL Image
        """
        interp_map = {
            "bicubic": Image.BICUBIC,
            "linear": Image.BILINEAR,
            "lanczos": Image.LANCZOS,
        }
        
        interp = interp_map.get(method, Image.BICUBIC)
        new_size = (image.width * scale, image.height * scale)
        
        return image.resize(new_size, interp)


# 全局实例
upscaler = ImageUpscaler()


import os
