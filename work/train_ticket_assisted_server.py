from __future__ import annotations

import json
import os
import random
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
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
ORDER_TTL_MINUTES = 20
BOOKING_URL = "https://tickets.kz/en/gd"
EXCHANGE_MARKUP_RATE = 0.03
TOTAL_FEE_RATE = 0.20
SERVICE_FEE_RATE = TOTAL_FEE_RATE - EXCHANGE_MARKUP_RATE
DEFAULT_EXCHANGE_RATES = {
    "KZT": float(os.getenv("TRAIN_TICKET_RATE_KZT", "0.0145")),
    "UZS": float(os.getenv("TRAIN_TICKET_RATE_UZS", "0.000564")),
}

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


def get_exchange_rate(currency: str, explicit_rate: Any = None) -> float:
    if explicit_rate not in (None, ""):
        rate = float(explicit_rate)
    else:
        rate = DEFAULT_EXCHANGE_RATES.get(currency.upper(), 1.0)
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


def parse_positive_int(value: Any, default: int = 1) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(6, parsed))


def default_currency_for_departure(from_station: str, train_country: str = "") -> str:
    country = str(train_country or "").strip().upper()
    if country == "UZ":
        return "UZS"
    if country == "KZ":
        return "KZT"
    uzbek_stations = {"Tashkent", "Samarkand", "Bukhara", "Khiva", "Urgench", "Nukus", "Andijan", "Fergana"}
    if from_station in uzbek_stations:
        return "UZS"
    return "KZT"


def parse_time_minutes(value: str) -> int | None:
    match = re.search(r"(\d{1,2})[:：](\d{2})", value or "")
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def format_duration(depart_time: str, arrive_time: str, fallback: str = "") -> str:
    if fallback:
        return fallback
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


def query_train_availability_browser(payload: dict[str, Any]) -> list[dict[str, Any]]:
    row_selector = os.getenv("TRAIN_TICKET_OFFER_ROW_SELECTOR", "").strip()
    selector_map = {
        "from": os.getenv("TRAIN_TICKET_FROM_SELECTOR", "").strip(),
        "to": os.getenv("TRAIN_TICKET_TO_SELECTOR", "").strip(),
        "date": os.getenv("TRAIN_TICKET_DATE_SELECTOR", "").strip(),
        "search": os.getenv("TRAIN_TICKET_SEARCH_SELECTOR", "").strip(),
        "row": row_selector,
        "train": os.getenv("TRAIN_TICKET_OFFER_TRAIN_SELECTOR", "").strip(),
        "depart": os.getenv("TRAIN_TICKET_OFFER_DEPART_SELECTOR", "").strip(),
        "arrive": os.getenv("TRAIN_TICKET_OFFER_ARRIVE_SELECTOR", "").strip(),
        "seat": os.getenv("TRAIN_TICKET_OFFER_SEAT_SELECTOR", "").strip(),
        "seat_detail": os.getenv("TRAIN_TICKET_OFFER_SEAT_DETAIL_SELECTOR", "").strip(),
        "left": os.getenv("TRAIN_TICKET_OFFER_LEFT_SELECTOR", "").strip(),
        "duration": os.getenv("TRAIN_TICKET_OFFER_DURATION_SELECTOR", "").strip(),
        "price": os.getenv("TRAIN_TICKET_OFFER_PRICE_SELECTOR", "").strip(),
    }
    if not all(selector_map[key] for key in ["from", "to", "date", "search", "row"]):
        raise RuntimeError("Realtime train sync is not configured")

    from_query = normalize_station(payload["from_station"])
    to_query = normalize_station(payload["to_station"])
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
        context = browser.new_context(storage_state=os.getenv("TRAIN_TICKET_STORAGE_STATE") or None)
        page = context.new_page()
        page.goto(BOOKING_URL, wait_until="domcontentloaded", timeout=timeout_ms)
        page.locator(selector_map["from"]).fill(from_query)
        page.locator(selector_map["to"]).fill(to_query)
        page.locator(selector_map["date"]).fill(str(payload["depart_date"]))
        page.locator(selector_map["search"]).click()
        page.wait_for_selector(selector_map["row"], timeout=timeout_ms)
        rows = page.locator(selector_map["row"])
        for index in range(min(rows.count(), max_offers)):
            row = rows.nth(index)
            row_text = row.inner_text(timeout=5000).strip()
            price_text = read_locator_text(row, selector_map["price"]) or row_text
            unit_price, currency = parse_price_text(price_text, default_currency)
            if unit_price <= 0:
                continue
            seat = read_locator_text(row, selector_map["seat"]) or seat_preference or "可出票座席"
            seat_detail = read_locator_text(row, selector_map["seat_detail"])
            if seat_preference and seat_preference != "任意可出票座席" and seat_preference not in seat:
                continue
            left_text = read_locator_text(row, selector_map["left"]) or row_text
            left_numbers = re.findall(r"\d+", left_text)
            left = int(left_numbers[-1]) if left_numbers else passenger_count
            if left < passenger_count:
                continue
            depart_time = read_locator_text(row, selector_map["depart"])
            arrive_time = read_locator_text(row, selector_map["arrive"])
            duration = format_duration(depart_time, arrive_time, read_locator_text(row, selector_map["duration"]))
            train_no = read_locator_text(row, selector_map["train"]) or row_text.splitlines()[0][:40] or f"可选车次 {index + 1}"
            ticket_total_local = round(unit_price * passenger_count, 2)
            price = calculate_price(ticket_total_local, get_exchange_rate(currency))
            seat_options = build_seat_details(seat, index, 0, max(left, passenger_count))
            selected_seat_detail = seat_detail or "、".join(seat_options[:passenger_count])
            offers.append(
                {
                    "train_no": train_no,
                    "depart_time": depart_time,
                    "arrive_time": arrive_time,
                    "duration": duration,
                    "time": " - ".join(item for item in [depart_time, arrive_time] if item) or "时间以系统同步为准",
                    "seat": seat,
                    "seat_detail": selected_seat_detail,
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
