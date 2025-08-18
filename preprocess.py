import ipaddress
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

NANO = 1_000_000_000


def _attr_value(v: Dict[str, Any]):
    if isinstance(v, dict):
        if "stringValue" in v:
            return v["stringValue"]
        if "intValue" in v:
            try:
                return int(v["intValue"])
            except Exception:
                return v["intValue"]
        if "boolValue" in v:
            return bool(v["boolValue"])
    return v


def _get_attr(attrs: List[Dict[str, Any]], key: str, default=None):
    for kv in attrs or []:
        if kv.get("key") == key:
            return _attr_value(kv.get("value", {}))
    return default


def _basename(p: Optional[str]):
    if not p:
        return p
    return p.replace("\\", "/").split("/")[-1]


def _port_fix(p: Any):
    try:
        p = int(p)
    except Exception:
        return None
    if p < 0:
        return (p + 65536) % 65536
    if 0 <= p <= 65535:
        return p
    return None


def _ip_or_none(s: Optional[str]):
    if not s:
        return None
    try:
        ipaddress.ip_address(s.split("%")[0])
        return s
    except Exception:
        if isinstance(s, str) and s.startswith("::ffff:"):
            return s.split("::ffff:")[-1]
        return None


def _safe_time_from_unix_nano(ns: str):
    try:
        ns = int(ns)
        dt = datetime.fromtimestamp(ns / NANO, tz=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def span_to_event(span: Dict[str, Any]):
    attrs = span.get("attributes", [])
    name = span.get("name", "") or ""
    proc_from_name, event_from_name = (
        (name.split("@", 1) + [None])[:2] if "@" in name else (None, None)
    )
    return {
        "trace_id": span.get("traceId"),
        "span_id": span.get("spanId"),
        "event_name": _get_attr(attrs, "EventName", event_from_name) or "",
        "timestamp_local": _get_attr(attrs, "TimeStamp"),
        "timestamp_utc": _get_attr(attrs, "UtcTime")
        or _safe_time_from_unix_nano(span.get("startTimeUnixNano", "")),
        "process_name": proc_from_name or _basename(_get_attr(attrs, "Image")),
        "process_path": _get_attr(attrs, "Image"),
        "process_id": _get_attr(attrs, "ProcessId"),
        "protocol": _get_attr(attrs, "Protocol"),
        "source_ip": _ip_or_none(_get_attr(attrs, "SourceIp")),
        "source_port": _port_fix(_get_attr(attrs, "SourcePort")),
        "destination_ip": _ip_or_none(_get_attr(attrs, "DestinationIp")),
        "destination_port": _port_fix(_get_attr(attrs, "DestinationPort")),
        "query_name": _get_attr(attrs, "QueryName"),
        "query_results": _get_attr(attrs, "QueryResults"),
        "command_line": _get_attr(attrs, "CommandLine"),
        "sigma_alert": _get_attr(attrs, "sigma.alert")
        or _get_attr(attrs, "sigma@alert"),
        "sigma_rule_title": _get_attr(attrs, "sigma.rule_title"),
    }


def extract_events_from_otlp(payload: Dict[str, Any]):
    events: List[Dict[str, Any]] = []
    for rs in payload.get("resourceSpans", []) or []:
        for ss in rs.get("scopeSpans", []) or []:
            for span in ss.get("spans", []) or []:
                events.append(span_to_event(span))
    return events


def group_by_trace(events: List[Dict[str, Any]]):
    d: Dict[str, List[Dict[str, Any]]] = {}
    for e in events:
        tid = e.get("trace_id") or f"no-trace:{e.get('span_id')}"
        d.setdefault(tid, []).append(e)
    return d


def build_clean_text(events: List[Dict[str, Any]]):
    lines: List[str] = []
    for e in events:
        ev = e.get("event_name", "")
        if "Dnsquery" in ev:
            lines.append(
                f"[DNS] {e.get('process_name')} -> {e.get('query_name')} / result={e.get('query_results')}"
            )
        elif "Networkconnectiondetected" in ev:
            lines.append(
                f"[NET] {e.get('process_name')} {e.get('source_ip')}:{e.get('source_port')} -> {e.get('destination_ip')}:{e.get('destination_port')} tcp"
            )
        elif "ProcessCreate" in ev:
            lines.append(
                f"[PROC+] {e.get('process_name')} pid={e.get('process_id')} cmd={e.get('command_line')}"
            )
        elif "Processterminated" in ev or "ProcessTerminate" in ev:
            lines.append(f"[PROC-] {e.get('process_name')} pid={e.get('process_id')}")
        else:
            lines.append(f"[{ev}] {e.get('process_name')} pid={e.get('process_id')}")
    return "\n".join([ln for ln in lines if ln])


def build_summary_meta(events: List[Dict[str, Any]]):
    event_types, proc_names, domains, dst_ips, dst_ports = (
        set(),
        set(),
        set(),
        set(),
        set(),
    )
    sigma_hit = False
    for e in events:
        if e.get("event_name"):
            event_types.add(e["event_name"])
        if e.get("process_name"):
            proc_names.add(e["process_name"])
        if e.get("query_name"):
            domains.add(e["query_name"])
        if e.get("destination_ip"):
            dst_ips.add(e["destination_ip"])
        if e.get("destination_port"):
            dst_ports.add(str(e["destination_port"]))
        if e.get("sigma_alert") or e.get("sigma_rule_title"):
            sigma_hit = True

    return {
        "event_types": sorted(event_types),
        "process_names": sorted(proc_names),
        "domains": sorted(domains),
        "dst_ips": sorted(dst_ips),
        "dst_ports": sorted(dst_ports),
        "sigma_hit": sigma_hit,
        "event_count": len(events),
    }
