"""
场景模板模块
"""

from typing import Dict, List, Optional, Tuple

from ..utils.config import config_manager


class TemplateManager:
    """模板管理器"""
    
    def __init__(self):
        self._templates = None
        self._categories = None
    
    @property
    def templates(self) -> Dict:
        if self._templates is None:
            self._templates = config_manager.load("templates.json")
        return self._templates
    
    @property
    def categories(self) -> Dict[str, List[Tuple[str, str]]]:
        if self._categories is None:
            self._categories = {}
            for key, template in self.templates.items():
                cat = template.get("category", "其他")
                if cat not in self._categories:
                    self._categories[cat] = []
                self._categories[cat].append((key, template["label"]))
        return self._categories
    
    def get_template(self, key: str) -> Optional[Dict]:
        """获取模板"""
        return self.templates.get(key)
    
    def get_category_list(self) -> List[str]:
        """获取分类列表"""
        return list(self.categories.keys())
    
    def get_templates_in_category(self, category: str) -> List[Tuple[str, str]]:
        """获取分类下的模板"""
        return self.categories.get(category, [])
    
    def generate_prompt(self, template: Dict, user_input: str) -> str:
        """根据模板生成 prompt"""
        base = template.get("base_prompt", "{subject}")
        quality = template.get("quality_additions", [])
        composition = template.get("composition", "")
        lighting = template.get("lighting", "")
        
        prompt = base.replace("{subject}", user_input)
        if quality: prompt += ", " + ", ".join(quality[:3])
        if composition: prompt += ", " + composition
        if lighting: prompt += ", " + lighting
        prompt += ", highly detailed, 8k"
        
        return prompt
    
    def select_interactive(self) -> Tuple[Optional[str], Optional[Dict]]:
        """交互式选择模板"""
        print("\n" + "=" * 50)
        print("  选择场景模板")
        print("=" * 50)
        
        cat_list = self.get_category_list()
        for i, cat in enumerate(cat_list, 1):
            templates = self.categories[cat]
            print(f"  [{i}] {cat} ({len(templates)}个)")
        
        print()
        cat_choice = input(">> 选择分类 (数字，直接回车跳过): ").strip()
        
        if not cat_choice or not cat_choice.isdigit():
            return None, None
        
        cat_idx = int(cat_choice) - 1
        if cat_idx < 0 or cat_idx >= len(cat_list):
            return None, None
        
        selected_cat = cat_list[cat_idx]
        templates = self.get_templates_in_category(selected_cat)
        
        print(f"\n  {selected_cat} 类模板：")
        for i, (key, label) in enumerate(templates, 1):
            print(f"  [{i}] {label}")
        
        print()
        tpl_choice = input(">> 选择模板 (数字): ").strip()
        
        if not tpl_choice or not tpl_choice.isdigit():
            return None, None
        
        tpl_idx = int(tpl_choice) - 1
        if tpl_idx < 0 or tpl_idx >= len(templates):
            return None, None
        
        tpl_key, tpl_label = templates[tpl_idx]
        return tpl_key, self.get_template(tpl_key)


# 全局模板管理器实例
template_manager = TemplateManager()
