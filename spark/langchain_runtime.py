"""LangChain runtime for the OpenAI-compatible Spark API.

This module is the provider boundary for the gradual migration. Application
code should depend on LangChain's chat-model and Runnable interfaces instead
of constructing an OpenAI SDK client directly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable, List, Optional

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI


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


def normalize_base_url(base_url: str) -> str:
    """Normalize a copied endpoint into the base URL expected by ChatOpenAI."""
    cleaned = (base_url or DEFAULT_SPARK_BASE_URL).strip().rstrip("/")
    suffix = "/chat/completions"
    if cleaned.endswith(suffix):
        cleaned = cleaned[: -len(suffix)]
    return cleaned


def env_flag(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def model_candidates() -> List[str]:
    primary = os.getenv("SPARK_MODEL", DEFAULT_SPARK_MODEL).strip()
    raw = os.getenv("SPARK_MODEL_CANDIDATES", primary)
    candidates: List[str] = []
    for item in raw.split(","):
        model = item.strip()
        if model and model not in candidates:
            candidates.append(model)
    if primary and primary not in candidates:
        candidates.insert(0, primary)
    return candidates or [DEFAULT_SPARK_MODEL]


def create_spark_chat_model(
    *,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    thinking: str = "disabled",
) -> ChatOpenAI:
    """Create a LangChain chat model for Spark's OpenAI-compatible endpoint."""
    api_password = os.getenv("SPARK_API_PASSWORD")
    if not api_password:
        raise ValueError(
            "未找到 SPARK_API_PASSWORD，请检查 .local-data/config/spark.env 是否配置正确"
        )

    extra_body = None
    if env_flag("SPARK_ENABLE_THINKING", False):
        extra_body = {"thinking": {"type": thinking}}

    return ChatOpenAI(
        model=model or os.getenv("SPARK_MODEL", DEFAULT_SPARK_MODEL),
        api_key=api_password,
        base_url=normalize_base_url(os.getenv("SPARK_BASE_URL", DEFAULT_SPARK_BASE_URL)),
        temperature=temperature,
        max_tokens=max_tokens,
        extra_body=extra_body,
        max_retries=2,
    )


def message_content_to_text(content: Any) -> str:
    """Normalize text or multimodal content blocks returned by LangChain."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return str(content or "")


def to_langchain_messages(
    *,
    system_prompt: str,
    history: Optional[Iterable[dict[str, Any]]] = None,
    user_input: Any,
) -> List[BaseMessage]:
    """Convert the project's existing message dictionaries to LangChain messages."""
    messages: List[BaseMessage] = [SystemMessage(content=system_prompt)]
    for item in history or []:
        role = str(item.get("role", "user"))
        content = item.get("content", "")
        if role == "assistant":
            messages.append(AIMessage(content=content))
        elif role == "system":
            messages.append(SystemMessage(content=content))
        else:
            messages.append(HumanMessage(content=content))
    messages.append(HumanMessage(content=user_input))
    return messages


def invoke_messages_with_fallback(
    messages: Iterable[BaseMessage],
    *,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    thinking: str = "disabled",
) -> str:
    """Invoke candidate Spark models through LangChain, preserving old fallback behavior."""
    last_error: Optional[Exception] = None
    message_list = list(messages)
    for model_name in model_candidates():
        try:
            response = create_spark_chat_model(
                model=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                thinking=thinking,
            ).invoke(message_list)
            return message_content_to_text(response.content)
        except Exception as error:  # provider errors are normalized by the caller
            last_error = error
            message = str(error).lower()
            if "invalid param model" not in message and "invalid model" not in message:
                break
    if last_error is None:
        raise RuntimeError("没有可用的讯飞星火模型候选项")
    raise last_error


def build_text_chain(
    *,
    system_prompt: str,
    user_template: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    thinking: str = "disabled",
) -> Runnable:
    """Build a reusable prompt -> model -> string LCEL chain."""
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("human", user_template)]
    )
    model = create_spark_chat_model(
        temperature=temperature,
        max_tokens=max_tokens,
        thinking=thinking,
    )
    return prompt | model | StrOutputParser()
