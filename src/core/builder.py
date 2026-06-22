"""
Prompt 构建模块 — 同 prompt_builder.build_prompt 保持一致的长度控制策略
"""

from typing import Dict, List

from ..utils.config import config_manager


class PromptBuilder:
    """Prompt 构建器"""

    def _count_words(self, prompt: str) -> int:
        return len([w.strip() for w in prompt.split(",") if w.strip()])

    def _trim_prompt(self, prompt: str, max_words: int) -> str:
        parts = [w.strip() for w in prompt.split(",") if w.strip()]
        if len(parts) <= max_words:
            return prompt
        return ", ".join(parts[:max_words])

    def build(self, parsed: Dict) -> str:
        """根据解析结果构建 prompt（与 prompt_builder.build_prompt 保持一致）"""
        parts = []
        exclude_words = []

        # 风格
        if parsed["style"]:
            parts.append(parsed["style"][0])

        # 主体
        if parsed.get("resolved_entities"):
            for entity in parsed["resolved_entities"]:
                if "name_en" in entity: parts.append(entity["name_en"])
                if "morphology" in entity: parts.extend(entity["morphology"][:2])
                if "elements" in entity: parts.extend(entity["elements"][:2])
                if "atmosphere" in entity: parts.append(entity["atmosphere"][0])
                if "exclude" in entity: exclude_words.extend(entity["exclude"])
        else:
            parts.append(parsed["subject"])

        # 场景
        if parsed["time"]:
            parts.append(parsed["time"][0])
        elif parsed.get("resolved_entities"):
            for entity in parsed["resolved_entities"]:
                if "scenes" in entity:
                    parts.append(entity["scenes"][0])
                    break

        if parsed["place"]:
            parts.append(parsed["place"][0])
        elif parsed["subject"]:
            subject_lower = parsed["subject"].lower()
            if any(k in subject_lower for k in ["dragon", "phoenix", "bird"]):
                parts.append("in the sky")
            elif any(k in subject_lower for k in ["fish", "whale", "coral"]):
                parts.append("underwater")
            elif any(k in subject_lower for k in ["tree", "forest", "wolf"]):
                parts.append("in a forest")

        if parsed["weather"]:
            parts.append(parsed["weather"][0])

        # 光影
        if parsed["light"]:
            parts.append(", ".join(parsed["light"]))
        elif parsed["subject"]:
            parts.append(self._get_default_lighting(parsed["subject"]))

        # 视角
        if parsed["view"]:
            parts.append(parsed["view"][0])
        else:
            parts.append(self._get_default_view(parsed.get("subject", "")))

        # 风格补充
        for s in parsed["style"][1:]:
            parts.append(s)

        # 艺术家、材质、氛围
        if parsed["artist"]: parts.append(", ".join(parsed["artist"][:2]))
        if parsed["material"]: parts.append(", ".join(parsed["material"][:2]))
        if parsed["mood"]: parts.append(", ".join(parsed["mood"][:2]))

        # 质量
        quality = self._get_quality(parsed, exclude_words)
        parts.extend(quality[:6])

        # 关系系统协同词
        all_words = []
        if parsed.get("style"): all_words.extend(parsed["style"])
        if parsed.get("subject"): all_words.append(parsed["subject"])
        if parsed.get("mood"): all_words.extend(parsed["mood"])
        try:
            from ..utils.relationship import relationship_manager
            synergies = relationship_manager.find_synergies(all_words)
            synergy_words = []
            for s in synergies:
                if isinstance(s, list): synergy_words.extend(s)
                elif isinstance(s, str): synergy_words.append(s)
            if synergy_words: parts.extend(synergy_words[:3])
        except Exception:
            pass

        # 场景丰富度
        scene_richness = self._get_scene_richness(parsed.get("subject", ""))
        if scene_richness: parts.extend(scene_richness[:2])

        # 色彩控制
        color_palette = self._get_color_palette(parsed.get("cultural_context"))
        if color_palette: parts.extend(color_palette[:2])

        # 清理并拼接
        prompt = ", ".join([p for p in parts if p and p.strip()])

        # 排除词过滤
        if exclude_words:
            for word in exclude_words:
                prompt = prompt.replace(word, "")

        # 去重
        words = [w.strip() for w in prompt.split(",")]
        seen = set()
        unique_words = []
        for word in words:
            word_lower = word.lower()
            if word_lower not in seen and word:
                seen.add(word_lower)
                unique_words.append(word)
        prompt = ", ".join(unique_words)

        # 清理多余逗号和空格
        prompt = re.sub(r',\s*,', ',', prompt)
        prompt = re.sub(r'^\s*,\s*', '', prompt)
        prompt = re.sub(r'\s*,\s*$', '', prompt)

        # 长度截断
        max_words = config_manager.get("config.json", "max_prompt_words", 45)
        prompt = self._trim_prompt(prompt, max_words)

        return prompt
    
    def _get_default_lighting(self, subject: str) -> str:
        """获取默认光影"""
        subject_lower = subject.lower()
        if any(k in subject_lower for k in ["horror", "abandoned", "dark"]):
            return "dim light, deep shadows, atmospheric fog"
        elif any(k in subject_lower for k in ["water", "ocean", "lake"]):
            return "sunlight reflections, caustics, shimmering light"
        elif any(k in subject_lower for k in ["flower", "garden", "spring"]):
            return "soft diffused light, gentle shadows"
        elif any(k in subject_lower for k in ["city", "cyber", "neon"]):
            return "neon glow, colorful reflections, urban lighting"
        elif any(k in subject_lower for k in ["mountain", "landscape", "valley"]):
            return "natural lighting, golden hour, atmospheric perspective"
        return "dramatic lighting, volumetric light"
    
    def _get_default_view(self, subject: str) -> str:
        """获取默认视角"""
        subject_lower = subject.lower()
        if any(k in subject_lower for k in ["portrait", "face", "girl", "boy", "person"]):
            return "portrait composition, shallow depth of field"
        elif any(k in subject_lower for k in ["city", "building", "architecture", "skyline"]):
            return "wide angle, deep depth of field, architectural composition"
        elif any(k in subject_lower for k in ["dragon", "creature", "monster", "beast"]):
            return "dynamic angle, dramatic composition"
        elif any(k in subject_lower for k in ["flower", "plant", "nature", "macro"]):
            return "close-up, macro photography, bokeh background"
        elif any(k in subject_lower for k in ["landscape", "mountain", "valley", "forest"]):
            return "panoramic view, rule of thirds, atmospheric perspective"
        return ""
    
    def _get_quality(self, parsed: Dict, exclude_words: List[str]) -> List[str]:
        """获取质量关键词"""
        quality = list(parsed["quality"])
        subject_lower = parsed["subject"].lower() if parsed["subject"] else ""
        
        if any(k in subject_lower for k in ["portrait", "face", "girl", "boy", "person"]):
            if not any(e in "detailed face" for e in exclude_words):
                quality.append("detailed face, detailed eyes, skin texture")
        elif any(k in subject_lower for k in ["dragon", "creature", "monster"]):
            if not any(e in "detailed scales" for e in exclude_words):
                quality.append("detailed scales, intricate details, realistic textures")
        elif any(k in subject_lower for k in ["city", "building", "architecture"]):
            quality.append("detailed architecture, sharp lines, intricate details")
        elif any(k in subject_lower for k in ["flower", "plant", "nature"]):
            if not any(e in "single flower" for e in exclude_words):
                quality.append("detailed petals, vibrant colors, natural textures")
        elif any(k in subject_lower for k in ["landscape", "mountain", "forest", "valley"]):
            quality.append("vast landscape, atmospheric depth, natural beauty")
        
        if len(quality) < 4: quality.append("sharp focus")
        if len(quality) < 5: quality.append("8k resolution")
        if len(quality) < 6: quality.append("highly detailed")
        
        return quality
    
    def _get_scene_richness(self, subject: str) -> List[str]:
        """获取场景丰富度关键词"""
        subject_lower = subject.lower()
        
        if any(k in subject_lower for k in ["city", "urban", "street"]):
            return ["busy streets", "atmospheric haze", "layered buildings"]
        elif any(k in subject_lower for k in ["forest", "jungle", "woodland"]):
            return ["dense foliage", "dappled light", "moss-covered ground"]
        elif any(k in subject_lower for k in ["ocean", "sea", "underwater"]):
            return ["light rays", "floating particles", "depth layers"]
        elif any(k in subject_lower for k in ["mountain", "peak", "cliff"]):
            return ["misty valleys", "distant peaks", "rocky terrain"]
        elif any(k in subject_lower for k in ["castle", "palace", "fortress"]):
            return ["stone textures", "dramatic architecture", "ancient details"]
        return []
    
    def _get_color_palette(self, cultural_context: str) -> List[str]:
        """获取色彩控制关键词"""
        if cultural_context == "chinese":
            return ["rich reds", "golden accents", "jade greens"]
        elif cultural_context == "japanese":
            return ["subtle pastels", "natural tones", "harmonious colors"]
        elif cultural_context == "western":
            return ["vibrant colors", "dramatic contrasts", "bold tones"]
        return []


import re

# 全局构建器实例
builder = PromptBuilder()
