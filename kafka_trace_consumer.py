import json, time
from typing import Any, Dict, List, Tuple
from kafka import KafkaConsumer
from config import (
    KAFKA_BOOTSTRAP,
    RAW_TOPIC,
    TRACE_INACTIVITY_SEC,
    TRACE_MAX_EVENTS,
    FLUSH_TICK_SEC,
)
from preprocess import extract_events_from_otlp, build_clean_text, build_summary_meta
from summarize_embed import summarize_korean, save_trace_summary


class TraceAggregator:
    def __init__(self, inactivity_sec: float, max_events: int):
        self.inactivity = inactivity_sec
        self.max_events = max_events
        self.buckets: Dict[str, List[Dict[str, Any]]] = {}
        self.last_seen: Dict[str, float] = {}

    def add_payload(self, payload: Dict[str, Any]):
        evs = extract_events_from_otlp(payload)
        now = time.time()
        for e in evs:
            tid = e.get("trace_id") or f"no-trace:{e.get('span_id')}"
            self.buckets.setdefault(tid, []).append(e)
            self.last_seen[tid] = now

    def pop_ready(self):
        now = time.time()
        ready_ids = []
        for tid, ts in list(self.last_seen.items()):
            if (now - ts) >= self.inactivity or len(
                self.buckets.get(tid, [])
            ) >= self.max_events:
                ready_ids.append(tid)
        out = []
        for tid in ready_ids:
            evs = self.buckets.pop(tid, [])
            self.last_seen.pop(tid, None)
            if evs:
                out.append((tid, evs))
        return out


def run():
    agg = TraceAggregator(TRACE_INACTIVITY_SEC, TRACE_MAX_EVENTS)
    consumer = KafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="trace-summary-writer",
        consumer_timeout_ms=0,
        max_poll_records=50,
    )
    print(f"[INFO] Consuming topic='{RAW_TOPIC}' @ {KAFKA_BOOTSTRAP}")

    last_check = time.time()
    for msg in consumer:
        try:
            payload = msg.value
            agg.add_payload(payload)
            now = time.time()
            if now - last_check >= FLUSH_TICK_SEC:
                last_check = now
                for trace_id, evs in agg.pop_ready():
                    clean = build_clean_text(evs)
                    meta = build_summary_meta(evs)
                    summary = summarize_korean(clean)
                    doc_id = save_trace_summary(trace_id, summary, meta)
                    print(f"[OK] upsert trace_summary id={doc_id} events={len(evs)}")
        except Exception as e:
            print(f"[ERR] {e}")


if __name__ == "__main__":
    run()
