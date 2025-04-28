import pytest
import yaml

import pytest
import requests
import yaml

# 加载 YAML 测试用例
def load_test_cases(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# 测试数据驱动
test_cases = load_test_cases("test_cases.yml")

@pytest.mark.parametrize("api_test", test_cases)
def test_api(api_test):
    """
    使用 pytest 执行接口测试
    """
    base_url = "http://localhost:8000"  # 替换为实际的接口服务地址

    # 遍历接口的测试用例
    for case in api_test["test_cases"]:
        name = case["name"]  # 测试用例名称
        request_data = case["request"]  # 请求数据
        expected_response = case["expected_response"]  # 期望响应

        # 打印测试用例名称
        print(f"执行测试用例: {name}")

        # 根据方法调用接口
        if api_test["method"] == "POST":
            response = requests.post(base_url + api_test["api"], json=request_data)
        elif api_test["method"] == "GET":
            response = requests.get(base_url + api_test["api"], params=request_data)
        else:
            pytest.fail(f"未支持的 HTTP 方法: {api_test['method']}")

        # 验证响应
        assert response.status_code == 200, f"HTTP 状态码错误: {response.status_code}"
        actual_response = response.json()
        for key, value in expected_response.items():
            assert actual_response.get(key) == value, f"响应字段 {key} 校验失败，期望: {value}，实际: {actual_response.get(key)}"
