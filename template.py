import json
import re
from typing import List, Dict, Generator, Any, Optional
from enum import Enum
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback
from test_manager import TestCase, save_testcase_to_file, TestStep, ExpectedResult

class TemplateType(Enum):
    """模板类型枚举，便于管理和使用"""
    ANALYZER = "analyzer"
    TESTCASE = "testcase"
    API_TESTCASE = "api_testcase"
    COMMON_TESTCASE = "common_testcase"



class Templates:
    """优化后的模板管理类，使用字典存储模板，便于扩展和维护"""

    _TEMPLATES = {
        TemplateType.ANALYZER: """
        你是一个专业的测试分析师，请帮助分析需求文档并提取关键功能点。

        请分析以下需求文档并列出关键功能点：

        {requirements_text}


        请提供：
        1- 请使用Markdown格式回复，并确保各部分清晰明确

        请直接输出最终答案，不要包含任何<think>这样的内部思考过程标记
        """,

        TemplateType.TESTCASE: """
        请严格按照以下JSON格式生成响应：
     {{
        "title": "测试用例标题",
        "description": "测试用例描述",
        "test_type": "api",
        "prerequisites": ["前置条件1", "前置条件2"],
        "steps": ["步骤1", "步骤2"],
        "expected_results": ["预期结果1", "预期结果2"],
       "test_data": {{
          "key1": "value1",
          "key2": "value2"
      }}
  }}
  
  请基于以下内容生成测试用例（请确保生成的是合法的JSON格式）：
  {content}
        """,

        TemplateType.API_TESTCASE: """
        请为以下API功能点生成测试用例：
        功能：{feature}

        请包含以下信息：
         1. API接口名称和路径
         2. 请求方法（GET/POST等）
         3. 请求参数和格式
         4. 预期响应和状态码
         5. 异常情况测试
         6. 测试数据示例

         请确保生成的响应是合法的JSON格式。
        """,

        TemplateType.COMMON_TESTCASE: """
        请为以下功能点生成{test_type}测试用例：
        功能：{feature}

        请包含以下信息：
         1. 测试用例标题
         2. 测试描述
         3. 前置条件
         4. 测试步骤
         5. 预期结果
         6. 测试数据

         请确保生成的响应是合法的JSON格式。
        """,


    }

    @classmethod
    def get_template(cls, template_type: TemplateType) -> str:
        """获取指定类型的模板"""
        return cls._TEMPLATES.get(template_type, "")

    @classmethod
    def format_prompt(cls, template_type: TemplateType, **kwargs) -> str:
        """
        格式化模板
        :param template_type: 模板类型枚举
        :param kwargs: 模板需要的参数
        :return: 格式化后的提示文本
        """
        template = cls.get_template(template_type)
        if not template:
            raise ValueError(f"模板类型 {template_type} 不存在")
        return template.format(**kwargs)
