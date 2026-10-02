import json
import re
from typing import Any, Optional, Type


def strip_json_markdown(text: str) -> str:
    """
    去掉大模型常见的 ```json ... ``` 包裹。
    """
    if not text:
        return ""

    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_text(text: str) -> Optional[str]:
    """
    从模型输出中提取 JSON 对象或 JSON 数组。
    """
    text = strip_json_markdown(text)

    if not text:
        return None

    if text.startswith("{") and text.endswith("}"):
        return text

    if text.startswith("[") and text.endswith("]"):
        return text

    obj_start = text.find("{")
    obj_end = text.rfind("}")

    if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
        return text[obj_start:obj_end + 1]

    arr_start = text.find("[")
    arr_end = text.rfind("]")

    if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
        return text[arr_start:arr_end + 1]

    return None


def safe_json_loads(
    text: str,
    default: Any = None,
    expected_type: Optional[Type] = None,
) -> Any:
    """
    安全解析 JSON；失败时返回 default。
    """
    json_text = extract_json_text(text)

    if not json_text:
        return default

    try:
        data = json.loads(json_text)
    except Exception:
        return default

    if expected_type is not None and not isinstance(data, expected_type):
        return default

    return data


def parse_json_or_raw(text: str) -> Any:
    """
    API 层使用：能解析就返回对象，不能解析就返回原始字符串。
    """
    data = safe_json_loads(text, default=None)

    if data is None:
        return text

    return data
