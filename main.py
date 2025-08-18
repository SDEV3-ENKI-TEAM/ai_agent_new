import json
from pathlib import Path
from pipeline import process_payload

if __name__ == "__main__":
    payload = json.loads(Path("./trace.json").read_text(encoding="utf-8"))
    results = process_payload(payload)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"[INFO] 저장 완료: {len(results)} traces")
