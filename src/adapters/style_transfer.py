"""
风格迁移模块 - 将图片转换为不同艺术风格
"""

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class StyleTransfer:
    """风格迁移器"""
    
    def __init__(self):
        self.styles = {
            "oil_painting": self._oil_painting,
            "watercolor": self._watercolor,
            "sketch": self._sketch,
            "cartoon": self._cartoon,
            "pixel_art": self._pixel_art,
            "vintage": self._vintage,
            "dramatic": self._dramatic,
        }
    
    def get_available_styles(self) -> List[Dict]:
        """获取可用风格列表"""
        return [
            {"key": "oil_painting", "name": "油画风格", "desc": "模拟油画笔触效果"},
            {"key": "watercolor", "name": "水彩风格", "desc": "模拟水彩渲染效果"},
            {"key": "sketch", "name": "素描风格", "desc": "模拟铅笔素描效果"},
            {"key": "cartoon", "name": "卡通风格", "desc": "简化色彩，卡通化处理"},
            {"key": "pixel_art", "name": "像素风格", "desc": "像素化处理，复古游戏风"},
            {"key": "vintage", "name": "复古风格", "desc": "老照片效果，暖色调"},
            {"key": "dramatic", "name": "戏剧风格", "desc": "高对比度，戏剧化光影"},
        ]
    
    def transfer(
        self,
        image_path: str,
        style: str = "oil_painting",
        intensity: float = 1.0,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        执行风格迁移
        
        Args:
            image_path: 输入图片路径
            style: 风格类型
            intensity: 强度 (0.0-1.0)
            output_path: 输出路径
            
        Returns:
            输出图片路径
        """
        try:
            # 读取图片
            img = cv2.imread(image_path)
            if img is None:
                logger.error(f"无法读取图片: {image_path}")
                return None
            
            # 获取风格函数
            style_func = self.styles.get(style)
            if not style_func:
                logger.error(f"未知风格: {style}")
                return None
            
            # 应用风格
            styled = style_func(img, intensity)
            
            # 保存图片
            if output_path is None:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_{style}{ext}"
            
            cv2.imwrite(output_path, styled)
            logger.info(f"风格迁移完成: {image_path} -> {output_path} ({style})")
            
            return output_path
            
        except Exception as e:
            logger.error(f"风格迁移失败: {e}")
            return None
    
    def _oil_painting(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """油画风格"""
        # 模拟油画笔触：模糊 + 边缘增强
        smooth = cv2.bilateralFilter(img, 9, 75, 75)
        edges = cv2.Canny(img, 50, 150)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # 混合原图和边缘
        result = cv2.addWeighted(smooth, 1 - intensity * 0.3, edges, intensity * 0.3, 0)
        
        # 调整色彩饱和度
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        hsv[:,:,1] = cv2.normalize(hsv[:,:,1] * 1.2, None, 0, 255, cv2.NORM_MINMAX)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        return result
    
    def _watercolor(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """水彩风格"""
        # 模拟水彩：边缘保留滤波 + 模糊
        smooth = cv2.bilateralFilter(img, 9, 50, 50)
        
        # 量化色彩
        data = img.reshape((-1, 3)).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
        _, labels, centers = cv2.kmeans(data, 8, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
        centers = np.uint8(centers)
        quantized = centers[labels.flatten()].reshape(img.shape)
        
        # 混合
        result = cv2.addWeighted(smooth, 0.6, quantized, 0.4, 0)
        
        # 柔化
        result = cv2.GaussianBlur(result, (3, 3), 0)
        
        return result
    
    def _sketch(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """素描风格"""
        # 转灰度
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 边缘检测
        inv = 255 - gray
        blur = cv2.GaussianBlur(inv, (21, 21), 0)
        sketch = cv2.divide(gray, 255 - blur, scale=256)
        
        # 转回 BGR
        result = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        
        # 混合原图
        result = cv2.addWeighted(img, 1 - intensity * 0.7, result, intensity * 0.7, 0)
        
        return result
    
    def _cartoon(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """卡通风格"""
        # 边缘检测
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 2)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # 平滑
        smooth = cv2.bilateralFilter(img, 9, 75, 75)
        
        # 混合
        result = cv2.bitwise_and(smooth, edges)
        
        return result
    
    def _pixel_art(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """像素风格"""
        h, w = img.shape[:2]
        
        # 像素化大小
        pixel_size = max(4, int(8 * intensity))
        
        # 缩小再放大
        small = cv2.resize(img, (w // pixel_size, h // pixel_size), interpolation=cv2.INTER_LINEAR)
        result = cv2.resize(small, (w, h), interpolation=cv2.INTER_NEAREST)
        
        return result
    
    def _vintage(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """复古风格"""
        # 暖色调
        result = img.copy()
        result[:,:,0] = np.clip(result[:,:,0] * 1.1, 0, 255)  # B
        result[:,:,2] = np.clip(result[:,:,2] * 0.9, 0, 255)  # R
        
        # 轻微模糊
        result = cv2.GaussianBlur(result, (3, 3), 0)
        
        # 暗角效果
        h, w = result.shape[:2]
        X = cv2.getGaussianKernel(w, 150)
        Y = cv2.getGaussianKernel(h, 150)
        mask = Y * X.T
        mask = mask / mask.max()
        
        result = result * mask[:,:,np.newaxis]
        
        return result.astype(np.uint8)
    
    def _dramatic(self, img: np.ndarray, intensity: float) -> np.ndarray:
        """戏剧风格"""
        # 高对比度
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # CLAHE
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # 增加对比度
        result = cv2.convertScaleAbs(result, alpha=1.2, beta=0)
        
        return result


# 全局实例
style_transfer = StyleTransfer()


import os
