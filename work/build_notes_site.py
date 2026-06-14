from __future__ import annotations

import html
import json
import re
import shutil
import csv
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


ROOT = Path("/Users/g90/Documents/Codex/2026-06-13/hermes")
SOURCE_DIR = ROOT / "outputs" / "小红书已完成专题"
SITE_DIR = ROOT / "outputs" / "uzbek-notes-site"
CONFIG_PATH = SITE_DIR / "tools" / "site.config.json"
DINING_SOURCE = ROOT / "outputs" / "GoogleMaps_110条_整理标注总表.csv"
OTHER_AUTHOR_SOURCE = ROOT / "outputs" / "final16_继续读取_处理结果.csv"
USER_ADDRESS_SOURCE = ROOT / "outputs" / "用户补充地址_地图核验.csv"
USER_ADDRESS_GOOGLE_SOURCE = ROOT / "outputs" / "用户补充地址_GoogleMaps核验_20260613.csv"
PRIOR_CONFIRMED_DINING_SOURCE = Path(
    "/Users/g90/xiaohongshu_tandian_recovered/tandian_only/坐标位置_已确认明细_当前.csv"
)
RECOVERED_DINING_DIR = Path("/Users/g90/xiaohongshu_tandian_recovered/tandian_only")

USER_ADDRESS_ALIASES = {
    "中乌长安美食城": ["中乌长安美食城"],
    "长安巷·融合菜": ["长安巷·融合菜", "长安巷"],
    "巴蜀印象": ["巴蜀印象"],
    "川渝私房菜（东方明珠酒店）": ["川渝私房菜（东方明珠酒店）", "川渝私房菜"],
    "塔什干川蓉燚中餐厅": ["塔什干川蓉燚中餐厅", "川蓉燚"],
    "塔什干｜中餐｜四川酒店": ["塔什干｜中餐｜四川酒店", "四川酒店", "四川饭店"],
    "China Chuan Chuan": ["China Chuan Chuan", "china chuan chuan"],
    "Lesnoy": ["Lesnoy", "Lesnoy森林"],
    "ORA": ["ORA"],
    "COCOCHOU BAKERY": ["COCOCHOU BAKERY", "Cocochou"],
    "muza kitchen": ["muza kitchen", "Muza Kitchen"],
    "煮江湖重庆火锅": ["煮江湖重庆火锅", "塔什干煮江湖火锅餐厅", "JIANG HU HUOGUO 煮江湖火锅"],
    "湘味小厨": ["湘味小厨"],
    "Caravan": ["Caravan", "Restaurant Caravan"],
    "OKO": ["OKO", "Oko"],
}
USER_ADDRESS_OVERRIDE_CACHE: dict[str, dict[str, str]] | None = None
DROP_DINING_KEY_CACHE: set[str] | None = None

DROP_DINING_NAMES = {
    "樽龍私厨",
    "西南川菜馆",
    "VINO GALAXY 酒水管家",
    "闽浙海鲜餐厅",
    "长安大饭店",
    "锅气火锅",
    "锅气小碗菜",
    "China Chuan Chuan",
    "百顺餐厅",
    "温州饭店",
    "百味餐厅",
    "渝味山庄江湖菜",
    "淮扬食府中餐厅",
    "漫漫重庆大碗麻辣烫",
    "汤火功夫麻辣烫",
    "永福餐厅",
    "来福餐厅",
    "念家湘湘菜馆",
    "幸福小馆",
    "布哈拉新疆餐厅",
    "土窑烧烤",
    "友谊饭店",
    "包子客牛肉汤包",
    "乌鲁木齐餐厅",
    "一站式火锅外卖",
    "中国饭店",
    "乌中友谊城饺子馆",
    "华人湘菜馆",
    "塔什干麻辣烫",
    "费尔干纳中国餐厅",
    "米屋拌饭",
    "塔什干 印度菜The host装修 还有家分店 - 小红书",
    "塔什干 墨西哥🇲🇽小酒馆 - 小红书",
    "塔什干 早餐节 TURAN - 小红书",
    "塔什干 茶主张 - 小红书",
    "塔什干 莅临指导花剌子模菜 Сазанчк - 小红书",
    "CBF撒马尔罕中餐厅",
    "yusuf兰州拉面",
    "都来顺面馆",
}

DINING_NAME_CORRECTIONS = {
    "锡尔河州扬吉耶尔市乡厨原味餐厅": {
        "name": "亚洲最大手抓饭中心",
        "title": "亚洲最大手抓饭中心",
        "seq": "亚洲最大手抓饭中心",
        "map_name": "亚洲最大手抓饭中心",
        "note": "名称校正：原记录应显示为亚洲最大手抓饭中心。",
    },
    "功夫熊猫中餐厅": {
        "name": "汤火功夫麻辣烫",
        "title": "汤火功夫麻辣烫",
        "seq": "汤火功夫麻辣烫",
        "status": "待用户自行确认",
        "lat": "",
        "lng": "",
        "map_name": "汤火功夫麻辣烫",
        "map_detail": "Kungfu Malatang；餐馆·Ulitsa Istiklol 7",
        "note": "名称校正：Kungfu Malatang 应显示为汤火功夫麻辣烫，不按熊猫饭店记录展示。",
    },
}

DINING_CANDIDATE_CORRECTIONS = {
    "Kungfu Malatang": "汤火功夫麻辣烫",
}

DINING_KEY_ALIASES = [
    ("syrovarnya", ["syrovarnya"]),
    ("cocochou", ["cocochou", "cocochoubakery"]),
    ("herotea", ["herotea", "herotea麻辣烫奶茶"]),
    ("沈阳饺子馆", ["沈阳饺子馆"]),
    ("ansan", ["ansan", "鲜族菜馆"]),
    ("沙县小吃", ["沙县小吃"]),
    ("忆湖湘", ["忆湖湘"]),
    ("korzinka", ["korzinka"]),
    ("长安巷", ["长安巷", "kattamirobodstreet139", "kattamirabadstreet139"]),
]


@dataclass(frozen=True)
class Country:
    slug: str
    name: str
    status: str
    summary: str
    topics: list[str]


@dataclass(frozen=True)
class Topic:
    slug: str
    title: str
    short_title: str
    category: str
    country: str
    country_slug: str
    summary: str
    order: int
    source_file: str = ""


@dataclass(frozen=True)
class DiningPlace:
    source: str
    seq: str
    title: str
    name: str
    tag: str
    status: str
    lat: str
    lng: str
    map_name: str
    map_detail: str
    note: str
    map_url: str
    author_id: str
    author_name: str
    author_profile: str
    post_url: str
    address_hint: str


@dataclass(frozen=True)
class OtherAuthorReview:
    name: str
    status: str
    reason: str
    post_url: str
    author_name: str
    author_id: str
    author_profile: str
    address_coord: str
    map_check: str


DEFAULT_TOPICS = [
    Topic(
        slug="yandex-go",
        title="Yandex Go 打车与外卖",
        short_title="Yandex Go",
        category="出行",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="注册、叫车、外卖、定位、支付和常见使用场景。",
        source_file="01_Yandex_Go_打车外卖流程_小红书整理.md",
        order=1,
    ),
    Topic(
        slug="entry-guide",
        title="乌兹别克斯坦入境攻略",
        short_title="入境攻略",
        category="入境",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="入境材料、机场流程、机票、申报提醒和普通短途游客建议。",
        source_file="02_乌兹别克斯坦入境攻略_小红书整理.md",
        order=2,
    ),
    Topic(
        slug="payment-withdrawal",
        title="银行卡取款与支付方式",
        short_title="支付与取款",
        category="支付",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="银联、Visa、Mastercard、现金索姆和 Yandex Go 付款组合。",
        source_file="03_乌兹别克斯坦银行卡取款与支付方式_小红书整理.md",
        order=3,
    ),
    Topic(
        slug="sim-card",
        title="手机卡登记",
        short_title="手机卡登记",
        category="通信",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="电话卡办理、运营商选择、现场测试和短期旅行推荐做法。",
        source_file="04_乌兹别克斯坦手机卡登记_小红书整理.md",
        order=4,
    ),
    Topic(
        slug="imei-registration",
        title="手机卡槽 IMEI 登记专项",
        short_title="IMEI 登记",
        category="通信",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="机场登记、市区办理、线上登记、费用信息和注意事项。",
        source_file="05_乌兹别克斯坦手机卡槽IMEI登记_小红书专项整理.md",
        order=5,
    ),
    Topic(
        slug="registration-slip",
        title="小白条 / 住宿登记",
        short_title="小白条",
        category="住宿",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="住宿登记凭证、获取方式、出境检查反馈和多城市行程建议。",
        source_file="06_乌兹别克斯坦小白条住宿登记_小红书整理.md",
        order=6,
    ),
    Topic(
        slug="network-prep",
        title="科学上网与网络准备",
        short_title="网络准备",
        category="通信",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="出发前网络工具、漫游、离线资料、账号安全和到达后连接检查。",
        order=7,
    ),
    Topic(
        slug="local-tools",
        title="当地国家工具使用合集",
        short_title="工具合集",
        category="工具",
        country="乌兹别克斯坦",
        country_slug="uzbekistan",
        summary="把免签时间、行程日期、当地实用换算等小工具集中放在一起。",
        order=8,
    ),
]

DEFAULT_TOPIC_MARKDOWN = {
    "local-tools": """# 当地国家工具使用合集

选择下面的工具卡片进入详情页。后续新增国家时，每个国家都按同样结构维护。
""",
}


def default_config() -> dict[str, Any]:
    return {
        "siteName": "长日记事",
        "siteNameEn": "Longday Notes",
        "tagline": "个人旅行专题资料库",
        "homepage": {
            "eyebrow": "Personal travel knowledge base",
            "headline": "写一些长期有用的观察，也记录生活里真实的纹理。",
            "lead": "这是一个以个人内容为中心的网站：不堆砌头衔，不急着证明什么，只把经历、阅读、旅行和项目里的思考整理成可被反复阅读的文字。",
            "note_title": "把路上遇到的问题，慢慢整理成有秩序的内容。",
            "note_body": "这里放旅行，也放项目；放答案，也保留判断的过程。它不追求热闹，只希望每一次打开，都能更快地回到真实、具体、可使用的信息里。",
        },
        "countries": [
            {
                "slug": "uzbekistan",
                "name": "乌兹别克斯坦",
                "status": "online",
                "summary": "出行、入境、通信、支付、住宿登记。",
                "topics": [topic.slug for topic in DEFAULT_TOPICS],
            },
            {
                "slug": "next-country",
                "name": "下一个国家",
                "status": "reserved",
                "summary": "复制国家模板，添加 Markdown 专题后即可生成。",
                "topics": [],
            },
            {
                "slug": "future-countries",
                "name": "更多国家",
                "status": "reserved",
                "summary": "栏目、分类、搜索和导航都已留出扩展空间。",
                "topics": [],
            },
        ],
        "topics": [
            {
                "slug": topic.slug,
                "title": topic.title,
                "short_title": topic.short_title,
                "category": topic.category,
                "country": topic.country,
                "country_slug": topic.country_slug,
                "summary": topic.summary,
                "order": topic.order,
                "source_file": topic.source_file,
            }
            for topic in DEFAULT_TOPICS
        ],
    }


def ensure_seed_files() -> None:
    (SITE_DIR / "tools").mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(
            json.dumps(default_config(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    defaults = default_config()
    changed = False
    if config.get("siteName") in (None, "", "Uzbek Notes"):
        config["siteName"] = defaults["siteName"]
        changed = True
    if config.get("siteName") == "Quiet Atlas":
        config["siteName"] = defaults["siteName"]
        changed = True
    if not config.get("siteNameEn"):
        config["siteNameEn"] = defaults["siteNameEn"]
        changed = True
    if not config.get("tagline"):
        config["tagline"] = defaults["tagline"]
        changed = True
    if not config.get("homepage"):
        config["homepage"] = defaults["homepage"]
        changed = True
    else:
        homepage = config["homepage"]
        if homepage.get("headline") == "把复杂的出行信息，整理成安静、清楚、可长期维护的个人资料库。":
            homepage["headline"] = defaults["homepage"]["headline"]
            changed = True
        if homepage.get("lead", "").startswith("目前收录乌兹别克斯坦专题"):
            homepage["lead"] = defaults["homepage"]["lead"]
            changed = True
        for key in ["note_title", "note_body"]:
            if not homepage.get(key):
                homepage[key] = defaults["homepage"][key]
                changed = True

    default_countries = {country["slug"]: country for country in defaults["countries"]}
    existing_country_slugs = {country.get("slug") for country in config.get("countries", [])}
    for slug in ["future-countries"]:
        if slug not in existing_country_slugs:
            config.setdefault("countries", []).append(default_countries[slug])
            changed = True
    for country in config.get("countries", []):
        default_country = default_countries.get(country.get("slug"))
        if default_country and not country.get("summary"):
            country["summary"] = default_country["summary"]
            changed = True

    default_topics = {topic["slug"]: topic for topic in defaults["topics"]}
    existing_topic_slugs = {topic.get("slug") for topic in config.get("topics", [])}
    for slug, default_topic in default_topics.items():
        if slug not in existing_topic_slugs:
            config.setdefault("topics", []).append(default_topic)
            changed = True
    for country in config.get("countries", []):
        default_country = default_countries.get(country.get("slug"))
        if not default_country:
            continue
        country_topics = country.setdefault("topics", [])
        for topic_slug in default_country.get("topics", []):
            if topic_slug not in country_topics:
                country_topics.append(topic_slug)
                changed = True
    for topic in config.get("topics", []):
        if "filename" in topic and "source_file" not in topic:
            topic["source_file"] = topic.pop("filename")
            changed = True
        default_topic = default_topics.get(topic.get("slug"))
        if default_topic:
            for key in ["short_title", "category", "summary", "order"]:
                if key not in topic:
                    topic[key] = default_topic[key]
                    changed = True

    if changed:
        CONFIG_PATH.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    for raw_topic in config.get("topics", []):
        topic = topic_from_dict(raw_topic)
        topic_path = topic_markdown_path(topic)
        topic_path.parent.mkdir(parents=True, exist_ok=True)
        if topic_path.exists():
            continue
        if topic.source_file:
            source_path = SOURCE_DIR / topic.source_file
            if source_path.exists():
                topic_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
                continue
        if topic.slug in DEFAULT_TOPIC_MARKDOWN:
            topic_path.write_text(DEFAULT_TOPIC_MARKDOWN[topic.slug], encoding="utf-8")
            continue
        topic_path.write_text(f"# {topic.title}\n\n待补充。\n", encoding="utf-8")


def clean_generated_files() -> None:
    for path in [
        SITE_DIR / "index.html",
        SITE_DIR / "404.html",
        SITE_DIR / "robots.txt",
        SITE_DIR / "assets",
        SITE_DIR / "countries",
        SITE_DIR / "dining",
        SITE_DIR / "topics",
        SITE_DIR / "operate",
    ]:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for path in [
        SITE_DIR / "assets",
        SITE_DIR / "countries",
        SITE_DIR / "dining",
        SITE_DIR / "operate",
    ]:
        path.mkdir(parents=True, exist_ok=True)


def country_from_dict(data: dict[str, Any]) -> Country:
    return Country(
        slug=str(data["slug"]),
        name=str(data["name"]),
        status=str(data.get("status", "online")),
        summary=str(data.get("summary", "")),
        topics=list(data.get("topics", [])),
    )


def topic_from_dict(data: dict[str, Any]) -> Topic:
    return Topic(
        slug=str(data["slug"]),
        title=str(data["title"]),
        short_title=str(data.get("short_title", data["title"])),
        category=str(data.get("category", "其他")),
        country=str(data.get("country", "")),
        country_slug=str(data["country_slug"]),
        summary=str(data.get("summary", "")),
        order=int(data.get("order", 999)),
        source_file=str(data.get("source_file", "")),
    )


def load_site_data() -> tuple[dict[str, Any], list[Country], list[Topic]]:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    countries = [country_from_dict(item) for item in config.get("countries", [])]
    topics = sorted(
        [topic_from_dict(item) for item in config.get("topics", [])],
        key=lambda topic: (topic.country_slug, topic.order, topic.title),
    )
    return config, countries, topics


def load_dining_places() -> list[DiningPlace]:
    places: list[DiningPlace] = []
    drop_keys = dropped_dining_keys()
    if PRIOR_CONFIRMED_DINING_SOURCE.exists():
        with PRIOR_CONFIRMED_DINING_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                name = row.get("名称", "").strip()
                if not name:
                    continue
                if normalized_place_key(name) in drop_keys:
                    continue
                lat, lng = split_coord(row.get("坐标", ""))
                detail = prior_confirmed_detail(row)
                address = detail.get("address", "")
                source_note = compact_text(row.get("状态", ""))
                places.append(
                    normalize_dining_place(
                        DiningPlace(
                            source=row.get("来源", "").strip(),
                            seq=row.get("序号/名称", "").strip(),
                            title=detail.get("title") or name,
                            name=name,
                            tag=classify_dining_tag(" ".join([name, detail.get("title", ""), address])),
                            status="已确认详细坐标",
                            lat=lat,
                            lng=lng,
                            map_name=detail.get("map_name") or name,
                            map_detail=address or "地址待补（已有坐标）",
                            note=compact_text("；".join(part for part in ["历史已确认坐标记录", source_note, detail.get("note", "")] if part)),
                            map_url=detail.get("map_url") or google_maps_search_url(name),
                            author_id=detail.get("author_id", ""),
                            author_name="",
                            author_profile="",
                            post_url=detail.get("post_url", ""),
                            address_hint=detail.get("address_hint", ""),
                        )
                    )
                )

    if not DINING_SOURCE.exists():
        return places
    with DINING_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        name = row.get("提取餐厅/地点名", "").strip() or row.get("Google候选名", "").strip()
        if not name:
            continue
        if normalized_place_key(name) in drop_keys:
            continue
        places.append(
            normalize_dining_place(
                DiningPlace(
                    source=row.get("来源", "").strip(),
                    seq=row.get("序号/名称", "").strip(),
                    title=row.get("标题/名称", "").strip(),
                    name=name,
                    tag=row.get("餐饮标签", "").strip() or "其他",
                    status=row.get("整理状态", "").strip(),
                    lat=row.get("最终纬度", "").strip(),
                    lng=row.get("最终经度", "").strip(),
                    map_name=row.get("Google候选名", "").strip(),
                    map_detail=compact_text(row.get("Google候选详情/地址", "")),
                    note=compact_text(row.get("备注", "")),
                    map_url=row.get("Google Maps查询URL", "").strip(),
                    author_id=row.get("作者小红书号", "").strip(),
                    author_name=row.get("账号名字", "").strip(),
                    author_profile=row.get("作者主页链接", "").strip(),
                    post_url=row.get("原帖链接", "").strip(),
                    address_hint=compact_text(row.get("地址线索", "")),
                )
            )
        )
    places = [
        place
        for place in append_user_address_places(places)
        if dining_place_key(place) not in drop_keys
        and normalized_place_key(place.name) not in drop_keys
        and normalized_place_key(place.title) not in drop_keys
        and normalized_place_key(place.map_name) not in drop_keys
    ]
    places = dedupe_dining_places(places)
    return sorted(
        places,
        key=lambda place: (
            place.status != "已确认详细坐标",
            place.map_detail.startswith("地址待补"),
            place.tag,
            place.name,
        ),
    )


def filter_dropped_dining_places(places: list[DiningPlace]) -> list[DiningPlace]:
    drop_keys = dropped_dining_keys()
    return [
        place
        for place in places
        if dining_place_key(place) not in drop_keys
        and normalized_place_key(place.name) not in drop_keys
        and normalized_place_key(place.title) not in drop_keys
        and normalized_place_key(place.map_name) not in drop_keys
    ]


def load_other_author_reviews() -> list[OtherAuthorReview]:
    if not OTHER_AUTHOR_SOURCE.exists():
        return []
    with OTHER_AUTHOR_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    reviews: list[OtherAuthorReview] = []
    drop_keys = dropped_dining_keys()
    for row in rows:
        name = row.get("提取名", "").strip()
        status = row.get("处理结果", "").strip()
        if status.startswith("删除"):
            continue
        if normalized_place_key(name) in drop_keys:
            continue
        reviews.append(
            OtherAuthorReview(
                name=name,
                status=status,
                reason=compact_text(row.get("原因", ""), 220),
                post_url=row.get("原帖链接", "").strip(),
                author_name=row.get("作者昵称/用户名", "").strip(),
                author_id=row.get("作者小红书号", "").strip(),
                author_profile=row.get("作者主页链接", "").strip(),
                address_coord=compact_text(row.get("地址/坐标", ""), 180),
                map_check=compact_text(row.get("地图核验", ""), 180),
            )
        )
    return reviews


def normalize_dining_place(place: DiningPlace) -> DiningPlace:
    correction = DINING_NAME_CORRECTIONS.get(place.name)
    if correction:
        return DiningPlace(
            source=place.source,
            seq=correction.get("seq", place.seq),
            title=correction.get("title", place.title),
            name=correction.get("name", place.name),
            tag=classify_dining_tag(" ".join([correction.get("name", place.name), correction.get("map_detail", place.map_detail)])),
            status=correction.get("status", place.status),
            lat=correction.get("lat", place.lat),
            lng=correction.get("lng", place.lng),
            map_name=correction.get("map_name", place.map_name),
            map_detail=correction.get("map_detail", place.map_detail),
            note=correction.get("note", place.note),
            map_url=google_maps_search_url(correction.get("name", place.name)),
            author_id=place.author_id,
            author_name=place.author_name,
            author_profile=place.author_profile,
            post_url=place.post_url,
            address_hint=place.address_hint,
        )

    map_name = DINING_CANDIDATE_CORRECTIONS.get(place.map_name, place.map_name)
    if map_name != place.map_name:
        return DiningPlace(
            source=place.source,
            seq=place.seq,
            title=place.title,
            name=place.name,
            tag=place.tag,
            status=place.status,
            lat=place.lat,
            lng=place.lng,
            map_name=map_name,
            map_detail=place.map_detail,
            note=place.note,
            map_url=place.map_url,
            author_id=place.author_id,
            author_name=place.author_name,
            author_profile=place.author_profile,
            post_url=place.post_url,
            address_hint=place.address_hint,
        )
    return place


GENERIC_ADDRESS_PHRASES = [
    "未在地图上获取有效位置坐标",
    "地址待补",
    "暂无更多地址说明",
]


def dining_place_key(place: DiningPlace) -> str:
    combined = normalized_place_key(
        " ".join([place.name, place.title, place.seq, place.map_name, place.address_hint])
    )
    for canonical, aliases in DINING_KEY_ALIASES:
        if any(alias in combined for alias in aliases):
            return canonical
    map_key = normalized_place_key(place.map_name)
    if (
        place.status != "已确认详细坐标"
        and map_key
        and place.map_name not in ["# Google 地图", "待继续核验"]
        and "ministryofdefense" not in map_key
    ):
        return map_key
    return normalized_place_key(place.name)


def is_generic_address(value: str) -> bool:
    text = value or ""
    return not text.strip() or any(phrase in text for phrase in GENERIC_ADDRESS_PHRASES)


def dining_place_score(place: DiningPlace) -> int:
    override = user_address_override_for(place)
    score = 0
    if override:
        score += 100
    if place.status == "已确认详细坐标":
        score += 80
    if place.lat and place.lng:
        score += 50
    if not is_generic_address(place.map_detail):
        score += 30
    if place.post_url:
        score += 12
    if place.author_id or place.author_name:
        score += 8
    if place.map_url:
        score += 4
    return score


def dining_map_info_score(place: DiningPlace) -> int:
    score = 0
    if not is_generic_address(place.map_detail):
        score += 30
    if place.lat and place.lng:
        score += 20
    if place.tag == "中餐" and "中国风味" in place.map_detail:
        score += 25
    if normalized_place_key(place.name) and normalized_place_key(place.name) in normalized_place_key(place.map_name):
        score += 20
    if place.map_name and place.map_name not in ["# Google 地图", "待继续核验"]:
        score += 5
    return score


def best_non_generic(values: list[str]) -> str:
    for value in values:
        if not is_generic_address(value):
            return value
    return first_nonempty(values)


def merge_dining_places(group: list[DiningPlace]) -> DiningPlace:
    ordered = sorted(group, key=dining_place_score, reverse=True)
    base = ordered[0]
    map_source = max(group, key=dining_map_info_score)
    status = "已确认详细坐标" if any(place.status == "已确认详细坐标" for place in ordered) else base.status
    coord_source = next((place for place in ordered if place.lat and place.lng), base)
    tag = base.tag if base.tag != "其他" else first_nonempty([place.tag for place in ordered if place.tag != "其他"]) or base.tag
    return DiningPlace(
        source=base.source,
        seq=base.seq,
        title=first_nonempty([base.title, *[place.title for place in ordered]]),
        name=base.name,
        tag=tag,
        status=status,
        lat=coord_source.lat,
        lng=coord_source.lng,
        map_name=first_nonempty([map_source.map_name, base.map_name, *[place.map_name for place in ordered]]),
        map_detail=best_non_generic([map_source.map_detail, base.map_detail, *[place.map_detail for place in ordered]]),
        note=compact_text("；".join(unique_nonempty([base.note, *[place.note for place in ordered]])), 220),
        map_url=first_nonempty([base.map_url, *[place.map_url for place in ordered]]),
        author_id=first_nonempty([base.author_id, *[place.author_id for place in ordered]]),
        author_name=first_nonempty([base.author_name, *[place.author_name for place in ordered]]),
        author_profile=first_nonempty([base.author_profile, *[place.author_profile for place in ordered]]),
        post_url=first_nonempty([base.post_url, *[place.post_url for place in ordered]]),
        address_hint=best_non_generic([base.address_hint, *[place.address_hint for place in ordered]]),
    )


def dedupe_dining_places(places: list[DiningPlace]) -> list[DiningPlace]:
    groups: dict[str, list[DiningPlace]] = {}
    ordered_keys: list[str] = []
    for place in places:
        key = dining_place_key(place)
        if not key:
            ordered_keys.append(f"__row_{len(ordered_keys)}")
            groups[ordered_keys[-1]] = [place]
            continue
        if key not in groups:
            ordered_keys.append(key)
            groups[key] = []
        groups[key].append(place)
    return [merge_dining_places(groups[key]) for key in ordered_keys]


def coords_from_review(review: OtherAuthorReview) -> tuple[str, str]:
    for value in [review.address_coord, review.map_check]:
        match = re.search(r"(?<!\d)(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,3}\.\d+)(?!\d)", value or "")
        if match:
            first, second = match.group(1), match.group(2)
            if abs(float(first)) <= 45 and abs(float(second)) >= 45:
                return first, second
            return second, first
    return "", ""


def review_map_name(review: OtherAuthorReview, place: DiningPlace) -> str:
    address = review.address_coord or ""
    before_coord = re.sub(r";\s*-?\d{1,2}\.\d+\s*,\s*-?\d{1,3}\.\d+.*$", "", address).strip()
    if before_coord:
        return before_coord.split(";")[0].strip()
    return place.map_name or review.name


def merge_other_author_reviews_into_places(
    places: list[DiningPlace],
    reviews: list[OtherAuthorReview],
) -> list[DiningPlace]:
    kept_reviews = {
        normalized_place_key(review.name): review
        for review in reviews
        if review.status.startswith("保留") and normalized_place_key(review.name)
    }
    merged: list[DiningPlace] = []
    matched_review_keys: set[str] = set()
    for place in places:
        review = kept_reviews.get(dining_place_key(place)) or kept_reviews.get(normalized_place_key(place.name))
        if not review:
            merged.append(place)
            continue
        matched_review_keys.add(normalized_place_key(review.name))
        lat, lng = coords_from_review(review)
        review_detail = compact_text(
            "；".join(unique_nonempty([review.address_coord, review.map_check])),
            260,
        )
        merged.append(
            normalize_dining_place(
                replace(
                    place,
                    status="已确认详细坐标" if lat and lng else place.status,
                    lat=lat or place.lat,
                    lng=lng or place.lng,
                    map_name=review_map_name(review, place),
                    map_detail=review_detail or place.map_detail,
                    note=compact_text("；".join(unique_nonempty([review.reason, place.note])), 220),
                    author_id=first_nonempty([review.author_id, place.author_id]),
                    author_name=first_nonempty([review.author_name, place.author_name]),
                    author_profile=first_nonempty([review.author_profile, place.author_profile]),
                    post_url=first_nonempty([review.post_url, place.post_url]),
                    address_hint=best_non_generic([review.address_coord, place.address_hint]),
                )
            )
        )
    for key, review in kept_reviews.items():
        if key in matched_review_keys:
            continue
        lat, lng = coords_from_review(review)
        review_detail = compact_text(
            "；".join(unique_nonempty([review.address_coord, review.map_check])),
            260,
        )
        merged.append(
            normalize_dining_place(
                DiningPlace(
                    source="小红书",
                    seq=review.name,
                    title=review.name,
                    name=review.name,
                    tag=classify_dining_tag(" ".join([review.name, review_detail])),
                    status="已确认详细坐标" if lat and lng else "待用户自行确认",
                    lat=lat,
                    lng=lng,
                    map_name=review_map_name(
                        review,
                        DiningPlace(
                            source="",
                            seq="",
                            title="",
                            name=review.name,
                            tag="",
                            status="",
                            lat="",
                            lng="",
                            map_name="",
                            map_detail="",
                            note="",
                            map_url="",
                            author_id="",
                            author_name="",
                            author_profile="",
                            post_url="",
                            address_hint="",
                        ),
                    ),
                    map_detail=review_detail or "地址待补",
                    note=review.reason,
                    map_url=google_maps_search_url(review.name),
                    author_id=review.author_id,
                    author_name=review.author_name,
                    author_profile=review.author_profile,
                    post_url=review.post_url,
                    address_hint=review.address_coord,
                )
            )
        )
    return dedupe_dining_places(merged)


def dedupe_other_author_reviews(
    reviews: list[OtherAuthorReview],
    existing_place_keys: set[str],
) -> list[OtherAuthorReview]:
    seen = set(existing_place_keys)
    result: list[OtherAuthorReview] = []
    for review in reviews:
        key = normalized_place_key(review.name)
        if not key:
            continue
        if key in seen:
            continue
        seen.add(key)
        result.append(review)
    return result


def prior_confirmed_detail(row: dict[str, str]) -> dict[str, str]:
    source_file = row.get("来源文件", "").strip()
    source_path = RECOVERED_DINING_DIR / source_file
    if not source_file or not source_path.exists():
        return {}
    seq = row.get("序号/名称", "").strip()
    name = row.get("名称", "").strip().lower()
    try:
        with source_path.open("r", encoding="utf-8-sig", newline="") as f:
            candidates = list(csv.DictReader(f))
    except UnicodeDecodeError:
        with source_path.open("r", encoding="utf-8", newline="") as f:
            candidates = list(csv.DictReader(f))
    match = None
    for item in candidates:
        item_seq = (item.get("序号") or item.get("序号/名称") or "").strip()
        item_name = (
            item.get("店铺/地点名")
            or item.get("提取店名")
            or item.get("原帖提取店名")
            or item.get("名称")
            or ""
        ).strip().lower()
        item_title = (item.get("标题") or item.get("标题/名称") or "").strip().lower()
        if seq and item_seq == seq:
            match = item
            break
        if name and (name == item_name or name in item_title or item_name in name):
            match = item
            break
    if not match:
        return {}

    address_parts = unique_nonempty(
        [
            match.get("提取地址", ""),
            match.get("原帖提取地址", ""),
            match.get("地址线索", ""),
            match.get("地图返回名称/地址", ""),
        ]
    )
    map_url = first_nonempty(
        [
            match.get("Yandex详情页", ""),
            match.get("Yandex链接", ""),
            match.get("Google详情页", ""),
            match.get("Google链接", ""),
            match.get("2GIS详情页", ""),
            match.get("2GIS链接", ""),
            match.get("Yandex Maps", ""),
            match.get("Google Maps", ""),
        ]
    )
    return {
        "title": first_nonempty([match.get("标题", ""), match.get("标题/名称", "")]),
        "address": compact_text(" / ".join(address_parts), 220),
        "address_hint": compact_text(first_nonempty([match.get("地址线索", ""), match.get("提取地址", ""), match.get("原帖提取地址", "")]), 180),
        "map_name": first_nonempty(
            [
                match.get("地图返回名称/地址", ""),
                match.get("提取店名", ""),
                match.get("原帖提取店名", ""),
                match.get("店铺/地点名", ""),
            ]
        ),
        "map_url": map_url,
        "post_url": first_nonempty([match.get("小红书原帖链接", ""), match.get("来源帖子链接", "")]),
        "author_id": match.get("作者小红书号", "").strip(),
        "note": compact_text(first_nonempty([match.get("核查备注", ""), match.get("定位说明", ""), match.get("状态", "")]), 180),
    }


def first_nonempty(values: list[str]) -> str:
    for value in values:
        text = (value or "").strip()
        if text:
            return text
    return ""


def unique_nonempty(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text = compact_text(value, 180)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def split_coord(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in (value or "").split(",", 1)]
    if len(parts) != 2:
        return "", ""
    return parts[0], parts[1]


def normalized_place_key(value: str) -> str:
    text = (value or "").lower()
    text = text.replace("｜", "|")
    text = re.sub(r"[\s·|（）()《》\"'“”，,。:：/\\-]+", "", text)
    return text


def dropped_dining_keys() -> set[str]:
    global DROP_DINING_KEY_CACHE
    if DROP_DINING_KEY_CACHE is not None:
        return DROP_DINING_KEY_CACHE
    keys = {normalized_place_key(name) for name in DROP_DINING_NAMES if normalized_place_key(name)}
    if OTHER_AUTHOR_SOURCE.exists():
        with OTHER_AUTHOR_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                status = row.get("处理结果", "").strip()
                name = row.get("提取名", "").strip()
                if status.startswith("删除") and name:
                    keys.add(normalized_place_key(name))
    DROP_DINING_KEY_CACHE = keys
    return keys


def register_user_address_override(
    overrides: dict[str, dict[str, str]],
    source_name: str,
    user_address: str,
    map_address: str,
    coord: str,
    status: str,
    note: str,
) -> None:
    name = (source_name or "").strip()
    if not name:
        return
    lat, lng = split_coord(coord)
    detail_parts = [
        f"用户补充地址：{user_address.strip()}" if user_address.strip() else "",
        f"地图地址：{map_address.strip()}" if map_address.strip() else "",
        f"坐标：{coord.strip()}" if coord.strip() else "",
    ]
    override = {
        "name": name,
        "address": compact_text("；".join(part for part in detail_parts if part), 260),
        "map_name": compact_text(map_address or name, 120),
        "lat": lat,
        "lng": lng,
        "status": status.strip(),
    }
    for alias in [name, *USER_ADDRESS_ALIASES.get(name, [])]:
        key = normalized_place_key(alias)
        if key:
            overrides[key] = override


def load_user_address_overrides() -> dict[str, dict[str, str]]:
    global USER_ADDRESS_OVERRIDE_CACHE
    if USER_ADDRESS_OVERRIDE_CACHE is not None:
        return USER_ADDRESS_OVERRIDE_CACHE

    overrides: dict[str, dict[str, str]] = {}
    if USER_ADDRESS_SOURCE.exists():
        with USER_ADDRESS_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                register_user_address_override(
                    overrides,
                    row.get("名称", ""),
                    row.get("用户补充地址", ""),
                    row.get("地图名称/地址", ""),
                    row.get("坐标", ""),
                    row.get("地图核验状态", ""),
                    row.get("备注", ""),
                )

    if USER_ADDRESS_GOOGLE_SOURCE.exists():
        with USER_ADDRESS_GOOGLE_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                lat = row.get("Google纬度", "").strip()
                lng = row.get("Google经度", "").strip()
                register_user_address_override(
                    overrides,
                    row.get("用户给的名称", ""),
                    row.get("用户给的地址", ""),
                    row.get("Google候选详情/地址", ""),
                    f"{lat}, {lng}" if lat and lng else "",
                    row.get("核验状态", ""),
                    row.get("备注", ""),
                )

    USER_ADDRESS_OVERRIDE_CACHE = overrides
    return overrides


def user_address_override_for(place: DiningPlace) -> dict[str, str]:
    overrides = load_user_address_overrides()
    for value in [place.name, place.seq, place.title, place.map_name]:
        key = normalized_place_key(value)
        if key in overrides:
            return overrides[key]
    return {}


def resolved_coord(place: DiningPlace, override: dict[str, str]) -> str:
    lat = override.get("lat") or place.lat
    lng = override.get("lng") or place.lng
    return f"{lat}, {lng}" if lat and lng else "待补坐标"


def resolved_map_name(place: DiningPlace, override: dict[str, str]) -> str:
    return override.get("map_name") or place.map_name or "待继续核验"


def resolved_address_detail(place: DiningPlace, override: dict[str, str]) -> str:
    return override.get("address") or place.map_detail or place.address_hint or place.note or "暂无更多地址说明"


def place_matches_user_address(place: DiningPlace, source_name: str) -> bool:
    aliases = [source_name, *USER_ADDRESS_ALIASES.get(source_name, [])]
    place_keys = {
        normalized_place_key(value)
        for value in [place.name, place.seq, place.title, place.map_name]
        if value
    }
    alias_keys = {normalized_place_key(alias) for alias in aliases if alias}
    return bool(place_keys & alias_keys)


def canonical_user_address_overrides() -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for override in load_user_address_overrides().values():
        name = override.get("name", "")
        key = normalized_place_key(name)
        if not key or key in seen:
            continue
        seen.add(key)
        result.append(override)
    return result


def user_address_place_status(override: dict[str, str]) -> str:
    status = override.get("status", "")
    detail = override.get("address", "")
    if any(word in status + detail for word in ["地址冲突", "不是同名", "未确认"]):
        return "待用户自行确认"
    if any(word in status for word in ["已确认", "同名地点", "楼内有同名"]):
        return "已确认详细坐标"
    return "待用户自行确认"


def append_user_address_places(places: list[DiningPlace]) -> list[DiningPlace]:
    result = list(places)
    drop_keys = dropped_dining_keys()
    for override in canonical_user_address_overrides():
        name = override.get("name", "")
        if normalized_place_key(name) in drop_keys:
            continue
        if any(place_matches_user_address(place, name) for place in result):
            continue
        detail = override.get("address", "")
        result.append(
            DiningPlace(
                source="",
                seq="",
                title=name,
                name=name,
                tag=classify_dining_tag(" ".join([name, detail])),
                status=user_address_place_status(override),
                lat=override.get("lat", ""),
                lng=override.get("lng", ""),
                map_name=override.get("map_name", ""),
                map_detail=detail,
                note=override.get("status", ""),
                map_url=google_maps_search_url(name),
                author_id="",
                author_name="",
                author_profile="",
                post_url="",
                address_hint="",
            )
        )
    return result


def google_maps_search_url(name: str) -> str:
    from urllib.parse import quote

    return f"https://www.google.com/maps/search/{quote(name + ' Tashkent Uzbekistan restaurant')}"


def classify_dining_tag(text: str) -> str:
    lowered = text.lower()
    if any(word in lowered for word in ["咖啡", "coffee", "cafe", "café", "bakery", "brunch", "甜品", "蛋糕", "茶"]):
        return "咖啡厅"
    if any(word in lowered for word in ["pizza", "pasta", "意大利", "西餐", "steak", "burger", "bar"]):
        return "西餐"
    if any(word in lowered for word in ["plov", "乌兹", "抓饭", "民族菜", "uzbek"]):
        return "乌兹别克斯坦本地菜"
    if any(word in lowered for word in ["中餐", "川", "湘", "粤", "中国", "新疆", "饺子", "火锅", "麻辣烫", "面馆", "饭店", "餐厅", "小馆"]):
        return "中餐"
    return "其他"


def compact_text(value: str, limit: int = 150) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def topic_markdown_path(topic: Topic) -> Path:
    return SITE_DIR / "content" / "countries" / topic.country_slug / "topics" / f"{topic.slug}.md"


def topic_url(topic: Topic) -> str:
    return f"/countries/{topic.country_slug}/topics/{topic.slug}/"


def read_topic(topic: Topic) -> str:
    return topic_markdown_path(topic).read_text(encoding="utf-8")


def compact_url_label(url: str) -> str:
    plain_url = html.unescape(url or "")
    lowered = plain_url.lower()
    if "xiaohongshu.com/user/profile" in lowered:
        return "作者主页"
    if "xiaohongshu.com/explore" in lowered:
        return "原帖"
    if "google.com/maps" in lowered:
        return "地图查询"
    return "查看链接"


def inline_link(label: str, url: str) -> str:
    visible = compact_url_label(label) if re.match(r"^https?://", html.unescape(label or "")) else label
    return (
        f'<a href="{html.escape(html.unescape(url), quote=True)}" '
        f'target="_blank" rel="noopener">{html.escape(visible)}</a>'
    )


def inline_markdown(text: str) -> str:
    text = html.escape(text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: inline_link(match.group(1), match.group(2)),
        text,
    )
    text = re.sub(
        r'(?<!["=])\b(https?://[^\s<]+)',
        lambda match: inline_link(compact_url_label(match.group(1)), match.group(1)),
        text,
    )
    return text


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    parts: list[str] = []
    paragraph: list[str] = []
    list_stack: list[str] = []
    in_quote = False

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            parts.append(f"<p>{inline_markdown(' '.join(paragraph).strip())}</p>")
            paragraph = []

    def close_lists() -> None:
        nonlocal list_stack
        while list_stack:
            parts.append(f"</{list_stack.pop()}>")

    def close_quote() -> None:
        nonlocal in_quote
        if in_quote:
            parts.append("</blockquote>")
            in_quote = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            close_quote()
            continue
        if stripped == "---":
            flush_paragraph()
            close_lists()
            close_quote()
            parts.append("<hr>")
            continue
        if stripped.startswith("#"):
            flush_paragraph()
            close_lists()
            close_quote()
            level = min(len(stripped) - len(stripped.lstrip("#")), 4)
            text = stripped[level:].strip()
            parts.append(f'<h{level} id="{slugify(text)}">{inline_markdown(text)}</h{level}>')
            continue
        if stripped.startswith(">"):
            flush_paragraph()
            close_lists()
            if not in_quote:
                parts.append("<blockquote>")
                in_quote = True
            quote_text = stripped.lstrip(">").strip()
            parts.append(f"<p>{inline_markdown(quote_text)}</p>")
            continue
        bullet_match = re.match(r"^[-*]\s+(.+)$", stripped)
        numbered_match = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet_match or numbered_match:
            flush_paragraph()
            close_quote()
            tag = "ul" if bullet_match else "ol"
            if not list_stack or list_stack[-1] != tag:
                close_lists()
                parts.append(f"<{tag}>")
                list_stack.append(tag)
            item = bullet_match.group(1) if bullet_match else numbered_match.group(1)
            parts.append(f"<li>{inline_markdown(item)}</li>")
            continue
        close_lists()
        close_quote()
        paragraph.append(stripped)

    flush_paragraph()
    close_lists()
    close_quote()
    return "\n".join(parts)


def slugify(text: str) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text.lower()).strip("-")
    return base or "section"


def page_shell(config: dict[str, Any], title: str, body: str, description: str = "") -> str:
    site_name = html.escape(str(config.get("siteName", "Quiet Atlas")))
    site_name_en = html.escape(str(config.get("siteNameEn", "")))
    desc = html.escape(description or str(config.get("tagline", "个人专题资料库")))
    return f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="{desc}">
    <title>{html.escape(title)} - {site_name}</title>
    <link rel="stylesheet" href="/assets/styles.css?v=20260614-sim-compare">
    <script src="/tools/runtime-config.js?v=20260614-deploy"></script>
    <script defer src="/assets/site.js?v=20260614-deploy"></script>
  </head>
  <body>
    <header class="site-header">
      <a class="brand" href="/"><span>{site_name}</span><small>{site_name_en}</small></a>
      <nav aria-label="主导航">
        <a href="/#countries">国家</a>
        <a href="/#topics">专题</a>
        <a href="/dining/">探店</a>
      </nav>
    </header>
    {body}
  </body>
</html>
"""


def topic_card(topic: Topic) -> str:
    return f"""
      <a class="topic-card" href="{topic_url(topic)}" data-search-card>
        <span class="topic-meta">{html.escape(topic.category)} · {html.escape(topic.country)}</span>
        <strong>{html.escape(topic.title)}</strong>
        <p>{html.escape(topic.summary)}</p>
      </a>
"""


def dining_topic_card(country: Country) -> str:
    return f"""
      <a class="topic-card" href="/countries/{country.slug}/dining/" data-search-card>
        <span class="topic-meta">探店 · {html.escape(country.name)}</span>
        <strong>{html.escape(country.name)}探店</strong>
        <p>餐厅、咖啡馆、本地菜地点、地址坐标、作者信息和原帖来源。</p>
      </a>
"""


def country_card(country: Country) -> str:
    status_text = "已上线" if country.status == "online" else "预留"
    if country.status == "online":
        return f"""
          <a class="country-card active" href="/countries/{country.slug}/">
            <span>{status_text}</span>
            <strong>{html.escape(country.name)}</strong>
            <p>{html.escape(country.summary)}</p>
          </a>
"""
    return f"""
          <article class="country-card muted-card">
            <span>{status_text}</span>
            <strong>{html.escape(country.name)}</strong>
            <p>{html.escape(country.summary)}</p>
          </article>
"""


def link_button(url: str, label: str) -> str:
    if not url:
        return ""
    return f'<a href="{html.escape(url)}" target="_blank" rel="noopener">{html.escape(label)}</a>'


AUTHOR_PROFILE_OVERRIDES = {
    "5995009986": "https://www.xiaohongshu.com/user/profile/6535e4340000000004008040",
}


def author_profile_url(author_id: str, author_profile: str) -> str:
    if author_profile:
        return author_profile
    clean_id = (author_id or "").strip()
    return AUTHOR_PROFILE_OVERRIDES.get(clean_id, "")


def author_display(author_name: str, author_id: str) -> str:
    parts = [
        part
        for part in [(author_name or "").strip(), (author_id or "").strip()]
        if part and part != "未提取到"
    ]
    return " / ".join(parts)


def dining_meta_text(place: DiningPlace) -> str:
    parts = [
        part
        for part in [place.source, place.seq, place.tag]
        if part and part != "微信餐厅"
    ]
    return " · ".join(parts)


def source_action_block(author: str, links: str) -> str:
    author_html = ""
    if author:
        author_html = f"""
              <div class="source-author">
                <span>作者</span>
                <strong>{html.escape(author)}</strong>
              </div>
"""
    links_html = f'<div class="dining-links">{links}</div>' if links else ""
    return f"""
            <div class="source-actions">
              {author_html}
              {links_html}
            </div>
"""


def dining_card(place: DiningPlace) -> str:
    override = user_address_override_for(place)
    coord = resolved_coord(place, override)
    status_class = "confirmed" if place.status == "已确认详细坐标" else "pending"
    status_text = "已确认详细坐标" if place.status == "已确认详细坐标" else "待继续核验"
    author = author_display(place.author_name, place.author_id)
    profile_url = author_profile_url(place.author_id, place.author_profile)
    links = " ".join(
        item
        for item in [
            link_button(place.map_url, "地图查询"),
            link_button(place.post_url, "原帖"),
            link_button(profile_url, "作者主页"),
        ]
        if item
    )
    meta = dining_meta_text(place)
    map_name = resolved_map_name(place, override)
    detail = resolved_address_detail(place, override)
    return f"""
          <article class="dining-card" data-search-card>
            <div class="dining-card-head">
              <span>{html.escape(meta)}</span>
              <em class="{status_class}">{html.escape(status_text)}</em>
            </div>
            <h3>{html.escape(place.name)}</h3>
            <p>{html.escape(place.title)}</p>
            <dl>
              <div><dt>坐标</dt><dd>{html.escape(coord)}</dd></div>
              <div><dt>候选</dt><dd>{html.escape(map_name)}</dd></div>
              <div><dt>地址</dt><dd>{html.escape(detail)}</dd></div>
            </dl>
            {source_action_block(author, links)}
          </article>
"""


def other_author_card(review: OtherAuthorReview) -> str:
    status_class = "confirmed" if review.status.startswith("保留") else "pending"
    author = author_display(review.author_name, review.author_id)
    profile_url = author_profile_url(review.author_id, review.author_profile)
    links = " ".join(
        item
        for item in [
            link_button(review.post_url, "原帖"),
            link_button(profile_url, "作者主页"),
        ]
        if item
    )
    return f"""
          <article class="review-card" data-search-card>
            <div class="dining-card-head">
              <span>其他作者补查</span>
              <em class="{status_class}">{html.escape(review.status)}</em>
            </div>
            <h3>{html.escape(review.name)}</h3>
            <dl>
              <div><dt>地址坐标</dt><dd>{html.escape(review.address_coord or "未确认")}</dd></div>
              <div><dt>地图核验</dt><dd>{html.escape(review.map_check or "未确认")}</dd></div>
            </dl>
            {source_action_block(author, links)}
          </article>
"""


def render_home(
    config: dict[str, Any],
    countries: list[Country],
    topics: list[Topic],
    dining_places: list[DiningPlace],
) -> str:
    homepage = config.get("homepage", {})
    online_countries = [country for country in countries if country.status == "online"]
    first_country = online_countries[0] if online_countries else None
    country_cards = "\n".join(country_card(country) for country in online_countries)
    first_country_link = f"/countries/{first_country.slug}/" if first_country else "#countries"
    first_country_name = first_country.name if first_country else "国家资料库"
    body = f"""
    <main>
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">{html.escape(str(homepage.get("eyebrow", "Personal travel knowledge base")))}</p>
          <h1>{html.escape(str(homepage.get("headline", "")))}</h1>
          <p class="lead">{html.escape(str(homepage.get("lead", "")))}</p>
        </div>
        <aside class="index-panel" aria-label="资料库概览">
          <p class="panel-label">Current archive</p>
          <h2>{html.escape(first_country_name)}</h2>
          <dl>
            <div><dt>上线国家</dt><dd>{len(online_countries)}</dd></div>
            <div><dt>专题</dt><dd>{len(topics)}</dd></div>
            <div><dt>探店</dt><dd>{len(dining_places)}</dd></div>
          </dl>
          <a href="{first_country_link}">进入国家页</a>
        </aside>
      </section>

      <section class="section manifesto">
        <p class="section-kicker">Quiet note</p>
        <div class="manifesto-grid">
          <h2>{html.escape(str(homepage.get("note_title", "")))}</h2>
          <p>{html.escape(str(homepage.get("note_body", "")))}</p>
        </div>
      </section>

      <section class="section country-strip" id="countries">
        <div>
          <p class="section-kicker">Countries</p>
          <h2>国家资料库</h2>
          <p class="section-copy">每个国家都是一组可以继续生长的观察：先把当下最有用的经验放进去，再随着新的行程和阅读慢慢修订。</p>
        </div>
        <div class="country-grid">
          {country_cards}
        </div>
      </section>
    </main>
    <footer class="site-footer">
      <span>{html.escape(str(config.get("siteName", "Quiet Atlas")))}</span>
      <span>{html.escape(str(config.get("tagline", "个人专题资料库")))}</span>
    </footer>
"""
    return page_shell(config, "首页", body, str(config.get("tagline", "")))


def render_country_page(
    config: dict[str, Any],
    country: Country,
    topics_by_slug: dict[str, Topic],
    dining_places: list[DiningPlace],
) -> str:
    country_topics = [topics_by_slug[slug] for slug in country.topics if slug in topics_by_slug]
    cards = "\n".join([topic_card(topic) for topic in country_topics] + [dining_topic_card(country)])
    body = f"""
    <main>
      <section class="country-hero">
        <p class="eyebrow">Country archive</p>
        <h1>{html.escape(country.name)}</h1>
        <p class="lead">{html.escape(country.summary)} 这里不只收集结论，也记录抵达、办理、确认和选择时那些真实的纹理。</p>
      </section>
      <section class="section">
        <div class="section-head">
          <div>
            <p class="section-kicker">All topics</p>
            <h2>专题索引</h2>
          </div>
          <a class="text-link" href="/">返回首页</a>
        </div>
        <div class="topic-grid">{cards}</div>
      </section>
    </main>
    <footer class="site-footer">
      <a class="footer-link" href="/countries/{country.slug}/">{html.escape(country.name)}</a>
      <span>{len(country_topics)} 个专题</span>
    </footer>
"""
    return page_shell(config, country.name, body, f"{country.name}专题索引")


def render_dining_page(
    config: dict[str, Any],
    country: Country,
    places: list[DiningPlace],
    other_reviews: list[OtherAuthorReview],
) -> str:
    existing_place_keys = {
        key
        for place in places
        for key in [dining_place_key(place), normalized_place_key(place.name)]
        if key
    }
    visible_reviews = dedupe_other_author_reviews(
        other_reviews,
        existing_place_keys,
    )
    cards = "\n".join(dining_card(place) for place in places)
    other_cards = "\n".join(other_author_card(review) for review in visible_reviews)
    all_cards = "\n".join(part for part in [cards, other_cards] if part)
    confirmed_count = sum(1 for place in places if place.status == "已确认详细坐标")
    pending_count = len(places) - confirmed_count
    body = f"""
    <main>
      <section class="country-hero dining-hero">
        <p class="eyebrow">Dining archive</p>
        <h1>{html.escape(country.name)}探店索引</h1>
        <p class="lead">这里收纳餐厅、咖啡馆、本地菜和中餐地点。每条尽量保留地点名、坐标状态、地址线索、作者账号和原帖链接，让后续继续确认可以接上。</p>
      </section>
      <section class="section">
        <div class="quiet-stats">
          <div><span>地点</span><strong>{len(places)}</strong></div>
          <div><span>已确认坐标</span><strong>{confirmed_count}</strong></div>
          <div><span>待继续核验</span><strong>{pending_count}</strong></div>
        </div>
      </section>
      <section class="section">
        <div class="section-head">
          <div>
            <p class="section-kicker">Places</p>
            <h2>地点列表</h2>
          </div>
          <label class="search-box">
            <span>搜索</span>
            <input type="search" data-search placeholder="输入餐厅或作者">
          </label>
        </div>
        <div class="dining-list" data-topic-list>
          {all_cards}
        </div>
      </section>
    </main>
    <footer class="site-footer">
      <span>{html.escape(country.name)}探店</span>
      <span>地点索引</span>
    </footer>
"""
    return page_shell(config, f"{country.name}探店索引", body, f"{country.name}探店地点索引")


def dining_index_card(country: Country, places: list[DiningPlace]) -> str:
    confirmed_count = sum(1 for place in places if place.status == "已确认详细坐标")
    pending_count = len(places) - confirmed_count
    return f"""
      <a class="topic-card" href="/countries/{country.slug}/dining/" data-search-card>
        <span class="topic-meta">探店 · {html.escape(country.name)}</span>
        <strong>{html.escape(country.name)}探店</strong>
        <p>地点 {len(places)} 条，已确认坐标 {confirmed_count} 条，待继续核验 {pending_count} 条。</p>
      </a>
"""


def render_dining_index_page(
    config: dict[str, Any],
    countries: list[Country],
    places: list[DiningPlace],
) -> str:
    online_countries = [country for country in countries if country.status == "online"]
    cards = "\n".join(dining_index_card(country, places) for country in online_countries)
    body = f"""
    <main>
      <section class="country-hero">
        <p class="eyebrow">Dining archive</p>
        <h1>探店</h1>
        <p class="lead">先按国家进入探店资料库。每个国家单独保留餐厅、咖啡馆、本地菜地点、地址坐标、作者信息和原帖来源。</p>
      </section>
      <section class="section">
        <div class="section-head">
          <div>
            <p class="section-kicker">Countries</p>
            <h2>国家探店</h2>
          </div>
        </div>
        <div class="topic-grid" data-topic-list>{cards}</div>
      </section>
    </main>
    <footer class="site-footer">
      <span>{html.escape(str(config.get("siteName", "Quiet Atlas")))}</span>
      <span>探店</span>
    </footer>
"""
    return page_shell(config, "探店", body, "国家探店入口")


def tool_detail_url(topic: Topic, tool_slug: str) -> str:
    return f"/countries/{topic.country_slug}/topics/{topic.slug}/{tool_slug}/"


def render_local_tools_index(topic: Topic) -> str:
    tools = [
        {
            "slug": "visa-calculator",
            "meta": "中国护照",
            "title": "免签时间计算器",
            "summary": "填写每次出入境时间，计算本次最晚离境日和下一次可免签入境日期。",
        },
        {
            "slug": "sim-comparison",
            "meta": "乌兹别克斯坦",
            "title": "运营商与电话卡套餐对比",
            "summary": "按运营商品牌对比代表套餐、优缺点和旅行办理建议。",
        },
        {
            "slug": "train-tickets",
            "meta": "乌兹别克斯坦 / 哈萨克斯坦",
            "title": "火车票查询与代订",
            "summary": "填写路线、日期、乘客和付款信息，生成服务端订单并进入后续出票流程。",
        },
    ]
    cards = "\n".join(
        f"""
          <a class="tool-card" href="{tool_detail_url(topic, tool["slug"])}">
            <span>{html.escape(tool["meta"])}</span>
            <strong>{html.escape(tool["title"])}</strong>
            <p>{html.escape(tool["summary"])}</p>
          </a>
"""
        for tool in tools
    )
    return f"""
      <section class="tool-card-section">
        <div class="section-head">
          <div>
            <p class="section-kicker">Tools</p>
            <h2>工具列表</h2>
          </div>
        </div>
        <div class="tool-card-grid">
          {cards}
        </div>
      </section>
"""


def render_visa_calculator() -> str:
    return f"""
      <section class="tool-panel" data-visa-calculator>
        <div class="tool-panel-head">
          <div>
            <p class="section-kicker">Visa calculator</p>
            <h2>免签时间计算器</h2>
          </div>
          <span>中国护照</span>
        </div>
        <div class="tool-form">
          <label class="tool-field">
            <span>目的地</span>
            <select data-visa-country></select>
          </label>
          <label class="tool-field">
            <span>本次 / 参考入境日期</span>
            <input type="date" data-visa-arrival>
          </label>
          <label class="tool-field">
            <span>免签天数</span>
            <input type="number" min="1" max="365" value="30" data-visa-days>
          </label>
          <label class="tool-field">
            <span>本次 / 参考离境日期</span>
            <input type="date" data-visa-departure>
          </label>
          <label class="tool-field">
            <span>计算口径</span>
            <select data-visa-mode>
              <option value="inclusive" selected>入境日算第 1 天</option>
              <option value="next-day">入境次日算第 1 天</option>
            </select>
          </label>
        </div>
        <div class="tool-rule" data-visa-rule-note></div>
        <label class="tool-field tool-field-wide" data-visa-history-wrap>
          <span>已完成出入境记录</span>
          <textarea data-visa-history rows="4" placeholder="一行一段，例如：2026-01-01 至 2026-01-30。填完后自动计算下一次可免签入境日期。"></textarea>
        </label>
        <div class="tool-result" data-visa-result>
          选择入境日期后，会自动计算最晚离境日期。
        </div>
      </section>
"""


def render_sim_comparison() -> str:
    return f"""
      <section class="tool-panel">
        <div class="tool-panel-head">
          <div>
            <p class="section-kicker">SIM comparison</p>
            <h2>运营商与电话卡套餐对比</h2>
          </div>
          <span>7 个品牌</span>
        </div>
        <div class="tool-result">
          乌兹别克斯坦普通用户会看到的手机卡品牌按 7 个整理：Ucell、Beeline、Mobiuz、Uzmobile / Uztelecom、Humans、OQ、Perfectum。短期旅行真正优先比较前 4 个；后 3 个更适合长期停留后再现场核验。
        </div>
        <div class="compare-table-wrap">
          <table class="compare-table">
            <thead>
              <tr>
                <th>运营商品牌</th>
                <th>官网代表套餐</th>
                <th>优点</th>
                <th>注意点</th>
                <th>旅行建议</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th>Ucell</th>
                <td>TV BOR：45GB / 69,000 索姆；Plus：60GB / 79,000；Max：85GB / 99,000；Ultra：200GB / 119,000。均含乌兹境内通话和 SMS 档位。</td>
                <td>主流品牌，营业厅多；小红书实测有 60,000 / 70,000 索姆月卡可用记录。</td>
                <td>机场柜台套餐未必和官网完全一致；部分地下空间可能信号弱。</td>
                <td>短期旅行优先候选。带护照和现金，办完当场测网页、短信、Yandex Go。</td>
              </tr>
              <tr>
                <th>Beeline</th>
                <td>官网套餐页按地区展示，价格和可办套餐以门店/机场柜台为准；小红书有机场月卡 70,000 索姆记录。</td>
                <td>机场容易遇到，落地马上联网方便；在塔什干覆盖认知度高。</td>
                <td>实测反馈差异大，有人正常，也有人遇到开通后不稳定。</td>
                <td>只适合急用。不要离柜台，必须现场测上网、收短信、注册打车。</td>
              </tr>
              <tr>
                <th>Mobiuz</th>
                <td>ORZU 90：180GB / 90,000 索姆；ORZU 110：250GB / 110,000；Mazza 70：150GB / 70,000；Connect M：10GB / 45,000；Connect L：15GB / 55,000。</td>
                <td>官网套餐信息清楚，大流量月套餐很直观，适合长时间刷地图和视频。</td>
                <td>不一定是机场最容易买到的卡；大流量套餐对短停游客可能过量。</td>
                <td>停留 7 天以上、流量需求高时值得比价；优先市区营业厅办理。</td>
              </tr>
              <tr>
                <th>Uzmobile / Uztelecom</th>
                <td>Travel 5：6GB / 55,000 索姆，500 分钟，500 SMS；Travel 10：12GB / 110,000 索姆，1000 分钟，1000 SMS。</td>
                <td>有明确 Travel 系列，逻辑上更接近游客套餐；Uztelecom 网点体系完整。</td>
                <td>同价位流量不如 Mobiuz / Ucell 大流量月套餐。</td>
                <td>轻度使用、只要地图打车和通讯时可选；重度上网不优先。</td>
              </tr>
              <tr>
                <th>Humans</th>
                <td>官网可见 Super VIP / Tekin 等方案；页面说明其移动服务运行在 Uzmobile 网络上。</td>
                <td>数字化程度高，适合愿意用 App 管理套餐的人。</td>
                <td>游客现场办理便利度不如传统大店；需要确认护照开户注册流程。</td>
                <td>不作为第一选择；除非同行已验证门店和开卡流程。</td>
              </tr>
              <tr>
                <th>OQ</th>
                <td>数字运营商品牌，官网主打 App 和 SIM 购买入口，套餐以 App/销售点实时显示为准。</td>
                <td>线上体验更现代，适合长期停留后再研究。</td>
                <td>游客落地即用的不确定性更高。</td>
                <td>短期游客先不优先；有本地朋友协助时再考虑。</td>
              </tr>
              <tr>
                <th>Perfectum</th>
                <td>官网套餐页访问不稳定，公开资料显示更偏小众移动/宽带方向。</td>
                <td>可作为补充品牌了解。</td>
                <td>游客柜台可得性和手机兼容性需要现场确认。</td>
                <td>不建议短期旅行首选。</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="tool-result">
          <strong>直接建议：</strong>短期旅行优先看 Ucell、Mobiuz、Uzmobile Travel；机场急用才看 Beeline。长期停留再比较 Humans、OQ、Perfectum。所有套餐价格会变，办理前以柜台和官网为准；拿到卡后先测上网、短信、打车软件，再离开柜台。资料入口：<a href="https://ucell.uz/ru/" target="_blank" rel="noopener noreferrer">Ucell</a>、<a href="https://beeline.uz/ru/tariffs" target="_blank" rel="noopener noreferrer">Beeline</a>、<a href="https://mobi.uz/ru/tariffs/" target="_blank" rel="noopener noreferrer">Mobiuz</a>、<a href="https://uztelecom.uz/ru/chastnym-litsam/mobilnaya-svyaz-1/gsm/tarify/travel-2" target="_blank" rel="noopener noreferrer">Uzmobile Travel</a>、<a href="https://humans.uz/" target="_blank" rel="noopener noreferrer">Humans</a>、<a href="https://oq.uz/" target="_blank" rel="noopener noreferrer">OQ</a>、<a href="https://perfectum.uz/ru/tariffs/" target="_blank" rel="noopener noreferrer">Perfectum</a>。
        </div>
      </section>
"""


def render_train_tickets() -> str:
    return f"""
      <section class="tool-panel" data-train-ticket-tool>
        <div class="tool-panel-head">
          <div>
            <p class="section-kicker">火车票</p>
            <h2>火车票查询与代订</h2>
          </div>
          <span>服务端订单</span>
        </div>
        <div class="tool-result">
          这里先收集用户行程、乘客和联系资料；选择出发、到达、日期和人数后，系统同步可选车次与座席，用户确认座席后才能进入订单预览和付款。
        </div>
        <div class="tool-form">
          <label class="tool-field">
            <span>出发国家</span>
            <select data-train-country>
              <option value="KZ">哈萨克斯坦</option>
              <option value="UZ">乌兹别克斯坦</option>
            </select>
          </label>
          <label class="tool-field">
            <span>到达国家（可跨国）</span>
            <select data-train-arrival-country>
              <option value="KZ">哈萨克斯坦</option>
              <option value="UZ">乌兹别克斯坦</option>
            </select>
          </label>
          <label class="tool-field">
            <span>行程类型</span>
            <select data-train-trip>
              <option value="oneway">单程</option>
              <option value="round">往返</option>
            </select>
          </label>
          <label class="tool-field">
            <span>出发城市 / 车站</span>
            <select data-train-from>
              <option value="" selected>请选择出发城市 / 车站</option>
              <option value="阿拉木图-2">阿拉木图-2（市中心主客运站）</option>
              <option value="阿拉木图-1">阿拉木图-1（北部车站，离市中心更远）</option>
              <option value="阿斯塔纳">阿斯塔纳</option>
              <option value="奇姆肯特">奇姆肯特</option>
              <option value="突厥斯坦">突厥斯坦</option>
            </select>
            <small>阿拉木图-2是市中心主客运站，常作为旅客默认选择；阿拉木图-1在城市北部/东北部，离市中心更远，部分线路会经停或从这里走。一般都是阿拉木图-2出发，具体站点信息以出票后的车票为准；订票时必须按车票站名 Almaty-1 或 Almaty-2 选择。</small>
          </label>
          <label class="tool-field">
            <span>到达城市 / 车站</span>
            <select data-train-to>
              <option value="" selected>请选择到达城市 / 车站</option>
              <option value="阿拉木图-2">阿拉木图-2（市中心主客运站）</option>
              <option value="阿拉木图-1">阿拉木图-1（北部车站，离市中心更远）</option>
              <option value="阿斯塔纳">阿斯塔纳</option>
              <option value="奇姆肯特">奇姆肯特</option>
              <option value="突厥斯坦">突厥斯坦</option>
              <option value="塔什干">塔什干</option>
              <option value="撒马尔罕">撒马尔罕</option>
              <option value="布哈拉">布哈拉</option>
              <option value="希瓦">希瓦</option>
              <option value="乌尔根奇">乌尔根奇</option>
              <option value="努库斯">努库斯</option>
              <option value="安集延">安集延</option>
              <option value="费尔干纳">费尔干纳</option>
            </select>
            <small>阿拉木图-2是市中心主客运站，常作为旅客默认选择；阿拉木图-1在城市北部/东北部，离市中心更远，部分线路会经停或从这里走。一般都是阿拉木图-2出发，具体站点信息以出票后的车票为准；订票时必须按车票站名 Almaty-1 或 Almaty-2 选择。</small>
          </label>
          <label class="tool-field">
            <span>出发日期</span>
            <input type="date" data-train-date>
          </label>
          <label class="tool-field">
            <span>乘客人数</span>
            <input type="number" min="1" max="6" value="1" data-train-passengers>
          </label>
          <label class="tool-field">
            <span>座席偏好</span>
            <select data-train-seat>
              <option value="任意可出票座席">任意可出票座席</option>
              <option value="二等座 / 坐席">二等座 / 坐席</option>
              <option value="卧铺">卧铺</option>
              <option value="包厢">包厢</option>
            </select>
          </label>
          <input type="hidden" data-train-ticket-currency>
          <input type="hidden" data-train-ticket-total>
          <input type="hidden" data-train-exchange-rate>
          <div class="tool-field tool-field-wide">
            <span>车次和座席</span>
            <div class="tool-actions">
              <button class="button secondary" type="button" data-train-search-offers>查询车次和座席</button>
            </div>
            <div class="availability-list" data-train-availability>
              选择出发、到达、日期和人数后，先查询可选座席。
            </div>
          </div>
          <div class="tool-field tool-field-wide">
            <span>乘客信息</span>
            <div class="passenger-form" data-train-passenger-form></div>
          </div>
          <label class="tool-field">
            <span>微信号</span>
            <input type="text" data-train-contact-wechat placeholder="用于接收订票进度">
          </label>
          <label class="tool-field">
            <span>手机号</span>
            <input type="tel" data-train-contact-phone placeholder="含国家区号">
          </label>
          <label class="tool-field">
            <span>邮箱</span>
            <input type="email" data-train-contact-email placeholder="用于接收出票信息">
          </label>
        </div>
        <div class="tool-actions">
          <button class="button primary" type="button" data-train-create-order disabled>生成信息预览</button>
        </div>
        <div class="tool-result" data-train-result>
          选择车次和座席后，再生成订单预览；系统会把中文站名、国籍、证件类型转换为订票流程需要的标准格式。
        </div>
        <div class="tool-form tool-payment-step is-hidden" data-train-payment-step>
          <label class="tool-field">
            <span>支付宝业务流水号</span>
            <input type="text" data-train-pay-ref placeholder="支付后填写">
          </label>
          <label class="tool-field">
            <span>付款金额</span>
            <input type="number" min="1" step="0.01" data-train-paid-amount placeholder="例如 99.03">
          </label>
          <label class="tool-field">
            <span>付款时间</span>
            <input type="datetime-local" data-train-paid-at>
          </label>
          <label class="tool-field tool-field-wide">
            <span>付款成功截图</span>
            <input type="file" accept="image/*" data-train-proof>
            <small>请上传支付宝付款成功页完整截图，截图里必须完整显示支付宝业务流水号、付款金额和付款时间。</small>
          </label>
        </div>
      </section>
"""


def render_topic_page(
    config: dict[str, Any],
    topic: Topic,
    country_lookup: dict[str, Country],
) -> str:
    country = country_lookup.get(topic.country_slug)
    country_name = country.name if country else topic.country
    article = markdown_to_html(read_topic(topic))
    if topic.slug == "local-tools":
        article = "\n".join([article, render_local_tools_index(topic)])
    body = f"""
    <main>
      <article class="article-shell">
        <aside class="article-side">
          <a class="back-link" href="/countries/{topic.country_slug}/">返回 {html.escape(country_name)}</a>
          <span>{html.escape(topic.category)}</span>
          <h1>{html.escape(topic.title)}</h1>
          <p>{html.escape(topic.summary)}</p>
          <p class="article-note">这是一篇会随着新信息继续修订的专题，目的是把具体经验整理成下次还能使用的文字。</p>
        </aside>
        <div class="article-body">
          {article}
        </div>
      </article>
    </main>
"""
    return page_shell(config, topic.title, body, topic.summary)


def render_local_tool_detail_page(
    config: dict[str, Any],
    topic: Topic,
    country_lookup: dict[str, Country],
    tool_slug: str,
) -> str:
    country = country_lookup.get(topic.country_slug)
    country_name = country.name if country else topic.country
    tool_map = {
        "visa-calculator": {
            "title": "免签时间计算器",
            "meta": "中国护照",
            "summary": "填写每次出入境时间，计算本次最晚离境日和下一次可免签入境日期。",
            "content": render_visa_calculator(),
        },
        "sim-comparison": {
            "title": "运营商与电话卡套餐对比",
            "meta": "乌兹别克斯坦",
            "summary": "按运营商品牌对比代表套餐、优缺点和旅行办理建议。",
            "content": render_sim_comparison(),
        },
        "train-tickets": {
            "title": "火车票查询与代订",
            "meta": "乌兹别克斯坦 / 哈萨克斯坦",
            "summary": "填写路线、日期、乘客和付款信息，生成服务端订单并进入后续出票流程。",
            "content": render_train_tickets(),
        },
    }
    tool = tool_map[tool_slug]
    body = f"""
    <main>
      <article class="article-shell">
        <aside class="article-side">
          <a class="back-link" href="/countries/{topic.country_slug}/topics/{topic.slug}/">返回工具合集</a>
          <span>{html.escape(tool["meta"])}</span>
          <h1>{html.escape(tool["title"])}</h1>
          <p>{html.escape(tool["summary"])}</p>
          <p class="article-note">归入 {html.escape(country_name)} 的工具合集，后续可以继续修订和补充。</p>
        </aside>
        <div class="article-body">
          {tool["content"]}
        </div>
      </article>
    </main>
"""
    return page_shell(config, str(tool["title"]), body, str(tool["summary"]))


def render_operate_page(
    config: dict[str, Any],
    countries: list[Country],
    topics: list[Topic],
    dining_places: list[DiningPlace],
) -> str:
    online_count = len([country for country in countries if country.status == "online"])
    body = f"""
    <main>
      <section class="country-hero">
        <p class="eyebrow">Operate</p>
        <h1>维护工作台</h1>
        <p class="lead">这里保留后续加国家、加专题、更新网站和免费部署的操作入口。内容不靠复杂系统支撑，只用清楚的文件结构，把长期有用的观察慢慢保存下来。</p>
      </section>
      <section class="section">
        <div class="ops-grid">
          <article class="ops-card">
            <span>Content</span>
            <strong>Markdown 内容源</strong>
            <p>路径：content/countries/国家 slug/topics/专题 slug.md</p>
          </article>
          <article class="ops-card">
            <span>Index</span>
            <strong>国家与专题配置</strong>
            <p>路径：tools/site.config.json。标题、分类、摘要、排序都在这里改。</p>
          </article>
          <article class="ops-card">
            <span>Build</span>
            <strong>重新生成网页</strong>
            <p>运行：python3 work/build_notes_site.py。生成后直接部署整个网站目录。</p>
          </article>
        </div>
      </section>
      <section class="section">
        <div class="section-head">
          <div>
            <p class="section-kicker">Current scale</p>
            <h2>当前容量</h2>
          </div>
        </div>
        <dl class="metric-list">
          <div><dt>上线国家</dt><dd>{online_count}</dd></div>
          <div><dt>专题页面</dt><dd>{len(topics)}</dd></div>
          <div><dt>探店记录</dt><dd>{len(dining_places)}</dd></div>
          <div><dt>预留国家位</dt><dd>{len(countries) - online_count}</dd></div>
        </dl>
      </section>
    </main>
    <footer class="site-footer">
      <span>{html.escape(str(config.get("siteName", "Quiet Atlas")))}</span>
      <span>维护区</span>
    </footer>
"""
    return page_shell(config, "维护工作台", body, "网站维护方式")


def write_assets() -> None:
    styles = r"""
:root {
  --bg: #f7f5f1;
  --surface: #ffffff;
  --ink: #171511;
  --muted: #756f66;
  --soft: #efede8;
  --line: #ded9cf;
  --accent: #5d5548;
  --max: 1180px;
  --display: "Songti SC", "STSong", "Noto Serif CJK SC", "Source Han Serif SC", serif;
  --text: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", sans-serif;
}

* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: var(--text);
  letter-spacing: 0;
}

a {
  color: inherit;
  text-decoration: none;
}

.site-header {
  position: sticky;
  top: 0;
  z-index: 5;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 max(28px, calc((100vw - var(--max)) / 2));
  background: rgba(247, 245, 241, 0.88);
  border-bottom: 1px solid var(--line);
  backdrop-filter: blur(18px);
}

.brand {
  display: grid;
  gap: 2px;
  font-family: var(--display);
  font-size: 19px;
  font-weight: 700;
  line-height: 1;
}

.brand small {
  color: var(--muted);
  font-family: var(--text);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

nav {
  display: flex;
  gap: 26px;
  color: var(--muted);
  font-size: 14px;
}

main {
  min-height: calc(100vh - 72px);
}

.hero {
  max-width: var(--max);
  margin: 0 auto;
  min-height: 760px;
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) 420px;
  gap: 80px;
  align-items: center;
  padding: 78px 28px 92px;
}

.eyebrow,
.section-kicker {
  margin: 0 0 18px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 650;
  text-transform: uppercase;
}

h1,
h2,
h3 {
  letter-spacing: 0;
  font-family: var(--display);
}

.hero h1,
.country-hero h1 {
  margin: 0;
  max-width: 860px;
  font-size: clamp(48px, 7.2vw, 94px);
  line-height: 1.04;
  font-weight: 700;
}

.lead {
  max-width: 760px;
  margin: 30px 0 0;
  color: var(--muted);
  font-size: 21px;
  line-height: 1.78;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-top: 42px;
  flex-wrap: wrap;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 50px;
  padding: 0 24px;
  border-radius: 8px;
  font-size: 15px;
}

.button.primary {
  background: var(--ink);
  color: #fff;
}

.button.ghost {
  border: 1px solid var(--line);
  color: var(--muted);
}

.index-panel {
  min-height: 520px;
  padding: 38px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.72);
}

.panel-label {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  text-transform: uppercase;
}

.index-panel h2 {
  margin: 18px 0 34px;
  font-size: 38px;
}

.index-panel dl {
  display: grid;
  gap: 12px;
  margin: 0 0 42px;
}

.index-panel dl div,
.metric-list div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
}

.index-panel dt,
.metric-list dt {
  color: var(--muted);
}

.index-panel dd,
.metric-list dd {
  margin: 0;
  font-weight: 650;
}

.index-panel a,
.text-link,
.back-link {
  color: var(--accent);
  font-weight: 650;
}

.section {
  max-width: var(--max);
  margin: 0 auto;
  padding: 84px 28px;
  border-top: 1px solid var(--line);
}

.section-head {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 34px;
}

.section h2 {
  margin: 0;
  font-size: clamp(34px, 4vw, 56px);
  line-height: 1;
}

.section-copy {
  max-width: 620px;
  margin: 22px 0 0;
  color: var(--muted);
  font-size: 17px;
  line-height: 1.8;
}

.manifesto {
  padding-top: 96px;
  padding-bottom: 96px;
}

.manifesto-grid {
  display: grid;
  grid-template-columns: minmax(0, 0.95fr) minmax(280px, 0.55fr);
  gap: 76px;
  align-items: end;
}

.manifesto-grid h2 {
  max-width: 820px;
  font-size: clamp(46px, 6.2vw, 86px);
  line-height: 1.04;
  font-weight: 650;
}

.manifesto-grid p {
  margin: 0;
  color: var(--muted);
  font-size: 19px;
  line-height: 1.85;
}

.country-grid,
.topic-grid,
.ops-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.country-card,
.topic-card,
.ops-card {
  min-height: 224px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 28px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.62);
}

.country-card span,
.topic-meta,
.ops-card span {
  color: var(--accent);
  font-size: 13px;
  font-weight: 650;
}

.country-card strong,
.topic-card strong,
.ops-card strong {
  display: block;
  margin: 28px 0 14px;
  font-size: 25px;
  line-height: 1.2;
}

.country-card p,
.topic-card p,
.ops-card p {
  margin: 0;
  color: var(--muted);
  font-size: 16px;
  line-height: 1.68;
}

.muted-card {
  background: transparent;
  border-style: dashed;
}

.search-box {
  width: min(360px, 100%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 18px;
  min-height: 48px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--surface);
  color: var(--muted);
}

.search-box input {
  min-width: 0;
  width: 100%;
  border: 0;
  outline: 0;
  background: transparent;
  font: inherit;
  color: var(--ink);
}

.steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  padding: 0;
  margin: 34px 0 0;
  list-style: none;
  border-top: 1px solid var(--line);
}

.steps li {
  min-height: 178px;
  padding: 28px 24px 0 0;
}

.steps li + li {
  border-left: 1px solid var(--line);
  padding-left: 24px;
}

.steps strong,
.steps span {
  display: block;
}

.steps strong {
  font-size: 20px;
  margin-bottom: 14px;
}

.steps span {
  color: var(--muted);
  line-height: 1.68;
}

.country-hero {
  max-width: var(--max);
  margin: 0 auto;
  padding: 108px 28px 92px;
}

.article-shell {
  max-width: var(--max);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 72px;
  padding: 72px 28px 110px;
}

.article-side {
  position: sticky;
  top: 104px;
  align-self: start;
}

.article-side span {
  display: inline-block;
  margin-top: 42px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
}

.article-side h1 {
  margin: 18px 0;
  font-size: 46px;
  line-height: 1.06;
}

.article-side p {
  color: var(--muted);
  line-height: 1.75;
}

.article-side .article-note {
  margin-top: 28px;
  padding-top: 24px;
  border-top: 1px solid var(--line);
  font-size: 15px;
}

.article-body {
  padding: 56px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
}

.article-body h1 {
  margin: 0 0 36px;
  font-size: 48px;
  line-height: 1.12;
}

.article-body h2 {
  margin: 64px 0 20px;
  font-size: 32px;
}

.article-body h3 {
  margin: 36px 0 14px;
  font-size: 23px;
}

.article-body p,
.article-body li {
  color: #343434;
  font-size: 17px;
  line-height: 1.9;
}

.article-body a {
  color: #3d352a;
  border-bottom: 1px solid currentColor;
  font-weight: 650;
  text-decoration: none;
}

.article-body blockquote {
  margin: 28px 0;
  padding: 4px 0 4px 22px;
  border-left: 3px solid var(--accent);
}

.article-body code {
  padding: 2px 6px;
  border-radius: 7px;
  background: var(--soft);
}

.article-body hr {
  margin: 34px 0;
  border: 0;
  border-top: 1px solid var(--line);
}

.metric-list {
  max-width: 740px;
  margin: 0;
  padding: 0;
}

.quiet-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  border-top: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
}

.quiet-stats div {
  min-height: 150px;
  padding: 28px;
}

.quiet-stats div + div {
  border-left: 1px solid var(--line);
}

.quiet-stats span {
  display: block;
  color: var(--muted);
  font-size: 14px;
}

.quiet-stats strong {
  display: block;
  margin-top: 24px;
  font-family: var(--display);
  font-size: clamp(42px, 6vw, 78px);
  line-height: 0.9;
}

.dining-list,
.review-list {
  display: grid;
  gap: 14px;
}

.dining-card,
.review-card {
  padding: 24px 0 28px;
  border-top: 1px solid var(--line);
}

.dining-card-head,
.dining-links {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.dining-card-head span {
  color: var(--muted);
  font-size: 13px;
}

.dining-card em,
.review-card em {
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  padding: 0 10px;
  border: 1px solid var(--line);
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
  font-style: normal;
}

.dining-card em.confirmed,
.review-card em.confirmed {
  color: #233a2c;
  border-color: #9db3a4;
}

.dining-card h3,
.review-card h3 {
  margin: 18px 0 10px;
  font-size: clamp(30px, 4vw, 50px);
  line-height: 1.08;
}

.dining-card p,
.review-card p {
  max-width: 760px;
  margin: 0 0 22px;
  color: var(--muted);
  line-height: 1.72;
}

.dining-card dl,
.review-card dl {
  display: grid;
  gap: 0;
  margin: 0;
  border-top: 1px solid var(--line);
}

.dining-card dl div,
.review-card dl div {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 20px;
  padding: 13px 0;
  border-bottom: 1px solid var(--line);
}

.dining-card dt,
.review-card dt {
  color: var(--muted);
}

.dining-card dd,
.review-card dd {
  margin: 0;
  overflow-wrap: anywhere;
}

.source-actions {
  margin-top: 0;
  border-bottom: 1px solid var(--line);
}

.source-author {
  display: grid;
  gap: 10px;
  padding: 20px 0 24px;
}

.source-author span {
  color: var(--muted);
  font-size: 17px;
  font-weight: 650;
}

.source-author strong {
  color: var(--ink);
  font-size: clamp(24px, 3vw, 34px);
  font-weight: 500;
  line-height: 1.15;
  overflow-wrap: anywhere;
}

.dining-links {
  justify-content: flex-start;
  padding: 20px 0 24px;
  margin-top: 0;
  border-top: 1px solid var(--line);
}

.article-body a,
.dining-links a {
  color: #3d352a;
  border-bottom: 1px solid currentColor;
  font-weight: 650;
  text-decoration: none;
}

.site-footer {
  max-width: var(--max);
  margin: 0 auto;
  padding: 30px 28px 46px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 14px;
}

.footer-link {
  color: inherit;
  text-decoration: none;
  border-bottom: 1px solid currentColor;
}

.footer-link:hover {
  color: var(--ink);
}

.tool-card-section {
  margin-top: 42px;
}

.tool-card-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.tool-card {
  display: grid;
  gap: 16px;
  min-height: 210px;
  padding: 26px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.68);
  color: inherit;
  text-decoration: none;
  transition: border-color 180ms ease, transform 180ms ease, background 180ms ease;
}

.tool-card:hover {
  transform: translateY(-2px);
  border-color: rgba(26, 24, 21, 0.35);
  background: #fff;
}

.tool-card span {
  color: var(--accent);
  font-size: 13px;
  font-weight: 650;
}

.tool-card strong {
  max-width: 520px;
  color: var(--ink);
  font-size: clamp(28px, 4vw, 46px);
  font-weight: 500;
  line-height: 1.08;
}

.tool-card p {
  max-width: 560px;
  margin: 0;
  color: var(--muted);
  line-height: 1.72;
}

.tool-panel {
  margin-top: 42px;
  padding: 32px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.68);
}

.tool-panel-head {
  display: flex;
  align-items: start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 28px;
}

.tool-panel-head h2 {
  margin: 0;
  font-size: 32px;
}

.tool-panel-head > span {
  color: var(--accent);
  font-size: 13px;
  font-weight: 650;
}

.tool-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.tool-field {
  display: grid;
  gap: 9px;
  color: var(--muted);
  font-size: 13px;
  font-weight: 650;
}

.tool-field input,
.tool-field select,
.tool-field textarea {
  min-height: 48px;
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
  font: inherit;
  padding: 0 14px;
}

.tool-field textarea {
  min-height: 112px;
  padding: 14px;
  line-height: 1.65;
  resize: vertical;
}

.tool-field-wide {
  margin-top: 16px;
}

.tool-rule {
  margin-top: 18px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.72;
}

.tool-rule strong {
  color: var(--ink);
}

.tool-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 22px;
}

.passenger-form {
  display: grid;
  gap: 16px;
}

.passenger-card {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
}

.passenger-card h3 {
  grid-column: 1 / -1;
  margin: 0;
  color: var(--ink);
  font-size: 18px;
  font-weight: 560;
}

.passenger-card .tool-field {
  font-size: 12px;
}

.availability-list {
  display: grid;
  gap: 12px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
}

.ticket-option {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
}

.ticket-option strong {
  display: block;
  color: var(--ink);
  font-size: 17px;
  font-weight: 560;
}

.ticket-option span {
  display: block;
}

.ticket-seat-pool {
  margin-top: 4px;
  color: var(--muted);
}

.ticket-timeline {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 10px 0;
}

.ticket-timeline span {
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
  color: var(--ink);
}

.ticket-timeline b {
  display: block;
  margin-bottom: 2px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 520;
}

.payment-qr {
  display: block;
  width: min(220px, 100%);
  height: auto;
  margin-top: 12px;
  border: 1px solid var(--line);
  border-radius: 8px;
}

.compare-table-wrap {
  overflow-x: auto;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #fff;
}

.compare-table {
  width: 100%;
  min-width: 860px;
  border-collapse: collapse;
  font-size: 14px;
  line-height: 1.62;
}

.compare-table th,
.compare-table td {
  padding: 16px;
  border-bottom: 1px solid var(--line);
  text-align: left;
  vertical-align: top;
}

.compare-table thead th {
  color: var(--accent);
  font-size: 12px;
  text-transform: uppercase;
  background: rgba(247, 245, 241, 0.72);
}

.compare-table tbody th {
  width: 148px;
  color: var(--ink);
  font-weight: 700;
}

.compare-table tbody tr:last-child th,
.compare-table tbody tr:last-child td {
  border-bottom: 0;
}

.tool-result {
  margin-top: 22px;
  padding-top: 22px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  line-height: 1.75;
}

.tool-result strong {
  color: var(--ink);
}

.tool-result.is-ok strong {
  color: #2f5d45;
}

.tool-result.is-warn strong {
  color: #8b3f2f;
}

.is-hidden {
  display: none;
}

@media (max-width: 900px) {
  .site-header {
    padding: 0 20px;
  }

  nav {
    gap: 14px;
    font-size: 13px;
  }

  .hero,
  .article-shell {
    grid-template-columns: 1fr;
  }

  .hero {
    gap: 42px;
    min-height: auto;
    padding-top: 64px;
  }

  .hero h1,
  .country-hero h1 {
    font-size: clamp(42px, 13vw, 62px);
  }

  .country-grid,
  .topic-grid,
  .ops-grid,
  .manifesto-grid,
  .quiet-stats,
  .steps,
  .tool-card-grid,
  .tool-form {
    grid-template-columns: 1fr;
  }

  .tool-card {
    min-height: 180px;
    padding: 22px;
  }

  .quiet-stats div + div {
    border-left: 0;
    border-top: 1px solid var(--line);
  }

  .steps li + li {
    border-left: 0;
    border-top: 1px solid var(--line);
    padding-left: 0;
  }

  .section-head {
    align-items: start;
    flex-direction: column;
  }

  .article-side {
    position: static;
  }

  .article-body {
    padding: 30px 22px;
    border-radius: 8px;
  }

  .dining-card dl div,
  .review-card dl div {
    grid-template-columns: 1fr;
    gap: 6px;
  }

  .site-footer {
    flex-direction: column;
    gap: 10px;
  }

  .passenger-card {
    grid-template-columns: 1fr;
  }

  .ticket-option {
    grid-template-columns: 1fr;
  }

  .ticket-timeline {
    grid-template-columns: 1fr;
  }
}
"""
    script = r"""
const input = document.querySelector("[data-search]");
const cards = [...document.querySelectorAll("[data-topic-list] [data-search-card]")];

if (input && cards.length) {
  input.addEventListener("input", () => {
    const query = input.value.trim().toLowerCase();
    cards.forEach((card) => {
      const text = card.textContent.toLowerCase();
      card.classList.toggle("is-hidden", query && !text.includes(query));
    });
  });
}

const visaCalculator = document.querySelector("[data-visa-calculator]");

const trainTicketTool = document.querySelector("[data-train-ticket-tool]");

if (trainTicketTool) {
  const countryInput = trainTicketTool.querySelector("[data-train-country]");
  const arrivalCountryInput = trainTicketTool.querySelector("[data-train-arrival-country]");
  const fromInput = trainTicketTool.querySelector("[data-train-from]");
  const toInput = trainTicketTool.querySelector("[data-train-to]");
  const dateInput = trainTicketTool.querySelector("[data-train-date]");
  const passengersInput = trainTicketTool.querySelector("[data-train-passengers]");
  const seatInput = trainTicketTool.querySelector("[data-train-seat]");
  const ticketCurrencyInput = trainTicketTool.querySelector("[data-train-ticket-currency]");
  const ticketTotalInput = trainTicketTool.querySelector("[data-train-ticket-total]");
  const exchangeRateInput = trainTicketTool.querySelector("[data-train-exchange-rate]");
  const searchOffersButton = trainTicketTool.querySelector("[data-train-search-offers]");
  const availabilityList = trainTicketTool.querySelector("[data-train-availability]");
  const passengerForm = trainTicketTool.querySelector("[data-train-passenger-form]");
  const contactWechatInput = trainTicketTool.querySelector("[data-train-contact-wechat]");
  const contactPhoneInput = trainTicketTool.querySelector("[data-train-contact-phone]");
  const contactEmailInput = trainTicketTool.querySelector("[data-train-contact-email]");
  const payRefInput = trainTicketTool.querySelector("[data-train-pay-ref]");
  const paidAmountInput = trainTicketTool.querySelector("[data-train-paid-amount]");
  const paidAtInput = trainTicketTool.querySelector("[data-train-paid-at]");
  const proofInput = trainTicketTool.querySelector("[data-train-proof]");
  const paymentStep = trainTicketTool.querySelector("[data-train-payment-step]");
  const createButton = trainTicketTool.querySelector("[data-train-create-order]");
  const result = trainTicketTool.querySelector("[data-train-result]");
  let selectedOffer = null;
  let currentOffers = [];

  const htmlEscape = (value) => String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");

  const formatDateTime = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const hours = String(date.getHours()).padStart(2, "0");
    const minutes = String(date.getMinutes()).padStart(2, "0");
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  const timeToMinutes = (value) => {
    const match = String(value || "").match(/(\d{1,2})[:：](\d{2})/);
    if (!match) return null;
    return Number(match[1]) * 60 + Number(match[2]);
  };

  const formatDuration = (departTime, arriveTime, fallback = "") => {
    if (fallback) return fallback;
    const departMinutes = timeToMinutes(departTime);
    const arriveMinutes = timeToMinutes(arriveTime);
    if (departMinutes === null || arriveMinutes === null) return "运行时长以系统同步为准";
    let diff = arriveMinutes - departMinutes;
    if (diff <= 0) diff += 24 * 60;
    const hours = Math.floor(diff / 60);
    const minutes = diff % 60;
    return `${hours}小时${String(minutes).padStart(2, "0")}分钟`;
  };

  const quoteTotalCny = (localTotal, rate) => {
    const amount = Number(localTotal || 0) * Number(rate || 0) * 1.2;
    return Number.isFinite(amount) && amount > 0 ? Number(amount.toFixed(2)) : 0;
  };

  const splitSeatDetails = (value) => String(value || "")
    .split(/[、,，;；]/)
    .map((item) => item.trim())
    .filter(Boolean);

  const buildSeatDetails = (seat, scheduleIndex, seatIndex, seatCount) => {
    const count = Math.min(12, Math.max(1, Number(seatCount || 1)));
    const carNo = String(3 + scheduleIndex + seatIndex).padStart(2, "0");
    if (String(seat).includes("卧铺")) {
      const berths = ["下铺", "中铺", "上铺", "下铺", "中铺", "上铺"];
      return Array.from({ length: count }, (_, index) => `${carNo}车 ${12 + scheduleIndex * 3 + index}${berths[(index + seatIndex) % berths.length]}`);
    }
    if (String(seat).includes("包厢")) {
      return Array.from({ length: count }, (_, index) => `${carNo}车 ${2 + scheduleIndex + index}号包厢`);
    }
    const letters = ["A", "B", "C", "D", "F"];
    return Array.from({ length: count }, (_, index) => `${carNo}车 ${10 + scheduleIndex * 4 + Math.floor(index / letters.length)}${letters[(index + seatIndex) % letters.length]}`);
  };

  const buildSeatDetail = (seat, scheduleIndex, seatIndex, passengerCount) =>
    buildSeatDetails(seat, scheduleIndex, seatIndex, passengerCount).join("、");

  const uzbekStations = ["塔什干", "撒马尔罕", "布哈拉", "希瓦", "乌尔根奇", "努库斯", "安集延", "费尔干纳"];
  const kazakhStations = [
    { value: "阿拉木图-2", label: "阿拉木图-2（市中心主客运站）" },
    { value: "阿拉木图-1", label: "阿拉木图-1（北部车站，离市中心更远）" },
    { value: "阿斯塔纳", label: "阿斯塔纳" },
    { value: "奇姆肯特", label: "奇姆肯特" },
    { value: "突厥斯坦", label: "突厥斯坦" },
  ];
  const kazakhStationValues = kazakhStations.map((station) => station.value);
  const stationOptions = {
    KZ: kazakhStations,
    UZ: uzbekStations.map((name) => ({ value: name, label: name })),
  };
  const allStationOptions = [...stationOptions.KZ, ...stationOptions.UZ];

  const renderStationOptions = (select, options, placeholder) => {
    if (!select) return;
    const currentValue = select.value;
    select.innerHTML = [
      `<option value="">${placeholder}</option>`,
      ...options.map((option) => `<option value="${htmlEscape(option.value)}">${htmlEscape(option.label)}</option>`),
    ].join("");
    select.value = options.some((option) => option.value === currentValue) ? currentValue : "";
  };

  const renderStationSelects = () => {
    renderStationOptions(fromInput, stationOptions[countryInput?.value || "KZ"] || [], "请选择出发城市 / 车站");
    renderStationOptions(toInput, allStationOptions, "请选择到达城市 / 车站");
  };

  const getStationDepartureCountry = () => {
    if (uzbekStations.includes(fromInput.value)) return "UZ";
    if (kazakhStationValues.includes(fromInput.value)) return "KZ";
    return "";
  };

  const getStationArrivalCountry = () => {
    if (uzbekStations.includes(toInput.value)) return "UZ";
    if (kazakhStationValues.includes(toInput.value)) return "KZ";
    return "";
  };

  const syncDepartureCountryFromStation = () => {
    const inferred = getStationDepartureCountry();
    if (countryInput && inferred) countryInput.value = inferred;
  };

  const syncArrivalCountryFromStation = () => {
    const inferred = getStationArrivalCountry();
    if (arrivalCountryInput && inferred) arrivalCountryInput.value = inferred;
  };

  const getDepartureCountry = () => {
    const inferred = getStationDepartureCountry();
    if (inferred) return inferred;
    return countryInput?.value || "KZ";
  };

  const getArrivalCountry = () => {
    const inferred = getStationArrivalCountry();
    if (inferred) return inferred;
    return arrivalCountryInput?.value || "KZ";
  };

  const getTrainApiBase = () => String(
    window.QUIET_ATLAS_API_BASE || trainTicketTool.getAttribute("data-api-base") || ""
  ).replace(/\/$/, "");

  const getDepartureCurrency = () => getDepartureCountry() === "UZ" ? "UZS" : "KZT";
  const getRateForCurrency = (currency) => currency === "UZS" ? 0.000564 : 0.0145;

  const resetSelectedOffer = () => {
    selectedOffer = null;
    currentOffers = [];
    ticketCurrencyInput.value = "";
    ticketTotalInput.value = "";
    exchangeRateInput.value = "";
    createButton.disabled = true;
    if (paymentStep) paymentStep.classList.add("is-hidden");
  };

  const normalizeOffer = (offer, index) => {
    const departTime = offer.depart_time || offer.departure_time || "";
    const arriveTime = offer.arrive_time || offer.arrival_time || "";
    const duration = formatDuration(departTime, arriveTime, offer.duration || offer.duration_text || offer.runtime || "");
    const time = offer.time || [departTime, arriveTime].filter(Boolean).join(" - ") || "时间以系统同步为准";
    const passengerCount = Math.min(6, Math.max(1, Number(passengersInput.value || 1)));
    const seatLabel = offer.seat || offer.seat_type || offer.seat_class || seatInput.value || "可出票座席";
    const leftCount = Number(offer.left ?? offer.available_seats ?? offer.available ?? 0);
    const availableCount = Math.min(12, Math.max(passengerCount, leftCount || passengerCount));
    let seatOptions = Array.isArray(offer.seat_options)
      ? offer.seat_options.map((item) => String(item || "").trim()).filter(Boolean)
      : splitSeatDetails(offer.seat_options || offer.available_seat_details || offer.available_seats_detail || offer.seat_detail_list);
    const rawSeatDetail = offer.seat_detail || offer.seat_no || offer.seat_number || offer.berth || "";
    if (!seatOptions.length) seatOptions = splitSeatDetails(rawSeatDetail);
    if (seatOptions.length < Math.min(availableCount, 6)) {
      seatOptions = buildSeatDetails(seatLabel, index, 0, availableCount);
    }
    const selectedSeatDetails = seatOptions.slice(0, passengerCount);
    return {
      trainNo: offer.trainNo || offer.train_no || offer.train || `可选车次 ${index + 1}`,
      departTime: departTime || "开车时间以系统同步为准",
      arriveTime: arriveTime || "到达时间以系统同步为准",
      duration,
      time,
      seat: seatLabel,
      seatDetail: selectedSeatDetails.join("、") || rawSeatDetail || "座位号以系统同步为准",
      seatOptions,
      seatOptionsText: seatOptions.slice(0, 8).join("、"),
      left: leftCount,
      currency: String(offer.currency || offer.ticket_currency || "").toUpperCase(),
      total: Number(offer.total ?? offer.ticket_total_local ?? offer.price_total ?? offer.price ?? 0),
      rate: Number(offer.rate ?? offer.exchange_rate ?? 0),
      totalCny: Number(offer.total_cny ?? offer.ticket_total_cny ?? offer.payable_preview_cny ?? quoteTotalCny(
        Number(offer.total ?? offer.ticket_total_local ?? offer.price_total ?? offer.price ?? 0),
        Number(offer.rate ?? offer.exchange_rate ?? 0)
      )),
      liveSynced: offer.live_synced === true || offer.liveSynced === true,
      syncedAt: offer.synced_at || offer.syncedAt || "",
    };
  };

  const renderOffers = (offers, emptyMessage = "") => {
    resetSelectedOffer();
    currentOffers = offers
      .map(normalizeOffer)
      .filter((offer) => offer.liveSynced && offer.left > 0 && offer.total > 0 && offer.rate > 0 && offer.currency);
    if (!currentOffers.length) {
      availabilityList.innerHTML = emptyMessage || "当前日期暂无可选座席，请返回修改日期或路线后重新查询；没有可选座席时不能进入下一步。";
      return;
    }
    availabilityList.innerHTML = currentOffers.map((offer, index) => `
      <div class="ticket-option">
        <div>
          <strong>${htmlEscape(offer.trainNo)} · ${htmlEscape(offer.seat)}</strong>
          <div class="ticket-timeline">
            <span><b>开车（当地时间）</b>${htmlEscape(offer.departTime)}</span>
            <span><b>运行</b>${htmlEscape(offer.duration)}</span>
            <span><b>到达（当地时间）</b>${htmlEscape(offer.arriveTime)}</span>
          </div>
          <span>本单座位/铺位：${htmlEscape(offer.seatDetail)}</span>
          <span class="ticket-seat-pool">可选座位/铺位：${htmlEscape(offer.seatOptionsText || offer.seatDetail)}</span>
          <span>余票 ${htmlEscape(offer.left)} 张 · 人民币总价 ${htmlEscape(offer.totalCny ? offer.totalCny.toFixed(2) : "以订单预览为准")} 元</span>
          <span class="ticket-seat-pool">车次、座位和价格已实时同步${offer.syncedAt ? `：${htmlEscape(offer.syncedAt)}` : ""}</span>
        </div>
        <button class="button secondary" type="button" data-train-select-offer="${index}">选择</button>
      </div>
    `).join("");
  };

  const queryOffers = async () => {
    const missing = [];
    if (!fromInput.value) missing.push("出发城市 / 车站");
    if (!toInput.value) missing.push("到达城市 / 车站");
    if (!dateInput.value) missing.push("出发日期");
    if (!passengersInput.value || Number(passengersInput.value) < 1) missing.push("乘客人数");
    if (fromInput.value && toInput.value && fromInput.value === toInput.value) missing.push("不同的到达城市 / 车站");
    if (missing.length) {
      resetSelectedOffer();
      availabilityList.innerHTML = `请先补全：<strong>${missing.map(htmlEscape).join("、")}</strong>。`;
      return;
    }
    availabilityList.innerHTML = "正在同步车次和座席信息...";
    try {
      const body = JSON.stringify({
        train_country: getDepartureCountry(),
        arrival_country: getArrivalCountry(),
        from_station: fromInput.value,
        to_station: toInput.value,
        depart_date: dateInput.value,
        passengers: Number(passengersInput.value || 1),
        seat_preference: seatInput.value,
      });
      const configuredApiBase = getTrainApiBase();
      const isLocalHost = ["127.0.0.1", "localhost"].includes(window.location.hostname);
      const apiBases = configuredApiBase ? [configuredApiBase] : ["", ...(isLocalHost ? ["http://127.0.0.1:8787"] : [])];
      let payload = null;
      for (const apiBase of apiBases) {
        try {
          const response = await fetch(`${apiBase}/api/train-availability`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body,
          });
          if (response.ok) {
            payload = await response.json();
            break;
          }
        } catch (error) {}
      }
      if (payload && Array.isArray(payload.offers) && payload.offers.length) {
        renderOffers(payload.offers, payload.message || "");
      } else {
        renderOffers([], payload?.message || "暂时没有同步到实时车次、座位和价格信息，请稍后重新查询；未同步到实时信息时不能进入下一步。");
      }
    } catch (error) {
      renderOffers([], "实时车次、座位和价格同步暂时不可用，请稍后重新查询；未同步到实时信息时不能进入下一步。");
    }
  };

  const passengerField = (index, key, label, type = "text", options = []) => {
    const attr = `data-passenger-${key}`;
    if (options.length) {
      return `<label class="tool-field"><span>${label}</span><select ${attr}>${options.map((option) => `<option value="${htmlEscape(option.value)}">${htmlEscape(option.label)}</option>`).join("")}</select></label>`;
    }
    return `<label class="tool-field"><span>${label}</span><input type="${type}" ${attr} placeholder="${label}"></label>`;
  };

  const renderPassengerForms = () => {
    const count = Math.min(6, Math.max(1, Number(passengersInput.value || 1)));
    const previous = collectPassengers();
    passengerForm.innerHTML = Array.from({ length: count }, (_, index) => {
      const passenger = previous[index] || {};
      return `
        <div class="passenger-card" data-passenger-card>
          <h3>乘客 ${index + 1}</h3>
          ${passengerField(index, "last-name", "英文姓氏")}
          ${passengerField(index, "first-name", "英文名字")}
          ${passengerField(index, "doc-type", "证件类型", "text", [
            { value: "passport", label: "护照" },
            { value: "id", label: "身份证" },
            { value: "other", label: "其他证件" },
          ])}
          ${passengerField(index, "doc-no", "证件号码")}
          ${passengerField(index, "doc-issued", "护照签发日期", "date")}
          ${passengerField(index, "doc-expiry", "护照到期日期", "date")}
          ${passengerField(index, "birth", "出生日期", "date")}
          ${passengerField(index, "gender", "性别", "text", [
            { value: "M", label: "男" },
            { value: "F", label: "女" },
          ])}
          ${passengerField(index, "nationality", "国籍", "text", [
            { value: "China", label: "中国" },
            { value: "Kazakhstan", label: "哈萨克斯坦" },
            { value: "Uzbekistan", label: "乌兹别克斯坦" },
            { value: "Other", label: "其他" },
          ])}
        </div>
      `;
    }).join("");
    [...passengerForm.querySelectorAll("[data-passenger-card]")].forEach((card, index) => {
      const passenger = previous[index] || {};
      const setValue = (selector, value) => {
        const field = card.querySelector(selector);
        if (field && value) field.value = value;
      };
      setValue("[data-passenger-last-name]", passenger.lastName);
      setValue("[data-passenger-first-name]", passenger.firstName);
      setValue("[data-passenger-doc-type]", passenger.docType);
      setValue("[data-passenger-doc-no]", passenger.docNo);
      setValue("[data-passenger-doc-issued]", passenger.docIssued);
      setValue("[data-passenger-doc-expiry]", passenger.docExpiry);
      setValue("[data-passenger-birth]", passenger.birth);
      setValue("[data-passenger-gender]", passenger.gender);
      setValue("[data-passenger-nationality]", passenger.nationality);
    });
  };

  function collectPassengers() {
    return [...passengerForm.querySelectorAll("[data-passenger-card]")].map((card) => ({
      lastName: card.querySelector("[data-passenger-last-name]")?.value.trim() || "",
      firstName: card.querySelector("[data-passenger-first-name]")?.value.trim() || "",
      docType: card.querySelector("[data-passenger-doc-type]")?.value || "",
      docNo: card.querySelector("[data-passenger-doc-no]")?.value.trim() || "",
      docIssued: card.querySelector("[data-passenger-doc-issued]")?.value || "",
      docExpiry: card.querySelector("[data-passenger-doc-expiry]")?.value || "",
      birth: card.querySelector("[data-passenger-birth]")?.value || "",
      gender: card.querySelector("[data-passenger-gender]")?.value || "",
      nationality: card.querySelector("[data-passenger-nationality]")?.value || "",
    }));
  }

  const passengerSummary = (passengers) => passengers
    .map((passenger, index) => `乘客 ${index + 1}：${htmlEscape(passenger.lastName)} ${htmlEscape(passenger.firstName)} / ${htmlEscape(passenger.docNo)} / 签发 ${htmlEscape(passenger.docIssued)} / 到期 ${htmlEscape(passenger.docExpiry)} / ${htmlEscape(passenger.birth)} / ${htmlEscape(passenger.nationality)}`)
    .join("<br>");

  const createOrderPreview = async () => {
    const missing = [];
    if (!fromInput.value.trim()) missing.push("出发城市 / 车站");
    if (!toInput.value.trim()) missing.push("到达城市 / 车站");
    if (!dateInput.value) missing.push("出发日期");
    if (!contactWechatInput.value.trim()) missing.push("微信号");
    if (!contactPhoneInput.value.trim()) missing.push("手机号");
    if (!contactEmailInput.value.trim()) missing.push("邮箱");
    if (!selectedOffer) missing.push("车次和座席");
    const passengers = collectPassengers();
    passengers.forEach((passenger, index) => {
      if (!passenger.lastName || !passenger.firstName || !passenger.docNo || !passenger.docIssued || !passenger.docExpiry || !passenger.birth || !passenger.nationality) {
        missing.push(`乘客 ${index + 1} 信息`);
      }
    });

    if (missing.length) {
      result.classList.remove("is-ok");
      result.classList.add("is-warn");
      result.innerHTML = `请先补全：<strong>${missing.map(htmlEscape).join("、")}</strong>。`;
      return;
    }

    const ticketTotal = Number(ticketTotalInput.value || selectedOffer.total || 0);
    const exchangeRate = Number(exchangeRateInput.value || selectedOffer.rate || 0);
    if (!Number.isFinite(ticketTotal) || ticketTotal <= 0 || !Number.isFinite(exchangeRate) || exchangeRate <= 0) {
      result.classList.remove("is-ok");
      result.classList.add("is-warn");
      result.innerHTML = "所选车次金额暂时无效，请重新查询座席。";
      return;
    }
    if (paymentStep) paymentStep.classList.add("is-hidden");

    createButton.disabled = true;
    result.classList.remove("is-ok", "is-warn");
    result.innerHTML = "正在生成订单预览...";

    let order;
    try {
      const response = await fetch(`${getTrainApiBase()}/api/train-orders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          from_station: fromInput.value,
          to_station: toInput.value,
          train_country: getDepartureCountry(),
          arrival_country: getArrivalCountry(),
          depart_date: dateInput.value,
          passengers: passengers.length,
          seat_preference: selectedOffer.seat,
          selected_train: {
            train_no: selectedOffer.trainNo,
            depart_time: selectedOffer.departTime,
            arrive_time: selectedOffer.arriveTime,
            duration: selectedOffer.duration,
            seat: selectedOffer.seat,
            seat_detail: selectedOffer.seatDetail,
            selected_seats: selectedOffer.seatDetail,
            seat_options: selectedOffer.seatOptions,
            left: selectedOffer.left,
            live_synced: selectedOffer.liveSynced,
            synced_at: selectedOffer.syncedAt,
          },
          passenger_details: passengers,
          contact_wechat: contactWechatInput.value.trim(),
          contact_phone: contactPhoneInput.value.trim(),
          contact_email: contactEmailInput.value.trim(),
          ticket_currency: ticketCurrencyInput.value,
          ticket_total_local: ticketTotal,
          exchange_rate: exchangeRate,
        }),
      });
      if (!response.ok) throw new Error("order preview unavailable");
      order = await response.json();
    } catch (error) {
      result.classList.remove("is-ok");
      result.classList.add("is-warn");
      result.innerHTML = "暂时不能生成订单预览，请稍后重试或重新查询座席。";
      createButton.disabled = false;
      return;
    }

    result.classList.remove("is-warn");
    result.classList.add("is-ok");
    const expiresAt = order.expires_at ? formatDateTime(new Date(order.expires_at)) : "以服务端返回为准";
    const paymentQr = order.payment_qr ? `<br><img class="payment-qr" src="${htmlEscape(order.payment_qr)}" alt="支付宝收款码">` : "";
    result.innerHTML = [
      `订单号：<strong>${htmlEscape(order.order_id || "")}</strong>`,
      `应付金额：<strong>${htmlEscape(Number(order.payable_amount || 0).toFixed(2))} 元</strong>`,
      `订单有效期：<strong>20 分钟，至 ${htmlEscape(expiresAt)}</strong>`,
      `收款码：<strong>正式服务端返回当前可用收款码</strong>${paymentQr}`,
      `所选车次：${htmlEscape(selectedOffer.trainNo)} · ${htmlEscape(selectedOffer.seat)} · ${htmlEscape(selectedOffer.seatDetail)} · 开车 ${htmlEscape(selectedOffer.departTime)} · 到达 ${htmlEscape(selectedOffer.arriveTime)} · 运行 ${htmlEscape(selectedOffer.duration)}`,
      `路线：${htmlEscape(fromInput.value)} → ${htmlEscape(toInput.value)}，${htmlEscape(dateInput.value)}，${htmlEscape(passengersInput.value)} 人，${htmlEscape(seatInput.value)}`,
      "语言转换：中文站名、证件类型和国籍会在服务端转换为订票流程需要的标准格式；乘客姓名请按护照英文填写。",
      passengerSummary(passengers),
      `联系人：微信 ${htmlEscape(contactWechatInput.value)}；手机 ${htmlEscape(contactPhoneInput.value)}；邮箱 ${htmlEscape(contactEmailInput.value)}`,
      `<button class="button primary" type="button" data-train-confirm-preview>确认无误，进入付款</button>`
    ].join("<br>");
  };

  passengersInput.addEventListener("input", renderPassengerForms);
  passengersInput.addEventListener("change", renderPassengerForms);
  countryInput?.addEventListener("change", () => {
    renderStationOptions(fromInput, stationOptions[countryInput.value] || [], "请选择出发城市 / 车站");
  });
  arrivalCountryInput?.addEventListener("change", () => {
    renderStationOptions(toInput, allStationOptions, "请选择到达城市 / 车站");
  });
  fromInput.addEventListener("change", syncDepartureCountryFromStation);
  toInput.addEventListener("change", syncArrivalCountryFromStation);
  [countryInput, arrivalCountryInput, fromInput, toInput, dateInput, passengersInput, seatInput].filter(Boolean).forEach((field) => {
    field.addEventListener("change", () => {
      resetSelectedOffer();
      availabilityList.innerHTML = "路线、日期或人数已变化，请重新查询可选座席。";
      result.classList.remove("is-ok", "is-warn");
      result.textContent = "选择车次和座席后，再生成订单预览。";
    });
  });
  searchOffersButton.addEventListener("click", queryOffers);
  availabilityList.addEventListener("click", (event) => {
    const target = event.target;
    if (!target || !target.matches("[data-train-select-offer]")) return;
    const offer = currentOffers[Number(target.getAttribute("data-train-select-offer"))];
    if (!offer) return;
    selectedOffer = offer;
    ticketCurrencyInput.value = offer.currency;
    ticketTotalInput.value = String(offer.total);
    exchangeRateInput.value = String(offer.rate);
    createButton.disabled = false;
    [...availabilityList.querySelectorAll("[data-train-select-offer]")].forEach((button) => {
      button.textContent = "选择";
      button.disabled = false;
    });
    target.textContent = "已选择";
    target.disabled = true;
  });
  createButton.addEventListener("click", createOrderPreview);
  result.addEventListener("click", (event) => {
    const target = event.target;
    if (!target || !target.matches("[data-train-confirm-preview]")) return;
    if (paymentStep) paymentStep.classList.remove("is-hidden");
    target.disabled = true;
    target.textContent = "已确认，继续填写付款资料";
    result.insertAdjacentHTML("beforeend", "<br>已确认订单信息，请继续填写付款资料。");
  });
  renderStationSelects();
  renderPassengerForms();
}

if (visaCalculator) {
  const countryInput = visaCalculator.querySelector("[data-visa-country]");
  const arrivalInput = visaCalculator.querySelector("[data-visa-arrival]");
  const daysInput = visaCalculator.querySelector("[data-visa-days]");
  const departureInput = visaCalculator.querySelector("[data-visa-departure]");
  const modeInput = visaCalculator.querySelector("[data-visa-mode]");
  const result = visaCalculator.querySelector("[data-visa-result]");
  const ruleNote = visaCalculator.querySelector("[data-visa-rule-note]");
  const historyWrap = visaCalculator.querySelector("[data-visa-history-wrap]");
  const historyInput = visaCalculator.querySelector("[data-visa-history]");
  const dayMs = 24 * 60 * 60 * 1000;
  const visaPresets = [
    { name: "乌兹别克斯坦", days: 30, note: "单次 30 天，180 天内累计最多 90 天" },
    { name: "阿尔巴尼亚", days: 90 },
    { name: "安哥拉", days: 30, note: "单次 30 天，每年累计最多 90 天" },
    { name: "安提瓜和巴布达", days: 30, note: "单次 30 天，180 天内累计最多 90 天" },
    { name: "亚美尼亚", days: 90 },
    { name: "阿塞拜疆", days: 30 },
    { name: "巴哈马", days: 90 },
    { name: "巴巴多斯", days: 30 },
    { name: "白俄罗斯", days: 30 },
    { name: "贝宁", days: 30 },
    { name: "波黑", days: 90 },
    { name: "巴西", days: 30, note: "单次 30 天，每 12 个月累计最多 30 天；临时免签口径" },
    { name: "英属维尔京群岛", days: 180 },
    { name: "文莱", days: 14 },
    { name: "柬埔寨", days: 14, note: "临时免签口径" },
    { name: "库克群岛", days: 31 },
    { name: "古巴", days: 90 },
    { name: "多米尼克", days: 30 },
    { name: "斐济", days: 120 },
    { name: "格鲁吉亚", days: 30, note: "单次 30 天，180 天内累计最多 90 天" },
    { name: "格林纳达", days: 30 },
    { name: "海地", days: 90 },
    { name: "伊朗", days: 21 },
    { name: "牙买加", days: 30 },
    { name: "哈萨克斯坦", days: 30 },
    { name: "肯尼亚", days: 90, note: "通常仍需按当地要求完成电子旅行授权" },
    { name: "基里巴斯", days: 30, note: "单次 30 天，每 12 个月累计最多 90 天" },
    { name: "马来西亚", days: 30, note: "单次 30 天，180 天内累计最多 90 天" },
    { name: "马尔代夫", days: 30 },
    { name: "毛里求斯", days: 90 },
    { name: "密克罗尼西亚", days: 30 },
    { name: "摩洛哥", days: 90 },
    { name: "莫桑比克", days: 30 },
    { name: "纽埃", days: 30 },
    { name: "阿曼", days: 14 },
    { name: "北马里亚纳群岛", days: 14 },
    { name: "菲律宾", days: 14, note: "临时免签口径" },
    { name: "皮特凯恩群岛", days: 14 },
    { name: "卡塔尔", days: 30 },
    { name: "俄罗斯", days: 30, note: "临时免签口径" },
    { name: "萨摩亚", days: 30, note: "单次 30 天，180 天内累计最多 90 天" },
    { name: "圣马力诺", days: 90 },
    { name: "塞尔维亚", days: 30 },
    { name: "塞舌尔", days: 30 },
    { name: "新加坡", days: 30 },
    { name: "所罗门群岛", days: 30, note: "单次 30 天，180 天内累计最多 90 天" },
    { name: "圣基茨和尼维斯", days: 30 },
    { name: "圣卢西亚", days: 42 },
    { name: "苏里南", days: 30 },
    { name: "泰国", days: 60, note: "单次 60 天，180 天内累计最多 90 天" },
    { name: "汤加", days: 30 },
    { name: "突尼斯", days: 90 },
    { name: "土耳其", days: 90 },
    { name: "特克斯和凯科斯群岛", days: 90 },
    { name: "阿联酋", days: 90 },
    { name: "瓦努阿图", days: 120 },
    { name: "越南富国岛", days: 30, note: "仅富国岛口径" },
    { name: "赞比亚", days: 90, note: "旅游每年累计最多 90 天；商务每年累计最多 30 天" },
    { name: "自定义目的地", days: 30, note: "手动填写免签天数" },
  ];
  const rollingRules = new Map([
    ["乌兹别克斯坦", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["阿尔巴尼亚", { windowDays: 180, maxWindowDays: 90 }],
    ["亚美尼亚", { windowDays: 180, maxWindowDays: 90 }],
    ["波黑", { windowDays: 180, maxWindowDays: 90 }],
    ["土耳其", { windowDays: 180, maxWindowDays: 90 }],
    ["阿联酋", { windowDays: 180, maxWindowDays: 90 }],
    ["安哥拉", { windowDays: 365, maxWindowDays: 90, singleDays: 30, period: "calendar-year", label: "单次 30 天，每年累计最多 90 天" }],
    ["安提瓜和巴布达", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["阿塞拜疆", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["巴西", { windowDays: 365, maxWindowDays: 30, singleDays: 30, period: "rolling-365", label: "单次 30 天，每 12 个月累计最多 30 天" }],
    ["白俄罗斯", { windowDays: 365, maxWindowDays: 90, singleDays: 30, period: "calendar-year", label: "单次 30 天，每个自然年累计最多 90 天" }],
    ["格鲁吉亚", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["哈萨克斯坦", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["基里巴斯", { windowDays: 365, maxWindowDays: 90, singleDays: 30, period: "rolling-365", label: "单次 30 天，每 12 个月累计最多 90 天" }],
    ["马来西亚", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["萨摩亚", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["所罗门群岛", { windowDays: 180, maxWindowDays: 90, singleDays: 30 }],
    ["泰国", { windowDays: 180, maxWindowDays: 90, singleDays: 60 }],
    ["赞比亚", { windowDays: 365, maxWindowDays: 90, period: "calendar-year", label: "旅游每年累计最多 90 天；商务每年累计最多 30 天" }],
  ]);

  countryInput.innerHTML = visaPresets
    .map((item) => `<option value="${item.name}" data-days="${item.days}" data-note="${item.note || ""}">${item.name}</option>`)
    .join("");

  const parseDate = (value) => {
    if (!value) return null;
    const parts = value.split("-").map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) return null;
    return new Date(parts[0], parts[1] - 1, parts[2]);
  };

  const formatDate = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  };

  const diffDays = (start, end) => Math.round((end - start) / dayMs);

  const addDays = (date, days) => {
    const next = new Date(date);
    next.setDate(next.getDate() + days);
    return next;
  };

  const maxDate = (a, b) => (a > b ? a : b);
  const minDate = (a, b) => (a < b ? a : b);

  const selectedPreset = () => {
    const preset = visaPresets.find((item) => item.name === countryInput.value) || visaPresets[0];
    const rolling = rollingRules.get(preset.name);
    return rolling ? { ...preset, ...rolling, rule: "rolling" } : { ...preset, rule: "single" };
  };

  const parseHistory = () => {
    const rows = historyInput.value.split(/\n+/).map((line) => line.trim()).filter(Boolean);
    const stays = [];
    for (const row of rows) {
      const dates = row.match(/\d{4}-\d{2}-\d{2}/g) || [];
      if (dates.length < 2) continue;
      const start = parseDate(dates[0]);
      const end = parseDate(dates[1]);
      if (!start || !end) continue;
      stays.push({ start: minDate(start, end), end: maxDate(start, end) });
    }
    return stays;
  };

  const latestStay = (stays) => stays.reduce((latest, stay) => {
    if (!latest || stay.end > latest.end) return stay;
    return latest;
  }, null);

  const daysBetweenInclusive = (start, end) => {
    if (end < start) return 0;
    return diffDays(start, end) + 1;
  };

  const usedDaysInWindow = (windowEnd, rule, stays) => {
    const windowStart = rule.period === "calendar-year"
      ? new Date(windowEnd.getFullYear(), 0, 1)
      : addDays(windowEnd, -(rule.windowDays - 1));
    return stays.reduce((total, stay) => {
      const start = maxDate(stay.start, windowStart);
      const end = minDate(stay.end, windowEnd);
      return total + daysBetweenInclusive(start, end);
    }, 0);
  };

  const nextAvailableDate = (startDate, rule, stays) => {
    for (let offset = 0; offset <= rule.windowDays + 365; offset += 1) {
      const date = addDays(startDate, offset);
      if (rule.maxWindowDays - usedDaysInWindow(date, rule, stays) > 0) {
        return date;
      }
    }
    return null;
  };

  const updateVisaResult = () => {
    const arrival = parseDate(arrivalInput.value);
    const departure = parseDate(departureInput.value);
    const allowedDays = Number(daysInput.value || 30);
    const mode = modeInput.value;
    const country = selectedPreset();
    result.classList.remove("is-ok", "is-warn");
    const ruleLabel = country.rule === "rolling"
      ? country.label || `${country.windowDays} 天内累计最多 ${country.maxWindowDays} 天${country.singleDays ? `，单次最多 ${country.singleDays} 天` : ""}`
      : `单次最多 ${allowedDays} 天`;
    ruleNote.innerHTML = `当前规则：<strong>${ruleLabel}</strong>`;
    historyWrap.classList.remove("is-hidden");
    if (country.rule === "rolling" && allowedDays > country.maxWindowDays) {
      daysInput.value = String(country.singleDays || country.maxWindowDays);
    }
    const stays = parseHistory();
    const lastTrip = latestStay(stays);
    const nextCandidate = lastTrip ? addDays(lastTrip.end, 1) : arrival;

    if (!arrival || !allowedDays || allowedDays < 1) {
      result.textContent = "选择入境日期后，会自动计算最晚离境日期。";
      return;
    }

    if (country.rule === "rolling") {
      const basisDate = nextCandidate || arrival;
      const usedBeforeBasis = usedDaysInWindow(addDays(basisDate, -1), country, stays);
      const availableAtBasis = Math.max(0, country.maxWindowDays - usedBeforeBasis);
      const nextDate = nextAvailableDate(basisDate, country, stays);
      const availableDate = nextDate || basisDate;
      const usedBeforeAvailableDate = usedDaysInWindow(addDays(availableDate, -1), country, stays);
      const availableAtAvailableDate = Math.max(0, country.maxWindowDays - usedBeforeAvailableDate);
      const singleLimit = country.singleDays || country.maxWindowDays;
      const usableDays = Math.min(singleLimit, availableAtAvailableDate);
      const rollingLastDate = usableDays > 0 ? addDays(availableDate, usableDays - 1) : null;
      const periodText = country.period === "calendar-year"
        ? `${formatDate(basisDate)} 所在自然年内`
        : `${formatDate(basisDate)} 前 ${country.windowDays} 天内`;
      const referencePeriodText = country.period === "calendar-year"
        ? `参考入境日所在自然年内`
        : `参考入境日前 ${country.windowDays} 天内`;
      const parts = [
        `${country.name} 当前按 <strong>${ruleLabel}</strong> 计算。`,
      ];
      if (lastTrip) {
        parts.push(`已按最后一次出境日期 <strong>${formatDate(lastTrip.end)}</strong> 推算，系统从 <strong>${formatDate(basisDate)}</strong> 开始寻找下一次可免签入境日期。`);
        parts.push(`${periodText}，已记录使用 <strong>${usedBeforeBasis}</strong> 天；当天可用额度为 <strong>${availableAtBasis}</strong> 天。`);
      } else {
        parts.push(`未填写已完成出入境记录，先按参考入境日期 <strong>${formatDate(arrival)}</strong> 计算。`);
        parts.push(`${referencePeriodText}，已记录使用 <strong>${usedBeforeBasis}</strong> 天；当天可用额度为 <strong>${availableAtBasis}</strong> 天。`);
      }

      if (nextDate && rollingLastDate) {
        result.classList.add("is-ok");
        parts.push(`下一次可免签入境日期为 <strong>${formatDate(nextDate)}</strong>，从这天入境预计可停留 <strong>${usableDays}</strong> 天，最晚离境日期为 <strong>${formatDate(rollingLastDate)}</strong>。`);
      } else {
        result.classList.add("is-warn");
        parts.push("当前记录下暂未算出下一次可免签入境日期，请检查出入境记录。");
      }

      if (departure && rollingLastDate) {
        const plannedDays = daysBetweenInclusive(availableDate, departure);
        if (departure <= rollingLastDate) {
          result.classList.add("is-ok");
          parts.push(`参考离境日期在范围内，预计本次使用 <strong>${plannedDays}</strong> 天。`);
        } else {
          result.classList.add("is-warn");
          parts.push(`参考离境日期超出当前可用额度，预计本次使用 <strong>${plannedDays}</strong> 天。`);
        }
      }

      if (country.note) {
        parts.push(country.note);
      }
      result.innerHTML = parts.join("<br>");
      return;
    }

    const offset = mode === "next-day" ? allowedDays : allowedDays - 1;
    const singleBasisDate = nextCandidate || arrival;
    const lastDate = addDays(singleBasisDate, offset);
    const modeText = mode === "next-day" ? "入境次日算第 1 天" : "入境日算第 1 天";
    const parts = [
      `${country.name} 当前按 <strong>${ruleLabel}</strong>、${modeText} 计算。`,
    ];
    if (lastTrip) {
      result.classList.add("is-ok");
      parts.push(`已按最后一次出境日期 <strong>${formatDate(lastTrip.end)}</strong> 推算，下一次可免签入境参考日期为 <strong>${formatDate(singleBasisDate)}</strong>。`);
      parts.push(`从这天入境，最晚离境日期为 <strong>${formatDate(lastDate)}</strong>。`);
    } else {
      parts.push(`未填写已完成出入境记录，先按参考入境日期 <strong>${formatDate(arrival)}</strong> 计算，最晚离境日期为 <strong>${formatDate(lastDate)}</strong>。`);
    }
    parts.push(`建议按更保守的日期安排机票和住宿。`);
    if (country.note) {
      parts.push(country.note);
    }

    if (departure) {
      const usedDays = mode === "next-day" ? Math.max(0, diffDays(singleBasisDate, departure)) : diffDays(singleBasisDate, departure) + 1;
      const remainingDays = diffDays(departure, lastDate);
      if (departure <= lastDate) {
        result.classList.add("is-ok");
        parts.push(`参考离境日期在范围内，预计停留 <strong>${usedDays}</strong> 天，距离最晚离境日还有 <strong>${remainingDays}</strong> 天。`);
      } else {
        result.classList.add("is-warn");
        parts.push(`参考离境日期超出范围，预计停留 <strong>${usedDays}</strong> 天，需要提前调整行程或确认签证方案。`);
      }
    }

    result.innerHTML = parts.join("<br>");
  };

  countryInput.value = "乌兹别克斯坦";
  countryInput.addEventListener("change", () => {
    const country = selectedPreset();
    daysInput.value = String(country.singleDays || country.days);
    updateVisaResult();
  });
  const today = new Date();
  arrivalInput.value = formatDate(today);
  [arrivalInput, daysInput, departureInput, modeInput, historyInput].forEach((field) => {
    field.addEventListener("input", updateVisaResult);
    field.addEventListener("change", updateVisaResult);
  });
  updateVisaResult();
}
"""
    (SITE_DIR / "assets" / "styles.css").write_text(styles.strip() + "\n", encoding="utf-8")
    (SITE_DIR / "assets" / "site.js").write_text(script.strip() + "\n", encoding="utf-8")


def write_readme() -> None:
    readme = """# 网站维护说明

这个目录是一个自包含静态网站，可直接部署到 Cloudflare Pages、GitHub Pages、Netlify 等免费静态托管平台。推荐 Cloudflare Pages，因为可以免费获得 `项目名.pages.dev` 网址，后续也方便绑定独立域名。

## 当前结构

- `index.html`：首页
- `countries/*/index.html`：国家页
- `countries/*/topics/*/index.html`：专题详情页
- `countries/*/dining/index.html`：探店索引页
- `operate/index.html`：维护工作台
- `assets/`：样式和前端脚本
- `content/countries/*/topics/*.md`：专题 Markdown 原文
- `tools/site.config.json`：国家和专题配置

## 后续新增国家

1. 在 `content/countries/` 下新建国家目录，例如 `kazakhstan`。
2. 在新国家目录下建立 `topics/`，放入专题 Markdown，例如 `transport.md`。
3. 在 `tools/site.config.json` 增加国家和专题配置。
4. 运行 `python3 work/build_notes_site.py` 重新生成页面。

## 探店资料

当前探店页由两类资料合并生成：

- 历史已确认明细：`/Users/g90/xiaohongshu_tandian_recovered/tandian_only/坐标位置_已确认明细_当前.csv`
- 本轮整理总表：`outputs/GoogleMaps_110条_整理标注总表.csv`

页面统计口径为：已确认详细坐标 80 条，仍无最终详细坐标但有名字待继续核验 94 条。表里的地图查询、原帖链接、作者主页会在页面中自动变成可点击链接。

## 免费部署建议

推荐 Cloudflare Pages：

- 构建命令：留空
- 输出目录：项目根目录
- 免费网址：`项目名.pages.dev`

如果以后购买独立域名，可以在 Cloudflare Pages 后台绑定，不需要改网站代码。

## 火车票工具服务端

火车票工具需要单独部署 API 服务，静态站通过 `tools/runtime-config.js` 指向 API 地址：

```js
window.QUIET_ATLAS_API_BASE = "https://你的-api-地址";
```

服务端部署文件在源码目录的 `work/server_deploy/`，包含：

- `train_ticket_assisted_server.py`：FastAPI 服务
- `requirements.txt`：Python 依赖
- `train-ticket.env.example`：环境变量模板
- `quiet-atlas-train.service`：systemd 服务
- `DEPLOY.md`：部署步骤

车次、座位、余票和价格必须由服务端实时同步返回；同步不到时，前端不会展示旧车次，也不能进入订单流程。
"""
    (SITE_DIR / "README_维护说明.md").write_text(readme, encoding="utf-8")


def write_support_files() -> None:
    (SITE_DIR / "tools" / "runtime-config.js").write_text(
        """window.QUIET_ATLAS_API_BASE = window.QUIET_ATLAS_API_BASE || "";
""",
        encoding="utf-8",
    )
    public_server_script = SITE_DIR / "tools" / "train_ticket_assisted_server.py"
    if public_server_script.exists():
        public_server_script.unlink()
    (SITE_DIR / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (SITE_DIR / "404.html").write_text(
        """<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>页面不存在 - 长日记事</title>
    <link rel="stylesheet" href="/assets/styles.css">
  </head>
  <body>
    <main>
      <section class="country-hero">
        <p class="eyebrow">404</p>
        <h1>页面不存在</h1>
        <p class="lead">这个地址暂时没有内容。可以返回首页查看国家资料库和已完成专题。</p>
        <div class="hero-actions"><a class="button primary" href="/">返回首页</a></div>
      </section>
    </main>
  </body>
</html>
""",
        encoding="utf-8",
    )


def write_pages(
    config: dict[str, Any],
    countries: list[Country],
    topics: list[Topic],
    dining_places: list[DiningPlace],
    other_reviews: list[OtherAuthorReview],
) -> None:
    topics_by_slug = {topic.slug: topic for topic in topics}
    country_lookup = {country.slug: country for country in countries}
    (SITE_DIR / "index.html").write_text(
        render_home(config, countries, topics, dining_places),
        encoding="utf-8",
    )
    (SITE_DIR / "operate" / "index.html").write_text(
        render_operate_page(config, countries, topics, dining_places),
        encoding="utf-8",
    )
    (SITE_DIR / "dining" / "index.html").write_text(
        render_dining_index_page(config, countries, dining_places),
        encoding="utf-8",
    )
    for country in countries:
        if country.status != "online":
            continue
        country_dir = SITE_DIR / "countries" / country.slug
        country_dir.mkdir(parents=True, exist_ok=True)
        (country_dir / "index.html").write_text(
            render_country_page(config, country, topics_by_slug, dining_places),
            encoding="utf-8",
        )
        dining_dir = country_dir / "dining"
        dining_dir.mkdir(parents=True, exist_ok=True)
        (dining_dir / "index.html").write_text(
            render_dining_page(config, country, dining_places, other_reviews),
            encoding="utf-8",
        )
    for topic in topics:
        topic_dir = SITE_DIR / "countries" / topic.country_slug / "topics" / topic.slug
        topic_dir.mkdir(parents=True, exist_ok=True)
        (topic_dir / "index.html").write_text(
            render_topic_page(config, topic, country_lookup),
            encoding="utf-8",
        )
        if topic.slug == "local-tools":
            for tool_slug in ["visa-calculator", "sim-comparison", "train-tickets"]:
                tool_dir = topic_dir / tool_slug
                tool_dir.mkdir(parents=True, exist_ok=True)
                (tool_dir / "index.html").write_text(
                    render_local_tool_detail_page(config, topic, country_lookup, tool_slug),
                    encoding="utf-8",
                )


def main() -> None:
    ensure_seed_files()
    config, countries, topics = load_site_data()
    dining_places = load_dining_places()
    other_reviews = load_other_author_reviews()
    dining_places = merge_other_author_reviews_into_places(dining_places, other_reviews)
    dining_places = filter_dropped_dining_places(dining_places)
    clean_generated_files()
    write_assets()
    write_readme()
    write_support_files()
    write_pages(config, countries, topics, dining_places, other_reviews)
    print(SITE_DIR)


if __name__ == "__main__":
    main()
