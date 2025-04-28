import json
import re
from typing import List, Dict, Generator, Any, Optional
from enum import Enum
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback

class AITestGenerator:
    """AI测试用例生成器"""

    def __init__(self, llm: CustomLLM):
        load_dotenv()
        self.llm = llm

    def analyze_requirements(self, requirements_text: str) -> List[str]:
        try:
            print("正在分析需求文档...")
            prompt = Templates.format_prompt(
                TemplateType.ANALYZER,
                requirements_text=requirements_text
            )
            print(f"生成的提示词:\n{prompt}")
            response = self.llm.complete(prompt)
            result = response.text
            result = ResponseCleaner.clean_response(result)

            # 清理并分割结果
            return self._clean_and_split_result(result)

        except Exception as e:
            print(f"分析需求时出错: {e}")
            raise Exception(f"需求分析失败: {str(e)}")

    def generate_test_cases(self, feature: str, test_type: str) -> str:
        print("准备生成Test case...")
        prompt = Templates.format_prompt(TemplateType.API_TESTCASE,
                                         feature=feature) if test_type == 'api' else Templates.format_prompt(
            TemplateType.COMMON_TESTCASE, feature=feature, test_type=test_type)

        test_case = Templates.format_prompt(TemplateType.TESTCASE, content=prompt)
        print(f"生成的提示词:\n{test_case}")

        response = self.llm.complete(test_case)
        result = response.text
        result = ResponseCleaner.clean_response(result)
        match = re.search(r'```json\s*({[\s\S]*?})\s*```', result)
        if match:
            cleaned_json_str = match.group(1).strip()
            try:
                test_case = json.loads(cleaned_json_str)
                print(test_case)

                tc = TestCase(**test_case)
                print(tc)
                save_testcase_to_file(tc)

            except json.JSONDecodeError as e:
                print("\nJSON解析错误:", e)
        else:
            print("未找到有效的JSON数据")
        print(result)
        return result

    def _clean_and_split_result(self, result: str) -> List[str]:
        """清理并分割LLM返回的结果"""
        lines = [line.strip() for line in result.split("\n") if line.strip()]
        return [line for line in lines if not line.startswith(("1.", "2.", "3."))]

    def _parse_ai_response(self, response: str) -> dict:
        """解析AI响应并转换为字典格式"""
        try:
              # 首先尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            print("直接解析JSON失败，尝试修复格式...")
            try:
                json_str = self._extract_json_from_text(response)
                cleaned_json = self._clean_json_string(json_str)
                return json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                print(f"JSON解析失败: {e}")
                print("原始响应:", response)
                return self._create_fallback_test_case(response)

    def _extract_json_from_text(self, text: str) -> str:
        """从文本中提取JSON部分"""
        # 查找第一个 { 和最后一个 } 之间的内容
        json_match = re.search(r'({[\s\S]*})', text)
        if json_match:
            return json_match.group(1)
        return text

    def _clean_json_string(self, json_str: str) -> str:
        """清理和修复常见的JSON格式问题"""
         # 移除可能导致解析错误的Unicode字符
        json_str = json_str.encode('utf-8', 'ignore').decode('utf-8')
        json_str = re.sub(r'(?<!\\)"(\w+)"(?=:)', r'"\1"', json_str)  # 修复键的引号
        json_str = re.sub(r'(?<=: )"([^"]*?)(?<!\\)"(?=[,}\]])', r'"\1"', json_str)  # 修复值的引号
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)  # 移除尾随逗号
        return json_str

    def convert_steps(self,steps: List[str]) -> List[TestStep]:
        """将字符串步骤转换为TestStep对象列表"""
        converted = []
        for i, step in enumerate(steps, 1):
            # 提取步骤描述（去掉前面的编号）
            step_desc = re.sub(r'^\d+\.\s*', '', step)
            converted.append(TestStep(
                step=i,
                action=step_desc,
                test_data=None
            ))
        return converted

    def convert_expected_results(self,results: List[str]) -> List[ExpectedResult]:
        """将字符串预期结果转换为ExpectedResult对象列表"""
        return [ExpectedResult(description=re.sub(r'^\d+\.\s*', '', r)) for r in results]


def read_file(file_name: str) -> str:
    try:
        with open(file_name, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_name} 不存在")
    except IOError as e:
        raise IOError(f"读取文件 {file_name} 失败: {str(e)}")


if __name__ == "__main__":
    try:
        requirement = read_file("requirements.txt")

        llm = DeepSeekLLM()
        instance = AITestGenerator(llm)

        res = instance.analyze_requirements(requirement)
        print("分析结果:")
        for i, feature in enumerate(res, 1):
            print(f"{i}. {feature}")

        test_types = ['functional', 'api']
        for feature in res:
            feature_name = feature.strip().lower().replace(' ', '_')
            for test_type in test_types:
                print(f"\n正在生成 {test_type} 测试用例，功能点：{feature}")
                test_case = instance.generate_test_cases(feature, test_type)


    except Exception as e:
        print(f"程序运行出错: {str(e)}")
