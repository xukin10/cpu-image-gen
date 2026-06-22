"""
词汇管理器 - 统一管理中英文词汇映射
"""

import json
import os
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class VocabularyManager:
    """词汇管理器"""
    
    def __init__(self):
        self._vocabulary = None
    
    @property
    def vocabulary(self) -> Dict:
        if self._vocabulary is None:
            self._load_vocabulary()
        return self._vocabulary
    
    def _load_vocabulary(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "configs", "vocabulary.json"
        )
        try:
            with open(path, "r", encoding="utf-8") as f:
                self._vocabulary = json.load(f)
        except Exception as e:
            logger.error(f"加载词汇库失败: {e}")
            self._vocabulary = {"categories": {}}
    
    def translate(self, chinese: str) -> str:
        categories = self.vocabulary.get("categories", {})
        for cat_name, cat_data in categories.items():
            words = cat_data.get("words", {})
            if chinese in words:
                return words[chinese]
        return chinese
    
    def get_category_words(self, category: str) -> Dict[str, str]:
        return self.vocabulary.get("categories", {}).get(category, {}).get("words", {})
    
    def get_all_categories(self) -> List[str]:
        return list(self.vocabulary.get("categories", {}).keys())
    
    def get_stats(self) -> Dict:
        categories = self.vocabulary.get("categories", {})
        total_words = sum(len(cat_data.get("words", {})) for cat_data in categories.values())
        return {"total_words": total_words, "categories": len(categories)}


vocab_manager = VocabularyManager()
