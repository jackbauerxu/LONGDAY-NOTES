import subprocess
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "work" / "maps_user_addresses"
DOKOBOT = "/Users/g90/.codex/vendor_imports/bin/dokobot"

ITEMS = [
    ("Lesnoy", "Lesnoy Istiqbol street 45 Tashkent Uzbekistan"),
    ("ORA", "ORA Tashkent Istiqbol street 41 floor 2"),
    ("COCOCHOU_BAKERY", "COCOCHOU BAKERY Mirobod 39 Tashkent Uzbekistan"),
    ("muza_kitchen", "muza kitchen Mahtumquli Street 45 Tashkent"),
    ("JIANG_HU_HUOGUO", "JIANG HU HUOGUO 煮江湖火锅 Arnasay 16B Tashkent"),
    ("湘味小厨", "湘味小厨 Kichik Beshagach 128 Tashkent"),
    ("Caravan", "Caravan 112 Abdurahman Jami Street Tashkent Uzbekistan"),
    ("OKO", "Oko 152/1 Buyuk Ipak Yuli Road Tashkent"),
]


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, query in ITEMS:
        out = OUT_DIR / f"{name}.md"
        if out.exists() and out.stat().st_size > 200:
            text = out.read_text(encoding="utf-8", errors="ignore")
            if "No local bridge running" not in text:
                print(f"skip {name}", flush=True)
                continue
        url = "https://www.google.com/maps/search/" + quote(query)
        print(f"read {name}: {query}", flush=True)
        proc = subprocess.run(
            [DOKOBOT, "read", "--local", url, "--screens", "5", "--timeout", "120000"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=150,
        )
        out.write_text(proc.stdout, encoding="utf-8")
        print(f"done {name} rc={proc.returncode} bytes={out.stat().st_size}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
