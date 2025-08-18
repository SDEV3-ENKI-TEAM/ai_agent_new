from typing import Any, Dict, List
from preprocess import (
    extract_events_from_otlp,
    group_by_trace,
    build_clean_text,
    build_summary_meta,
)
from summarize_embed import summarize_korean, save_trace_summary


def process_payload(payload: Dict[str, Any]):
    events = extract_events_from_otlp(payload)
    by_trace = group_by_trace(events)
    out: List[Dict[str, str]] = []

    for tid, evs in by_trace.items():
        clean = build_clean_text(evs)
        meta = build_summary_meta(evs)
        summary = summarize_korean(clean)  # 한국어 요약
        doc_id = save_trace_summary(tid, summary, meta)  # 요약을 임베딩하여 저장
        out.append({"trace_id": tid, "doc_id": doc_id, "summary": summary})
    return out
