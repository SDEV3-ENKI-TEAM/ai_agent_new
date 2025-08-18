from typing import Dict, Any
from openai import OpenAI
from config import OPENAI_API_KEY, CHAT_MODEL
from chroma_setup import upsert_trace_summary

_client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = (
    "당신은 사이버 보안 분석가입니다. "
    "주어진 Sysmon/네트워크 이벤트를 1~2문장 한국어로 간결하게 요약하세요. "
    "핵심 행위, 주체(프로세스), 대상(도메인/IP/포트)를 포함하세요."
)


def summarize_korean(clean_text: str):
    user = f"다음은 한 트레이스의 핵심 행위 로그입니다:\n\n{clean_text}\n\n위 내용을 1~2문장 한국어로 요약해 주세요."
    resp = _client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def save_trace_summary(trace_id: str, summary: str, meta: Dict[str, Any]):
    return upsert_trace_summary(trace_id, summary, meta)
