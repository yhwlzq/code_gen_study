import json
import re
from typing import List, Dict, Generator, Any, Optional
from enum import Enum
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llama_index.core.llms import CustomLLM, CompletionResponse, LLMMetadata
from llama_index.core.llms.callbacks import llm_completion_callback

class ResponseCleaner:
    """响应内容清洗工具类"""

    @staticmethod
    def clean_response(text: str) -> str:
        """
        清洗LLM响应内容
        1. 去除内部思考标记（如<think>）
        2. 去除多余空行
        3. 规范化格式
        """
        # 去除所有类似<think>...</think>的标记
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # 去除其他可能的内部分析标记
        text = re.sub(r'\[内部思考\].*?\[/内部思考\]', '', text, flags=re.DOTALL)
        # 去除多余空行
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()


class DeepSeekLLM(CustomLLM):
    """基于 Ollama 的 DeepSeek LLM 封装"""

    base_url: str = Field(default="http://localhost:11434", description="Ollama 服务器地址")
    model_name: str = Field(default="deepseek-r1:latest", description="Ollama 模型名称")
    temperature: float = Field(default=0.7, description="生成温度")
    max_tokens: int = Field(default=2048, description="最大 token 数")
    timeout: int = Field(default=60, description="请求超时时间(秒)")

    def __init__(self, base_url: str = None, model_name: str = None, **kwargs):
        super().__init__(**kwargs)
        if base_url:
            self.base_url = base_url
        if model_name:
            self.model_name = model_name

    @property
    def metadata(self) -> LLMMetadata:
        """获取 LLM 元数据"""
        return LLMMetadata(
            model_name=self.model_name,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """同步生成文本"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return CompletionResponse(text=result["message"]["content"])
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API 请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"解析API响应失败: {str(e)}")
        except KeyError as e:
            raise Exception(f"API响应格式不正确，缺少字段: {str(e)}")

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> Generator[CompletionResponse, None, None]:
        """流式生成文本"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": True,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_tokens,
                    },
                },
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()

            for chunk in response.iter_lines():
                if chunk:
                    try:
                        data = json.loads(chunk.decode("utf-8"))
                        if "message" in data and data["message"]["content"]:
                            content = data["message"]["content"]
                            yield CompletionResponse(text=content, delta=content)
                    except json.JSONDecodeError:
                        continue  # 跳过无效的JSON数据

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama 流式请求失败: {str(e)}")
