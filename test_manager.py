import json
from typing import List, Dict, Optional,Any
from pydantic import BaseModel
from datetime import datetime
import os,re


# 定义数据模型
class TestStep(BaseModel):
    step: int
    action: str
    test_data: Optional[Dict[str, str]] = None

class ExpectedResult(BaseModel):
    description: str
    conditions: Optional[List[str]] = None

class TestCase_bak(BaseModel):
    """测试用例模型"""
    title: str
    description: str
    test_type: str  # 'functional', 'api', 'automation'
    prerequisites: List[str]
    steps: List[TestStep]
    expected_results: List[ExpectedResult]
    test_data: Dict[str, Dict[str, str]]  # 修改为字典结构


class Step(BaseModel):
    step: int
    action: str
    input: Dict[str, str] = None
    username: str = None
    password: str = None
    account: str = None

class TestCase(BaseModel):
    title: str
    description: str
    test_type: str = 'api'  # 默认值
    prerequisites: List[str]
    steps: List[Any]
    expected_results: List[Any]  # 改为 List[Any]，可以接受任何类型
    test_data: Dict[Any, Any]


def save_testcase_to_file(test_case: TestCase, filename: str = None):
    """
    将TestCase对象保存为格式化的JSON文件

    参数:
        test_case: TestCase对象
        filename: 保存的文件名（可选）
    """
    # 如果没有指定文件名，使用测试用例标题+时间戳
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in test_case.title if c.isalnum() or c in " _-")
        filename = f"testcase_{safe_title}_{timestamp}.json"

    # 确保目录存在
    os.makedirs("testcases", exist_ok=True)
    filepath = os.path.join("testcases", filename)

    # 转换为字典（使用Pydantic的dict方法保留所有字段）
    testcase_dict = test_case.dict()

    # 添加元信息
    testcase_dict["_meta"] = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0"
    }

    # 保存为格式化的JSON文件
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(testcase_dict, f, indent=4, ensure_ascii=False)

    print(f"测试用例已保存到: {filepath}")
    return filepath
