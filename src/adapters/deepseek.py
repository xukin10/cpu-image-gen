"""
DeepSeek 集成模块 - 增强中文语义理解
"""

import os
import json
import logging
import requests
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class DeepSeekAdapter:
    """DeepSeek API 适配器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
    
    def is_configured(self) -> bool:
        """检查是否已配置 API Key"""
        return bool(self.api_key)
    
    def parse_complex_prompt(self, user_input: str) -> Dict[str, Any]:
        """
        解析复杂中文描述为结构化 prompt
        
        Args:
            user_input: 用户输入的中文描述
            
        Returns:
            结构化的 prompt 数据
        """
        if not self.is_configured():
            logger.warning("DeepSeek API Key 未配置，使用基础解析")
            return self._fallback_parse(user_input)
        
        try:
            response = self._call_api(
                system_prompt=self._get_system_prompt(),
                user_prompt=user_input
            )
            
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"DeepSeek API 调用失败: {e}")
            return self._fallback_parse(user_input)
    
    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        """调用 DeepSeek API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _get_system_prompt(self) -> str:
        """获取系统 prompt"""
        return """你是一个专业的 AI 生图 prompt 工程师。你的任务是将用户的中文描述转换为高质量的英文生图 prompt。

规则：
1. 理解用户的意图和情感
2. 提取关键元素：主体、场景、风格、光影、氛围
3. 生成结构化的英文 prompt
4. 保持 prompt 的自然流畅

输出格式（JSON）：
{
    "subject": "主体描述",
    "style": "风格",
    "scene": "场景",
    "lighting": "光影",
    "atmosphere": "氛围",
    "prompt_en": "完整的英文 prompt"
}

示例：
输入：画一个有中国风的赛博朋克城市，要有传统建筑和霓虹灯的对比
输出：{
    "subject": "city",
    "style": "cyberpunk + Chinese traditional",
    "scene": "urban night",
    "lighting": "neon glow, contrast lighting",
    "atmosphere": "futuristic yet traditional",
    "prompt_en": "cyberpunk city with Chinese traditional architecture, neon lights, contrast between ancient and futuristic, night scene, highly detailed"
}"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """解析 API 响应"""
        try:
            # 尝试解析 JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            
            return json.loads(json_str.strip())
        except json.JSONDecodeError:
            # 如果解析失败，返回基础结构
            return {
                "subject": "scene",
                "style": "",
                "scene": "",
                "lighting": "",
                "atmosphere": "",
                "prompt_en": response
            }
    
    def _fallback_parse(self, user_input: str) -> Dict[str, Any]:
        """备用解析（不调用 API）"""
        return {
            "subject": user_input,
            "style": "",
            "scene": "",
            "lighting": "",
            "atmosphere": "",
            "prompt_en": user_input
        }
    
    def enhance_prompt(self, base_prompt: str, context: str = None) -> str:
        """
        增强已有的 prompt
        
        Args:
            base_prompt: 基础 prompt
            context: 额外上下文
            
        Returns:
            增强后的 prompt
        """
        if not self.is_configured():
            return base_prompt
        
        try:
            user_prompt = f"请增强以下 prompt，使其更详细、更有画面感：\n\n{base_prompt}"
            if context:
                user_prompt += f"\n\n额外要求：{context}"
            
            response = self._call_api(
                system_prompt="你是一个 prompt 优化专家。请直接输出增强后的英文 prompt，不要解释。",
                user_prompt=user_prompt
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Prompt 增强失败: {e}")
            return base_prompt


# 全局实例
deepseek_adapter = DeepSeekAdapter()
