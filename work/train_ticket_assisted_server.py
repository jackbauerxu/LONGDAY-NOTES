from __future__ import annotations

import base64
import json
import os
import random
import re
import smtplib
import threading
import time
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Any

try:
    from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
    from fastapi.middleware.cors import CORSMiddleware
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Install server dependencies first: pip3 install fastapi uvicorn python-multipart playwright"
    ) from exc


APP_DIR = Path(os.getenv("TRAIN_TICKET_APP_DIR", Path(__file__).resolve().parent))
DATA_DIR = Path(os.getenv("TRAIN_TICKET_DATA_DIR", APP_DIR / "data"))
DATA_PATH = Path(os.getenv("TRAIN_TICKET_ORDERS_PATH", DATA_DIR / "train_ticket_orders.json"))
PROOF_DIR = Path(os.getenv("TRAIN_TICKET_PROOF_DIR", DATA_DIR / "payment_proofs"))
EMAIL_OUTBOX_DIR = Path(os.getenv("TRAIN_TICKET_EMAIL_OUTBOX_DIR", DATA_DIR / "email_outbox"))
ORDER_TTL_MINUTES = 20
BOOKING_URL = "https://tickets.kz/en/gd"
PAYMENT_SUCCESS_NOTICE = "付款成功后 3 小时内出票；如最终无票，100%退款。建议最好提前 1 到 2 天订票。"
EXCHANGE_MARKUP_RATE = 0.03
TOTAL_FEE_RATE = 0.20
SERVICE_FEE_RATE = TOTAL_FEE_RATE - EXCHANGE_MARKUP_RATE
DEFAULT_EXCHANGE_RATES = {
    "KZT": float(os.getenv("TRAIN_TICKET_RATE_KZT", "0.0145")),
    "UZS": float(os.getenv("TRAIN_TICKET_RATE_UZS", "0.000564")),
}
_rate_cache: dict[str, tuple[float, float]] = {}

STATION_ALIASES = {
    "阿拉木图-1": "Almaty-1",
    "阿拉木图1": "Almaty-1",
    "阿拉木图-2": "Almaty-2",
    "阿拉木图2": "Almaty-2",
    "almaty-1": "Almaty-1",
    "almaty-2": "Almaty-2",
    "алматы-1": "Almaty-1",
    "алматы-2": "Almaty-2",
    "阿斯塔纳": "Astana",
    "努尔苏丹": "Astana",
    "astana": "Astana",
    "астана": "Astana",
    "奇姆肯特": "Shymkent",
    "希姆肯特": "Shymkent",
    "shymkent": "Shymkent",
    "шымкент": "Shymkent",
    "突厥斯坦": "Turkistan",
    "turkistan": "Turkistan",
    "туркестан": "Turkistan",
    "塔什干": "Tashkent",
    "tashkent": "Tashkent",
    "ташкент": "Tashkent",
    "撒马尔罕": "Samarkand",
    "samarkand": "Samarkand",
    "самарканд": "Samarkand",
    "布哈拉": "Bukhara",
    "bukhara": "Bukhara",
    "бухара": "Bukhara",
    "希瓦": "Khiva",
    "khiva": "Khiva",
    "хива": "Khiva",
    "乌尔根奇": "Urgench",
    "urgench": "Urgench",
    "ургенч": "Urgench",
    "努库斯": "Nukus",
    "nukus": "Nukus",
    "нукус": "Nukus",
    "安集延": "Andijan",
    "andijan": "Andijan",
    "андижан": "Andijan",
    "费尔干纳": "Fergana",
    "fergana": "Fergana",
    "фергана": "Fergana",
}

STATION_SLUGS = {
    "Almaty-1": "almaty",
    "Almaty-2": "almaty",
    "Almaty": "almaty",
    "Astana": "astana",
    "Shymkent": "shymkent",
    "Turkistan": "turkestan",
    "Tashkent": "tashkent",
    "Samarkand": "samarkand",
    "Bukhara": "buhara-1",
    "Khiva": "hiva",
    "Urgench": "urgench",
    "Nukus": "nukus",
    "Andijan": "andijan-1",
    "Fergana": "fergana",
}


@dataclass
class TrainOrder:
    order_id: str
    status: str
    from_station: str
    from_station_query: str
    to_station: str
    to_station_query: str
    depart_date: str
    passengers: int
    seat_preference: str
    selected_train: dict[str, Any]
    passenger_info: str
    passenger_details: list[dict[str, str]]
    contact: str
    contact_wechat: str
    contact_phone: str
    contact_email: str
    ticket_currency: str
    ticket_total_local: float
    exchange_rate: float
    exchange_rate_used: float
    ticket_amount_cny: float
    service_fee_cny: float
    base_amount: float
    payable_amount: float
    expires_at: str
    created_at: str
    payment_ref: str = ""
    paid_amount: float | None = None
    paid_at: str = ""
    proof_path: str = ""
    browser_note: str = ""
    official_result: str = ""
    history: list[str] = field(default_factory=list)


app = FastAPI(title="Train Ticket Assisted Order Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("TRAIN_TICKET_ALLOWED_ORIGINS", "http://127.0.0.1:4173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
_lock = threading.Lock()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def utc_now() -> datetime:
    return datetime.utcnow()


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat() + "Z"


def load_orders() -> dict[str, TrainOrder]:
    if not DATA_PATH.exists():
        return {}
    raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    for item in raw.values():
        item.setdefault("from_station_query", item.get("from_station", ""))
        item.setdefault("to_station_query", item.get("to_station", ""))
        item.setdefault("passenger_details", [])
        item.setdefault("selected_train", {})
        item.setdefault("contact", "")
        item.setdefault("contact_wechat", "")
        item.setdefault("contact_phone", "")
        item.setdefault("contact_email", "")
        item.setdefault("ticket_currency", "CNY")
        item.setdefault("ticket_total_local", item.get("base_amount", 0))
        item.setdefault("exchange_rate", 1)
        item.setdefault("exchange_rate_used", 1)
        item.setdefault("ticket_amount_cny", item.get("base_amount", 0))
        item.setdefault("service_fee_cny", 0)
    return {order_id: TrainOrder(**item) for order_id, item in raw.items()}


def save_orders(orders: dict[str, TrainOrder]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(
        json.dumps({key: asdict(value) for key, value in orders.items()}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_history(order: TrainOrder, message: str) -> None:
    order.history.append(f"{iso(utc_now())} {message}")


def create_order_id(existing: dict[str, TrainOrder]) -> str:
    while True:
        order_id = f"A{random.randint(10000, 99999)}"
        if order_id not in existing:
            return order_id


def assign_payable_amount(base_amount: float, existing: dict[str, TrainOrder]) -> float:
    active_amounts = {
        round(order.payable_amount, 2)
        for order in existing.values()
        if order.status in {"created", "waiting_payment", "submitted"}
    }
    base = int(base_amount * 100) / 100
    for cents in range(1, 100):
        amount = round(base + cents / 100, 2)
        if amount not in active_amounts:
            return amount
    raise HTTPException(status_code=409, detail="No unique amount available right now")


def require_order(orders: dict[str, TrainOrder], order_id: str) -> TrainOrder:
    order = orders.get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


def parse_client_time(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid payment time") from exc


def fetch_live_exchange_rate(currency: str) -> float | None:
    currency = currency.upper()
    if currency == "CNY":
        return 1.0
    now = time.time()
    cached = _rate_cache.get(currency)
    if cached and now - cached[0] < 1800:
        return cached[1]
    url = f"https://api.frankfurter.app/latest?from={currency}&to=CNY"
    try:
        with urllib.request.urlopen(url, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
            rate = float(payload.get("rates", {}).get("CNY", 0))
    except Exception:
        return None
    if rate <= 0:
        return None
    _rate_cache[currency] = (now, rate)
    return rate


def get_exchange_rate(currency: str, explicit_rate: Any = None) -> float:
    if explicit_rate not in (None, ""):
        rate = float(explicit_rate)
    else:
        normalized_currency = currency.upper()
        rate = fetch_live_exchange_rate(normalized_currency) or DEFAULT_EXCHANGE_RATES.get(normalized_currency, 1.0)
    if rate <= 0:
        raise HTTPException(status_code=400, detail="Exchange rate must be greater than 0")
    return rate


def calculate_price(ticket_total_local: float, exchange_rate: float) -> dict[str, float]:
    ticket_amount_cny = ticket_total_local * exchange_rate
    exchange_fee_cny = ticket_amount_cny * EXCHANGE_MARKUP_RATE
    service_fee_cny = ticket_amount_cny * SERVICE_FEE_RATE
    subtotal_cny = ticket_amount_cny + exchange_fee_cny + service_fee_cny
    return {
        "exchange_rate_used": round(exchange_rate, 8),
        "ticket_amount_cny": round(ticket_amount_cny, 2),
        "service_fee_cny": round(service_fee_cny, 2),
        "subtotal_cny": round(subtotal_cny, 2),
    }


def zh_duration(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    match = re.fullmatch(r"(\d+)\s*h(?:ours?)?\s*(\d+)?\s*m(?:in(?:utes?)?)?", text, re.I)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2) or 0)
        return f"{hours}小时{minutes:02d}分钟"
    match = re.fullmatch(r"(\d+)\s*h(?:ours?)?", text, re.I)
    if match:
        return f"{int(match.group(1))}小时"
    return text


def parse_positive_int(value: Any, default: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(6, parsed))


def default_currency_for_departure(from_station: str, train_country: str = "") -> str:
    # The synchronized booking page is a Kazakhstan platform and often omits
    # the currency label in visible fare buttons. Treat unlabeled fares as KZT;
    # only switch to UZS when the page text explicitly says so.
    return "KZT"


def parse_time_minutes(value: str) -> int | None:
    match = re.search(r"(\d{1,2})[:：](\d{2})", value or "")
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def format_duration(depart_time: str, arrive_time: str, fallback: str = "") -> str:
    if fallback:
        return zh_duration(fallback)
    depart_minutes = parse_time_minutes(depart_time)
    arrive_minutes = parse_time_minutes(arrive_time)
    if depart_minutes is None or arrive_minutes is None:
        return "运行时长以系统同步为准"
    diff = arrive_minutes - depart_minutes
    if diff <= 0:
        diff += 24 * 60
    hours, minutes = divmod(diff, 60)
    return f"{hours}小时{minutes:02d}分钟"


def parse_price_text(text: str, default_currency: str) -> tuple[float, str]:
    cleaned = re.sub(r"\s+", " ", text or "")
    currency = default_currency
    if re.search(r"\bKZT\b|₸|тенге|тг", cleaned, re.I):
        currency = "KZT"
    elif re.search(r"\bUZS\b|сум|sum|so'm", cleaned, re.I):
        currency = "UZS"
    matches = re.findall(r"(\d[\d\s.,]*\d|\d+)", cleaned)
    if not matches:
        return 0.0, currency
    amounts: list[float] = []
    for item in matches:
        normalized = item.replace(" ", "")
        if currency in {"KZT", "UZS"}:
            normalized = re.sub(r"[,.]", "", normalized)
        else:
            normalized = normalized.replace(",", ".")
            if normalized.count(".") > 1:
                normalized = normalized.replace(".", "")
        try:
            amounts.append(float(normalized))
        except ValueError:
            continue
    if not amounts:
        return 0.0, currency
    amount = max(amounts)
    return amount, currency


def read_locator_text(row: Any, selector: str) -> str:
    if not selector:
        return ""
    locator = row.locator(selector)
    if locator.count() <= 0:
        return ""
    return locator.first.inner_text(timeout=3000).strip()


def build_seat_details(seat: str, schedule_index: int, seat_index: int, seat_count: int) -> list[str]:
    count = max(1, min(12, seat_count))
    car_no = f"{3 + schedule_index + seat_index:02d}"
    if "卧铺" in seat:
        berths = ["下铺", "中铺", "上铺", "下铺", "中铺", "上铺"]
        return [f"{car_no}车 {12 + schedule_index * 3 + index}{berths[(index + seat_index) % len(berths)]}" for index in range(count)]
    if "包厢" in seat:
        return [f"{car_no}车 {2 + schedule_index + index}号包厢" for index in range(count)]
    letters = ["A", "B", "C", "D", "F"]
    return [
        f"{car_no}车 {10 + schedule_index * 4 + index // len(letters)}{letters[(index + seat_index) % len(letters)]}"
        for index in range(count)
    ]


def build_seat_detail(seat: str, schedule_index: int, seat_index: int, passenger_count: int) -> str:
    return "、".join(build_seat_details(seat, schedule_index, seat_index, passenger_count))


def station_slug(station: str) -> str:
    normalized = normalize_station(station)
    slug = STATION_SLUGS.get(normalized)
    if slug:
        return slug
    return re.sub(r"[^a-z0-9-]+", "-", normalized.lower()).strip("-")


def format_ticket_date(value: str) -> str:
    try:
        parsed = datetime.strptime(str(value), "%Y-%m-%d")
    except ValueError:
        try:
            parsed = datetime.strptime(str(value), "%d.%m.%Y")
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid departure date") from exc
    return parsed.strftime("%d.%m.%Y")


def seat_preference_matches(preference: str, seat: str) -> bool:
    if not preference or preference == "任意可出票座席":
        return True
    haystack = seat.lower()
    if preference == "卧铺":
        return "sleeper" in haystack or "sleep" in haystack
    if "座席" in preference or "坐席" in preference or "二等座" in preference:
        return "seat" in haystack or "seating" in haystack
    if "包厢" in preference:
        return "compartment" in haystack or "cabin" in haystack or "sleeper" in haystack
    return preference.lower() in haystack


def normalize_seat_label(label: str) -> str:
    lowered = label.lower()
    if "1st" in lowered and "sleeper" in lowered:
        return "一等卧铺"
    if "2nd" in lowered and "sleeper" in lowered:
        return "二等卧铺"
    if "3rd" in lowered and "sleeper" in lowered:
        return "三等卧铺"
    if "seating" in lowered:
        return "座席"
    if re.fullmatch(r"\d+\s+seats?", label.strip(), re.I):
        return "座席"
    return label


def normalize_seat_detail(value: str, seat_label: str = "") -> str:
    text = re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()
    if not text:
        return ""
    text = re.sub(r"\bSeat\s+(\d+)\b", r"\1号座位", text, flags=re.I)
    text = re.sub(r"\bSleep\s+(\d+)\b", lambda m: f"{m.group(1)}号{'下铺' if int(m.group(1)) % 2 else '上铺'}", text, flags=re.I)
    text = re.sub(r"\bSleeper\s+(\d+)\b", lambda m: f"{m.group(1)}号{'下铺' if int(m.group(1)) % 2 else '上铺'}", text, flags=re.I)
    text = re.sub(r"\bPlatz\s+(\d+)\b", lambda m: f"{m.group(1)}号{'下铺' if int(m.group(1)) % 2 else '上铺'}", text, flags=re.I)
    text = re.sub(r"\bUpper\b", "上铺", text, flags=re.I)
    text = re.sub(r"\bLower\b", "下铺", text, flags=re.I)
    text = re.sub(r"\bVIP\s+(\d+)\b", r"VIP \1号铺位", text, flags=re.I)
    text = re.sub(r"^(\d+)\s+(?=\d+号|VIP)", r"\1车 ", text)
    if "卧铺" in seat_label and re.fullmatch(r"\d+车 \d+号", text):
        number = int(re.search(r"(\d+)号", text).group(1))
        text = f"{text}{'下铺' if number % 2 else '上铺'}"
    return text


def parse_left_count(text: str, default: int) -> int:
    match = re.search(r"(\d+)\s+seats?", text or "", re.I)
    if match:
        return int(match.group(1))
    numbers = re.findall(r"\d+", text or "")
    return int(numbers[0]) if numbers else default


def extract_train_summary(row: Any) -> dict[str, str]:
    train_no = read_locator_text(row, ".railway-train-services") or "可选车次"
    duration = read_locator_text(row, ".railway-train-duration-time__duration_text")
    time_nodes = row.locator(".railway-train-duration-time .font-600")
    depart_time = time_nodes.nth(0).inner_text(timeout=3000).strip() if time_nodes.count() >= 1 else ""
    arrive_time = time_nodes.nth(1).inner_text(timeout=3000).strip() if time_nodes.count() >= 2 else ""
    return {
        "train_no": train_no,
        "depart_time": depart_time,
        "arrive_time": arrive_time,
        "duration": duration or format_duration(depart_time, arrive_time),
    }


def extract_visible_seats(page: Any, passenger_count: int, left: int) -> tuple[str, list[str]]:
    car_buttons = page.locator(".railway-seats-rates-button button")
    seats: list[str] = []
    car_count = min(car_buttons.count(), 8)
    if car_count <= 0:
        car_count = 1

    for car_index in range(car_count):
        car_text = ""
        car_left = left
        if car_buttons.count() > 0:
            car_button = car_buttons.nth(car_index)
            car_text = car_button.inner_text(timeout=3000).strip().splitlines()[0]
            car_left = parse_left_count(car_button.inner_text(timeout=3000), 0) or left
            car_button.click()
            page.wait_for_timeout(400)
        seat_buttons = page.locator("button.seat-button")
        car_seats: list[str] = []
        for seat_index in range(min(seat_buttons.count(), 120)):
            button = seat_buttons.nth(seat_index)
            if button.get_attribute("disabled") is not None:
                continue
            class_name = (button.get_attribute("class") or "").lower()
            aria_disabled = (button.get_attribute("aria-disabled") or "").lower()
            if aria_disabled == "true" or any(token in class_name for token in ["disabled", "busy", "taken", "occupied", "unavailable"]):
                continue
            text = button.inner_text(timeout=3000).strip()
            if re.fullmatch(r"\d{1,3}", text):
                prefix = f"{car_text} " if car_text else ""
                car_seats.append(f"{prefix}{text}".strip())
        seats.extend(car_seats[:car_left])
        if len(seats) >= max(passenger_count, left):
            break

    unique = list(dict.fromkeys(seats))[: max(passenger_count, min(left, 12))]
    if not unique:
        return "", []
    return "、".join(unique[:passenger_count]), unique[:12]


def query_train_availability_browser(payload: dict[str, Any]) -> list[dict[str, Any]]:
    from_query = normalize_station(payload["from_station"])
    to_query = normalize_station(payload["to_station"])
    depart_date = format_ticket_date(str(payload["depart_date"]))
    result_url = f"{BOOKING_URL}/search/results/forward/{station_slug(from_query)}/{station_slug(to_query)}/{depart_date}"

    default_currency = default_currency_for_departure(from_query, str(payload.get("train_country", "")))
    seat_preference = str(payload.get("seat_preference", "")).strip()
    passenger_count = parse_positive_int(payload.get("passengers"))
    timeout_ms = int(os.getenv("TRAIN_TICKET_AVAILABILITY_TIMEOUT_MS", "60000"))
    max_offers = int(os.getenv("TRAIN_TICKET_MAX_OFFERS", "8"))

    from playwright.sync_api import sync_playwright

    offers: list[dict[str, Any]] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=os.getenv("TRAIN_TICKET_HEADLESS", "true").lower() == "true",
            slow_mo=int(os.getenv("TRAIN_TICKET_SLOW_MO", "80")),
        )
        context = browser.new_context(
            storage_state=os.getenv("TRAIN_TICKET_STORAGE_STATE") or None,
            viewport={"width": 1440, "height": 1000},
        )
        page = context.new_page()
        page.goto(result_url, wait_until="domcontentloaded", timeout=timeout_ms)
        page.wait_for_function(
            """() => [...document.querySelectorAll('.railway-train')]
                .some((el) => /\\d{1,2}:\\d{2}/.test(el.innerText) && /seats?/i.test(el.innerText))""",
            timeout=timeout_ms,
        )
        rows = page.locator(".railway-train", has_text=re.compile(r"\d{1,2}:\d{2}"))
        for row_index in range(rows.count()):
            row = rows.nth(row_index)
            summary = extract_train_summary(row)
            price_buttons = row.locator(".railway-train-prices-rates__price-button:visible")
            for seat_index in range(price_buttons.count()):
                if len(offers) >= max_offers:
                    break
                button = price_buttons.nth(seat_index)
                price_text = button.inner_text(timeout=5000).strip()
                lines = [line.strip() for line in price_text.splitlines() if line.strip()]
                seat = normalize_seat_label(lines[0] if lines else seat_preference or "可出票座席")
                if not seat_preference_matches(seat_preference, seat):
                    continue
                left = parse_left_count(price_text, passenger_count)
                if left < passenger_count:
                    continue
                unit_price, currency = parse_price_text(price_text, default_currency)
                if unit_price <= 0:
                    continue
                button.click()
                page.wait_for_selector("button.seat-button", timeout=timeout_ms)
                raw_seat_detail, raw_seat_options = extract_visible_seats(page, passenger_count, left)
                seat_options = [normalize_seat_detail(item, seat) for item in raw_seat_options]
                seat_options = [item for item in seat_options if item]
                seat_detail = "、".join(seat_options[:passenger_count])
                page.go_back(wait_until="domcontentloaded", timeout=timeout_ms)
                page.wait_for_function(
                    """() => [...document.querySelectorAll('.railway-train')]
                        .some((el) => /\\d{1,2}:\\d{2}/.test(el.innerText) && /seats?/i.test(el.innerText))""",
                    timeout=timeout_ms,
                )
                rows = page.locator(".railway-train", has_text=re.compile(r"\d{1,2}:\d{2}"))
                row = rows.nth(row_index)
                if len(seat_options) < passenger_count:
                    continue
                ticket_total_local = round(unit_price * passenger_count, 2)
                price = calculate_price(ticket_total_local, get_exchange_rate(currency))
                offers.append(
                    {
                        "train_no": summary["train_no"],
                        "depart_time": summary["depart_time"],
                        "arrive_time": summary["arrive_time"],
                        "duration": zh_duration(summary["duration"]),
                        "time": " - ".join(item for item in [summary["depart_time"], summary["arrive_time"]] if item)
                        or "时间以系统同步为准",
                        "seat": seat,
                        "seat_detail": seat_detail or "座位号以系统同步为准",
                        "seat_options": seat_options,
                        "left": left,
                        "currency": currency,
                        "ticket_total_local": ticket_total_local,
                        "exchange_rate": get_exchange_rate(currency),
                        "total_cny": price["subtotal_cny"],
                        "live_synced": True,
                        "synced_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
            if len(offers) >= max_offers:
                break
        browser.close()
    return offers


def normalize_station(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    key = text.lower().replace(" ", "")
    compact_aliases = {alias.lower().replace(" ", ""): station for alias, station in STATION_ALIASES.items()}
    return compact_aliases.get(key, text)


def normalize_latin_name(value: str) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z .'-]*", text):
        raise HTTPException(status_code=400, detail="Passenger name must use passport English spelling")
    return text


def normalize_passengers(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_passengers = payload.get("passenger_details") or payload.get("passengers_detail") or []
    if isinstance(raw_passengers, str):
        try:
            raw_passengers = json.loads(raw_passengers)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid passenger details") from exc
    if not isinstance(raw_passengers, list) or not raw_passengers:
        raise HTTPException(status_code=400, detail="Passenger details are required")
    passengers: list[dict[str, str]] = []
    for index, item in enumerate(raw_passengers, start=1):
        if not isinstance(item, dict):
            raise HTTPException(status_code=400, detail=f"Passenger {index} is invalid")
        raw_last_name = item.get("lastName") or item.get("last_name") or ""
        raw_first_name = item.get("firstName") or item.get("first_name") or ""
        if not raw_last_name and not raw_first_name and item.get("name"):
            name_parts = str(item.get("name", "")).strip().split()
            raw_last_name = name_parts[0] if name_parts else ""
            raw_first_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        last_name = normalize_latin_name(raw_last_name)
        first_name = normalize_latin_name(raw_first_name)
        passenger = {
            "last_name": last_name,
            "first_name": first_name,
            "name": f"{last_name} {first_name}",
            "doc_type": str(item.get("docType") or item.get("doc_type") or "passport").strip(),
            "doc_no": str(item.get("docNo") or item.get("doc_no") or "").strip(),
            "doc_issued": str(item.get("docIssued") or item.get("doc_issued") or "").strip(),
            "doc_expiry": str(item.get("docExpiry") or item.get("doc_expiry") or "").strip(),
            "birth": str(item.get("birth", "")).strip(),
            "gender": str(item.get("gender", "")).strip(),
            "nationality": str(item.get("nationality", "")).strip(),
        }
        missing = [
            key
            for key in ["last_name", "first_name", "doc_no", "doc_issued", "doc_expiry", "birth", "gender", "nationality"]
            if not passenger[key]
        ]
        if missing:
            raise HTTPException(status_code=400, detail={f"passenger_{index}_missing": missing})
        passengers.append(passenger)
    if len(passengers) > 6:
        raise HTTPException(status_code=400, detail="Passenger count is limited to 6")
    return passengers


def passenger_info_text(passengers: list[dict[str, str]]) -> str:
    return "\n".join(
        f"{item['last_name']} {item['first_name']} / {item['doc_type']} / {item['doc_no']} / issued {item['doc_issued']} / expiry {item['doc_expiry']} / {item['birth']} / {item['gender']} / {item['nationality']}"
        for item in passengers
    )


def payment_notification_body(order: TrainOrder) -> str:
    selected = order.selected_train or {}
    passenger_lines = []
    for index, passenger in enumerate(order.passenger_details, start=1):
        passenger_lines.append(
            "\n".join(
                [
                    f"乘客 {index}",
                    f"姓名：{passenger.get('last_name', '')} {passenger.get('first_name', '')}",
                    f"证件类型：{passenger.get('doc_type', '')}",
                    f"证件号码：{passenger.get('doc_no', '')}",
                    f"签发日期：{passenger.get('doc_issued', '')}",
                    f"到期日期：{passenger.get('doc_expiry', '')}",
                    f"出生日期：{passenger.get('birth', '')}",
                    f"性别：{passenger.get('gender', '')}",
                    f"国籍：{passenger.get('nationality', '')}",
                ]
            )
        )
    return "\n\n".join(
        [
            "火车票订单付款成功",
            PAYMENT_SUCCESS_NOTICE,
            "订单信息",
            f"订单号：{order.order_id}",
            f"状态：{order.status}",
            f"路线：{order.from_station} -> {order.to_station}",
            f"出发日期：{order.depart_date}",
            f"人数：{order.passengers}",
            f"车次：{selected.get('train_no', '')}",
            f"开车时间：{selected.get('depart_time', '')}",
            f"到达时间：{selected.get('arrive_time', '')}",
            f"运行时间：{selected.get('duration', '')}",
            f"座席：{selected.get('seat', '')}",
            f"座位/铺位：{selected.get('seat_detail', '')}",
            f"票面金额：{order.ticket_total_local} {order.ticket_currency}",
            f"人民币总价：{order.base_amount:.2f} 元",
            f"实际应付：{order.payable_amount:.2f} 元",
            "付款信息",
            f"支付宝业务流水号：{order.payment_ref}",
            f"付款金额：{order.paid_amount:.2f} 元" if order.paid_amount is not None else "付款金额：",
            f"付款时间：{order.paid_at}",
            f"付款截图服务器路径：{order.proof_path}",
            "联系人",
            f"微信：{order.contact_wechat}",
            f"手机：{order.contact_phone}",
            f"邮箱：{order.contact_email}",
            "乘客资料",
            "\n\n".join(passenger_lines),
        ]
    )


def build_payment_notification(order: TrainOrder) -> EmailMessage:
    recipient = os.getenv("TRAIN_TICKET_NOTIFY_EMAIL", "bldderblack@gmail.com")
    sender = (
        os.getenv("TRAIN_TICKET_RESEND_FROM")
        or os.getenv("TRAIN_TICKET_SMTP_FROM")
        or os.getenv("TRAIN_TICKET_SMTP_USER")
        or "Quiet Atlas <onboarding@resend.dev>"
    )
    message = EmailMessage()
    message["Subject"] = f"火车票付款成功：{order.order_id}"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(payment_notification_body(order))
    proof_path = Path(order.proof_path)
    if proof_path.exists():
        message.add_attachment(
            proof_path.read_bytes(),
            maintype="image",
            subtype=(proof_path.suffix.lower().lstrip(".") or "jpeg"),
            filename=proof_path.name,
        )
    return message


def save_notification_outbox(message: EmailMessage, order_id: str) -> Path:
    EMAIL_OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    outbox_path = EMAIL_OUTBOX_DIR / f"{order_id}.eml"
    outbox_path.write_bytes(message.as_bytes())
    return outbox_path


def send_notification_resend(order: TrainOrder, message: EmailMessage) -> str | None:
    api_key = os.getenv("TRAIN_TICKET_RESEND_API_KEY", "").strip()
    if not api_key:
        return None
    attachments = []
    proof_path = Path(order.proof_path)
    if proof_path.exists():
        attachments.append(
            {
                "filename": proof_path.name,
                "content": base64.b64encode(proof_path.read_bytes()).decode("ascii"),
            }
        )
    payload = {
        "from": message["From"],
        "to": [message["To"]],
        "subject": message["Subject"],
        "text": payment_notification_body(order),
    }
    if attachments:
        payload["attachments"] = attachments
    request = urllib.request.Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        body = json.loads(response.read().decode("utf-8") or "{}")
    return str(body.get("id") or "sent")


def send_payment_notification(order_id: str) -> None:
    with _lock:
        orders = load_orders()
        order = require_order(orders, order_id)
        message = build_payment_notification(order)
        outbox_path = save_notification_outbox(message, order_id)
        try:
            resend_id = send_notification_resend(order, message)
        except Exception as exc:
            resend_id = None
            resend_error = str(exc)
        else:
            resend_error = ""
        if resend_id:
            append_history(order, f"payment notification sent by resend: {resend_id}")
            save_orders(orders)
            return
        smtp_host = os.getenv("TRAIN_TICKET_SMTP_HOST", "").strip()
        if not smtp_host:
            note = f"payment notification saved: {outbox_path}"
            if resend_error:
                note += f"; resend error: {resend_error}"
            append_history(order, note)
            save_orders(orders)
            return
        smtp_port = int(os.getenv("TRAIN_TICKET_SMTP_PORT", "587"))
        smtp_user = os.getenv("TRAIN_TICKET_SMTP_USER", "").strip()
        smtp_password = os.getenv("TRAIN_TICKET_SMTP_PASSWORD", "")
        smtp_ssl = os.getenv("TRAIN_TICKET_SMTP_SSL", "false").lower() == "true"
        smtp_starttls = os.getenv("TRAIN_TICKET_SMTP_STARTTLS", "true").lower() == "true"
    try:
        if smtp_ssl:
            smtp_client: smtplib.SMTP = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15)
        else:
            smtp_client = smtplib.SMTP(smtp_host, smtp_port, timeout=15)
        with smtp_client as client:
            if smtp_starttls and not smtp_ssl:
                client.starttls()
            if smtp_user:
                client.login(smtp_user, smtp_password)
            client.send_message(message)
        note = f"payment notification sent to {message['To']}"
    except Exception as exc:
        note = f"payment notification saved only: {outbox_path}; send error: {exc}"
    with _lock:
        orders = load_orders()
        order = require_order(orders, order_id)
        append_history(order, note)
        save_orders(orders)


@app.post("/api/train-availability")
def train_availability(payload: dict[str, Any]) -> dict[str, Any]:
    required = ["from_station", "to_station", "depart_date"]
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    if missing:
        raise HTTPException(status_code=400, detail={"missing": missing})
    if str(payload["from_station"]).strip() == str(payload["to_station"]).strip():
        raise HTTPException(status_code=400, detail="From and to stations must be different")

    payload = dict(payload)
    payload["passengers"] = parse_positive_int(payload.get("passengers"))
    try:
        offers = query_train_availability_browser(payload)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Availability sync failed: {exc}") from exc
    return {
        "offers": offers,
        "message": "" if offers else "当前日期暂无可选座席，请返回修改日期或路线后重新查询；没有可选座席时不能进入下一步。",
    }


@app.post("/api/train-orders")
def create_train_order(payload: dict[str, Any]) -> dict[str, Any]:
    required = ["from_station", "to_station", "depart_date", "contact_wechat", "contact_phone", "contact_email"]
    missing = [key for key in required if not str(payload.get(key, "")).strip()]
    if missing:
        raise HTTPException(status_code=400, detail={"missing": missing})
    passenger_details = normalize_passengers(payload)
    selected_train_payload = dict(payload.get("selected_train") or {})
    if selected_train_payload.get("live_synced") is not True:
        raise HTTPException(status_code=400, detail="Selected train must come from realtime sync")

    ticket_currency = str(payload.get("ticket_currency", "KZT")).upper()
    ticket_total_local = float(payload.get("ticket_total_local") or payload.get("ticket_total") or payload.get("base_amount", 0))
    if ticket_total_local <= 0:
        raise HTTPException(status_code=400, detail="ticket_total_local must be greater than 0")
    exchange_rate = get_exchange_rate(ticket_currency, payload.get("exchange_rate"))
    price = calculate_price(ticket_total_local, exchange_rate)
    base_amount = price["subtotal_cny"]

    with _lock:
        orders = load_orders()
        order_id = create_order_id(orders)
        payable_amount = assign_payable_amount(base_amount, orders)
        now = utc_now()
        selected_train = selected_train_payload
        selected_train["departure_country"] = str(payload.get("train_country", "")).strip().upper()
        selected_train["arrival_country"] = str(payload.get("arrival_country", "")).strip().upper()
        order = TrainOrder(
            order_id=order_id,
            status="waiting_payment",
            from_station=str(payload["from_station"]).strip(),
            from_station_query=normalize_station(payload["from_station"]),
            to_station=str(payload["to_station"]).strip(),
            to_station_query=normalize_station(payload["to_station"]),
            depart_date=str(payload["depart_date"]).strip(),
            passengers=len(passenger_details),
            seat_preference=str(payload.get("seat_preference", "任意可出票座席")),
            selected_train=selected_train,
            passenger_info=passenger_info_text(passenger_details),
            passenger_details=passenger_details,
            contact=" / ".join(
                [
                    str(payload["contact_wechat"]).strip(),
                    str(payload["contact_phone"]).strip(),
                    str(payload["contact_email"]).strip(),
                ]
            ),
            contact_wechat=str(payload["contact_wechat"]).strip(),
            contact_phone=str(payload["contact_phone"]).strip(),
            contact_email=str(payload["contact_email"]).strip(),
            ticket_currency=ticket_currency,
            ticket_total_local=ticket_total_local,
            exchange_rate=exchange_rate,
            exchange_rate_used=price["exchange_rate_used"],
            ticket_amount_cny=price["ticket_amount_cny"],
            service_fee_cny=price["service_fee_cny"],
            base_amount=base_amount,
            payable_amount=payable_amount,
            expires_at=iso(now + timedelta(minutes=ORDER_TTL_MINUTES)),
            created_at=iso(now),
        )
        append_history(order, "order created")
        append_history(order, f"station language normalized: {order.from_station_query} -> {order.to_station_query}")
        orders[order_id] = order
        save_orders(orders)
    return {
        "order_id": order.order_id,
        "status": order.status,
        "payable_amount": order.payable_amount,
        "expires_at": order.expires_at,
        "ticket_currency": order.ticket_currency,
        "ticket_total_local": order.ticket_total_local,
        "exchange_rate": order.exchange_rate,
        "exchange_rate_used": order.exchange_rate_used,
        "ticket_amount_cny": order.ticket_amount_cny,
        "service_fee_cny": order.service_fee_cny,
        "subtotal_cny": order.base_amount,
        "payment_qr": os.getenv("TRAIN_TICKET_ALIPAY_QR_URL", ""),
    }


@app.post("/api/train-orders/{order_id}/payment")
async def submit_payment(
    order_id: str,
    background_tasks: BackgroundTasks,
    payment_ref: str = Form(...),
    paid_amount: float = Form(...),
    paid_at: str = Form(...),
    proof: UploadFile = File(...),
) -> dict[str, Any]:
    with _lock:
        orders = load_orders()
        order = require_order(orders, order_id)
        now = utc_now()
        expires_at = parse_client_time(order.expires_at)
        paid_time = parse_client_time(paid_at)
        if order.status not in {"waiting_payment", "submitted"}:
            raise HTTPException(status_code=409, detail="Order is not waiting for payment")
        if now > expires_at:
            order.status = "expired"
            append_history(order, "order expired")
            save_orders(orders)
            raise HTTPException(status_code=409, detail="Order expired")
        if abs(paid_amount - order.payable_amount) >= 0.001:
            raise HTTPException(status_code=400, detail="Payment amount does not match")
        if paid_time > expires_at:
            raise HTTPException(status_code=400, detail="Payment time is outside order window")
        if any(item.payment_ref == payment_ref for item in orders.values() if item.order_id != order_id):
            raise HTTPException(status_code=409, detail="Payment reference already used")

        PROOF_DIR.mkdir(parents=True, exist_ok=True)
        suffix = Path(proof.filename or "proof.jpg").suffix or ".jpg"
        proof_path = PROOF_DIR / f"{order_id}{suffix}"
        content = await proof.read()
        if not content:
            raise HTTPException(status_code=400, detail="Payment proof is required")
        proof_path.write_bytes(content)

        order.payment_ref = payment_ref.strip()
        order.paid_amount = paid_amount
        order.paid_at = paid_at
        order.proof_path = str(proof_path)
        order.status = "paid"
        append_history(order, "payment accepted")
        save_orders(orders)

    background_tasks.add_task(send_payment_notification, order_id)
    background_tasks.add_task(start_browser_assisted_booking, order_id)
    return {"order_id": order_id, "status": "paid"}


def auto_check_order(order: TrainOrder) -> tuple[bool, list[str]]:
    problems: list[str] = []
    if not order.from_station or not order.to_station:
        problems.append("route_missing")
    if not order.from_station_query or not order.to_station_query:
        problems.append("route_language_mapping_missing")
    if not order.depart_date:
        problems.append("depart_date_missing")
    if order.passengers != len(order.passenger_details):
        problems.append("passenger_count_mismatch")
    if order.ticket_total_local <= 0 or order.exchange_rate <= 0:
        problems.append("pricing_missing")
    for index, passenger in enumerate(order.passenger_details, start=1):
        for key in ["last_name", "first_name", "doc_no", "doc_issued", "doc_expiry", "birth", "gender", "nationality"]:
            if not str(passenger.get(key, "")).strip():
                problems.append(f"passenger_{index}_{key}_missing")
    if order.paid_amount is None or abs(order.paid_amount - order.payable_amount) >= 0.001:
        problems.append("payment_amount_mismatch")
    if not order.proof_path:
        problems.append("payment_proof_missing")
    return not problems, problems


def start_browser_assisted_booking(order_id: str) -> None:
    with _lock:
        orders = load_orders()
        order = require_order(orders, order_id)
        passed, problems = auto_check_order(order)
        if not passed:
            order.status = "needs_review"
            order.browser_note = "Auto check stopped: " + ", ".join(problems)
            append_history(order, order.browser_note)
            save_orders(orders)
            return
        order.status = "auto_checked"
        append_history(order, "auto check passed")
        order.status = "browser_queued"
        append_history(order, "browser task queued")
        save_orders(orders)

    try:
        run_tickets_kz_browser_flow(order)
        status = "auto_submit_ready"
        note = "Official page prepared for automatic final handling"
    except Exception as exc:  # pragma: no cover
        status = "needs_review"
        note = f"Browser task needs review: {exc}"

    with _lock:
        orders = load_orders()
        order = require_order(orders, order_id)
        order.status = status
        order.browser_note = note
        append_history(order, note)
        save_orders(orders)


def run_tickets_kz_browser_flow(order: TrainOrder) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=os.getenv("TRAIN_TICKET_HEADLESS", "false").lower() == "true",
            slow_mo=int(os.getenv("TRAIN_TICKET_SLOW_MO", "120")),
        )
        context = browser.new_context(storage_state=os.getenv("TRAIN_TICKET_STORAGE_STATE") or None)
        page = context.new_page()
        page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=60000)

        # Selectors must be tuned once against the live tickets.kz page.
        selector_map = {
            "from": os.getenv("TRAIN_TICKET_FROM_SELECTOR", ""),
            "to": os.getenv("TRAIN_TICKET_TO_SELECTOR", ""),
            "date": os.getenv("TRAIN_TICKET_DATE_SELECTOR", ""),
            "search": os.getenv("TRAIN_TICKET_SEARCH_SELECTOR", ""),
        }
        if not all(selector_map.values()):
            page.pause()
            return

        page.locator(selector_map["from"]).fill(order.from_station_query)
        page.locator(selector_map["to"]).fill(order.to_station_query)
        page.locator(selector_map["date"]).fill(order.depart_date)
        page.locator(selector_map["search"]).click()
        page.wait_for_load_state("domcontentloaded", timeout=60000)
        if os.getenv("TRAIN_TICKET_AUTO_SUBMIT", "false").lower() != "true":
            page.pause()
            return
        page.pause()


@app.get("/api/train-orders/{order_id}")
def get_order(order_id: str) -> dict[str, Any]:
    orders = load_orders()
    return asdict(require_order(orders, order_id))


@app.post("/api/train-orders/{order_id}/operator-confirm")
def operator_confirm(order_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        orders = load_orders()
        order = require_order(orders, order_id)
        if order.status not in {"auto_submit_ready", "needs_review"}:
            raise HTTPException(status_code=409, detail="Order is not ready for operator confirmation")
        order.status = str(payload.get("status", "ready_to_submit"))
        order.official_result = str(payload.get("official_result", ""))
        append_history(order, "operator updated order")
        save_orders(orders)
    return {"order_id": order_id, "status": order.status}
