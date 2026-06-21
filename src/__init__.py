"""
CPU Image Gen - 自然语言 Prompt 架构
"""

__version__ = "1.0.0"
__author__ = "CPU Image Gen Team"

# 导入核心模块
from .core import parser, builder
from .entities import cultural_resolver, template_manager
from .utils import config_manager, logger

# 保持向后兼容的导入
from .prompt_builder import (
    parse_input,
    build_prompt,
    generate_image,
    main,
    TEMPLATES,
    TEMPLATE_CATEGORIES,
    CULTURAL_ENTITIES,
    ENTITY_KEYWORDS,
    MODEL_CONFIGS,
    select_template,
    generate_prompt_from_template,
    build_video_prompt,
    build_3d_prompt,
    get_video_keywords,
    get_3d_keywords,
    get_model_config,
)
