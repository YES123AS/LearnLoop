import os
import base64
from pathlib import Path
from typing import List, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

try:
    from .langchain_runtime import invoke_messages_with_fallback, to_langchain_messages
except ImportError:
    from langchain_runtime import invoke_messages_with_fallback, to_langchain_messages


PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_ENV_FILE = Path(
    os.getenv(
        "SPARK_ENV_FILE",
        str(PROJECT_ROOT / ".local-data" / "config" / "spark.env"),
    )
)
load_dotenv(LOCAL_ENV_FILE, override=True)

DEFAULT_SPARK_BASE_URL = "https://spark-api-open.xf-yun.com/agent/v1"
DEFAULT_SPARK_MODEL = "spark-x"
DEFAULT_SPARK_MODEL_CANDIDATES = "spark-x"


def _normalize_base_url(base_url: str) -> str:
    """
    OpenAI SDK 会自动在 base_url 后拼接 /chat/completions。
    如果用户从控制台复制了完整接口地址，这里去掉最后的接口路径。
    """
    cleaned = (base_url or DEFAULT_SPARK_BASE_URL).strip().rstrip("/")
    suffix = "/chat/completions"
    if cleaned.endswith(suffix):
        cleaned = cleaned[:-len(suffix)]
    return cleaned


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def _split_models(value: str) -> List[str]:
    models = []
    for item in (value or "").split(","):
        model = item.strip()
        if model and model not in models:
            models.append(model)
    return models


def _is_invalid_model_error(error: Exception) -> bool:
    message = str(error).lower()
    return "invalid param model" in message or "invalid model" in message


class SparkX2Client:
    """
    讯飞星火 X2 / X2-Flash 大模型调用模块

    作用：
    1. 封装讯飞星火 WebAPI
    2. 输入用户问题
    3. 返回模型回答
    4. 支持多轮对话
    5. 可按模型能力开启或关闭深度思考参数
    """

    def __init__(self):
        self.api_password = os.getenv("SPARK_API_PASSWORD")
        self.base_url = _normalize_base_url(os.getenv("SPARK_BASE_URL", DEFAULT_SPARK_BASE_URL))
        self.model = os.getenv("SPARK_MODEL", DEFAULT_SPARK_MODEL)
        self.model_candidates = _split_models(
            os.getenv("SPARK_MODEL_CANDIDATES", f"{self.model},{DEFAULT_SPARK_MODEL_CANDIDATES}")
        )
        self.user = os.getenv("SPARK_USER", "softwarecup")
        self.enable_thinking = _env_flag("SPARK_ENABLE_THINKING", False)

        if not self.api_password:
            raise ValueError(
                "未找到 SPARK_API_PASSWORD，请检查 .local-data/config/spark.env 是否配置正确"
            )

        self.client = OpenAI(
            api_key=self.api_password,
            base_url=self.base_url
        )

    def chat(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "你是一个个性化学习助手，请用清晰、通俗、直接的方式回答学生的问题。",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        thinking: str = "disabled"
    ) -> str:
        """
        调用讯飞星火模型

        参数说明：
        user_input: 用户输入的问题
        history: 历史对话列表，用于多轮对话
        system_prompt: 系统提示词
        temperature: 生成随机性，越高越发散
        max_tokens: 最大输出长度
        thinking: 深度思考模式，可选 enabled / disabled / auto

        返回：
        模型最终回答文本
        """

        if history is None:
            history = []

        try:
            messages = to_langchain_messages(
                system_prompt=system_prompt,
                history=history,
                user_input=user_input,
            )
            return invoke_messages_with_fallback(
                messages,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking=thinking,
            )
        except Exception as e:
            raise RuntimeError(f"讯飞星火模型调用失败：{e}")

    def chat_with_image(
        self,
        user_input: str,
        image_bytes: bytes,
        mime_type: str = "image/png",
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "你是一个能够理解图片内容的学习辅导助手，请先识别图片内容，再结合学生问题给出清晰回答。",
        temperature: float = 0.4,
        max_tokens: int = 2048,
        thinking: str = "disabled"
    ) -> str:
        """
        使用 OpenAI 兼容的多模态消息格式发送图片。
        若当前讯飞模型不支持图片，接口会返回明确错误并向上抛出。
        """

        if history is None:
            history = []

        encoded = base64.b64encode(image_bytes).decode("ascii")
        data_url = f"data:{mime_type};base64,{encoded}"
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            *history,
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_input
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_url
                        }
                    }
                ]
            }
        ]

        try:
            last_error = None
            for model in self.model_candidates:
                request_kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": False,
                    "user": self.user
                }
                if self.enable_thinking:
                    request_kwargs["extra_body"] = {
                        "thinking": {
                            "type": thinking
                        }
                    }

                try:
                    response = self.client.chat.completions.create(**request_kwargs)
                    self.model = model
                    return response.choices[0].message.content
                except Exception as error:
                    last_error = error
                    if not _is_invalid_model_error(error):
                        break

            raise last_error

        except Exception as e:
            raise RuntimeError(f"讯飞星火图片理解调用失败：{e}")
        
    def chat_stream(
        self,
        user_input: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: str = "你是一个个性化学习助手，请用清晰、通俗、直接的方式回答学生的问题。",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        thinking: str = "disabled"
    ) -> str:
        """
        流式调用讯飞星火模型

        作用：
        1. 模型生成过程中，终端实时显示回答
        2. 最后仍然返回完整回答文本
        """

        if history is None:
            history = []

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]

        messages.extend(history)

        messages.append(
            {
                "role": "user",
                "content": user_input
            }
        )

        try:
            print(f"\n[INFO] 正在连接讯飞星火模型：{self.model} ...")
            print("[INFO] 正在发送问题给模型...")
            print("[INFO] 模型开始生成回答：\n")

            response = None
            last_error = None
            for model in self.model_candidates:
                request_kwargs = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                    "user": self.user
                }
                if self.enable_thinking:
                    request_kwargs["extra_body"] = {
                        "thinking": {
                            "type": thinking
                        }
                    }

                try:
                    response = self.client.chat.completions.create(**request_kwargs)
                    self.model = model
                    break
                except Exception as error:
                    last_error = error
                    if not _is_invalid_model_error(error):
                        break

            if response is None:
                raise last_error

            full_answer = ""

            for chunk in response:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if delta and delta.content:
                    content = delta.content
                    print(content, end="", flush=True)
                    full_answer += content

            print("\n\n[INFO] 模型回答生成完成。")

            return full_answer

        except Exception as e:
            print("[ERROR] 流式调用失败。")
            raise RuntimeError(f"讯飞星火模型流式调用失败：{e}")


def call_spark_x2(prompt: str) -> str:
    """
    简单调用函数：
    输入 prompt，返回模型回答
    """
    client = SparkX2Client()
    return client.chat(prompt)


if __name__ == "__main__":
    spark = SparkX2Client()

    history = []

    while True:
        question = input("\n请输入你的问题，输入 q 退出：")

        if question.lower() == "q":
            break

        answer = spark.chat(
            user_input=question,
            history=history
        )

        print("\n模型回答：")
        print(answer)

        history.append({
            "role": "user",
            "content": question
        })

        history.append({
            "role": "assistant",
            "content": answer
        })
