import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs" / "仍需地图查询_110条_GoogleMaps查询表_补充读取后.csv"
OUT_DIR = ROOT / "work" / "maps_reads_next"
DOKOBOT = "/Users/g90/.codex/vendor_imports/bin/dokobot"
TARGET_STATUSES = {"Google有文字候选无坐标", "未确认"}


def safe_name(text: str) -> str:
    chars = []
    for ch in text.strip():
        if ch.isalnum() or ch in "-_":
            chars.append(ch)
        elif ch.isspace():
            chars.append("_")
    return ("".join(chars).strip("_") or "item")[:48]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    targets = [
        (idx, row)
        for idx, row in enumerate(rows, start=1)
        if row.get("Google搜索状态") in TARGET_STATUSES
    ]
    print(f"targets={len(targets)}", flush=True)

    for idx, row in targets:
        name = row.get("提取餐厅/地点名") or row.get("标题/名称") or row.get("序号/名称")
        out = OUT_DIR / f"{idx:03d}_{safe_name(name)}.md"
        if out.exists() and out.stat().st_size > 200:
            text = out.read_text(encoding="utf-8", errors="ignore")
            if "No local bridge running" not in text:
                print(f"skip {idx} {name}", flush=True)
                continue
        print(f"read {idx} {name}", flush=True)
        proc = subprocess.run(
            [DOKOBOT, "read", "--local", row["Google Maps查询URL"], "--screens", "5", "--timeout", "120000"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=150,
        )
        out.write_text(proc.stdout, encoding="utf-8")
        print(f"done {idx} rc={proc.returncode} bytes={out.stat().st_size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
