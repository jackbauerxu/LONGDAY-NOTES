import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
UPSTREAM = Path("/Users/g90/xiaohongshu_tandian_recovered/tandian_only")

MAP_110 = OUT / "仍需地图查询_110条_GoogleMaps查询表_补充读取后.csv"
NEED_110 = OUT / "仍需地图查询_有可用餐厅名_按新规则.csv"
XHS_DETAIL = UPSTREAM / "xhs_google_yandex_83" / "xhs_unconfirmed83_google_yandex_final.csv"
XHS_ALL = UPSTREAM / "小红书探店信息_带位置和原帖链接_补原帖链接.csv"

PENDING_REMARK = "未在地图上获取有效位置坐标，用户搜索时，需要自行确认"


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact(value):
    return " ".join((value or "").replace("\n", " ").split())


def get(row, *keys):
    for key in keys:
        if key in row and row[key]:
            return row[key]
    return ""


def classify(row):
    text = " ".join([
        row.get("标题/名称", ""),
        row.get("提取餐厅/地点名", ""),
        row.get("Google候选名", ""),
        row.get("Google候选详情", ""),
        row.get("Google查询词", ""),
    ]).lower()

    chinese_tokens = [
        "中餐", "中国", "chinese", "湘", "川", "重庆", "火锅", "麻辣", "拉面",
        "面馆", "小面", "饭店", "食府", "小厨", "私厨", "烧烤", "串串", "新疆",
        "兰州", "沙县", "饺子", "包子", "牛肉汤", "江湖菜", "江南", "华人",
        "清真餐厅", "大盘鸡", "湘菜", "川菜", "粤", "广式", "福建", "温州",
        "长沙", "唐朝", "东方红", "长安", "china", "xibei", "uygur",
        "dungan", "malatang", "huoguo", "友谊餐厅", "百味餐厅", "湘疆缘",
        "唐朝饭店", "沈阳饺子馆", "中国饭店", "川湘食府", "来福餐厅",
        "小馆", "小碗菜", "乌鲁木齐餐厅",
    ]
    cafe_tokens = [
        "咖啡", "coffee", "cafe", "café", "bakery", "brunch", "甜品", "蛋糕",
        "奶茶", "tea", "bubble tea", "hero tea", "matcha", "beanberry",
        "cocochou", "boost", "good food bakery",
    ]
    local_tokens = [
        "乌兹民族", "乌兹庭院", "乌兹别克风味", "本地菜", "plov", "抓饭", "lagman", "jigarim", "shesh besh", "lali",
        "jumanji", "besh qozon", "khan chapan", "jiz-biz", "bog'i zilol",
        "samarkand", "pilaf",
    ]
    western_tokens = [
        "西餐", "意大利", "法餐", "希腊", "披萨", "pizza", "steak", "牛排",
        "sorrento", "paul", "nika", "syrovarnya", "borjomi", "european",
        "french", "italian", "georgian", "brasserie",
    ]

    if any(token in text for token in chinese_tokens):
        return "中餐"
    if any(token in text for token in cafe_tokens):
        return "咖啡厅"
    if any(token in text for token in local_tokens):
        return "乌兹别克斯坦本地菜"
    if any(token in text for token in western_tokens):
        return "西餐"
    return "其他"


def load_xhs_meta():
    meta = {}
    for path in [XHS_ALL, XHS_DETAIL, NEED_110]:
        if not path.exists():
            continue
        for row in read_csv(path):
            seq = get(row, "序号", "序号/名称")
            if not seq:
                continue
            current = meta.setdefault(seq, {})
            current["原帖链接"] = current.get("原帖链接") or get(row, "小红书原帖链接", "原帖链接_输出", "原帖链接")
            current["作者小红书号"] = current.get("作者小红书号") or get(row, "作者小红书号", "作者小红书号_输出", "作者账号ID_输出")
            current["账号名字"] = current.get("账号名字") or get(row, "作者昵称_用户名_输出", "作者昵称_输出")
            current["作者主页链接"] = current.get("作者主页链接") or get(row, "作者主页链接_输出")
            current["地址线索"] = current.get("地址线索") or get(row, "地址线索", "提取地址")
            current["原帖证据"] = current.get("原帖证据") or get(row, "原帖证据_输出")
    return meta


def is_confirmed(row):
    return "已确认" in row.get("Google搜索状态", "")


def make_row(row, xhs_meta):
    seq = row["序号/名称"]
    meta = xhs_meta.get(seq, {}) if row["来源"] == "小红书" else {}
    confirmed = is_confirmed(row)
    status = "已确认详细坐标" if confirmed else "待用户自行确认"
    lat = row.get("Google纬度", "") if confirmed else ""
    lng = row.get("Google经度", "") if confirmed else ""
    remark = row.get("备注", "")
    if not confirmed:
        remark = PENDING_REMARK

    account_name = meta.get("账号名字") or ""
    if row["来源"] == "小红书" and not account_name:
        account_name = "未提取到"

    return {
        "来源": row["来源"],
        "序号/名称": seq,
        "标题/名称": row["标题/名称"],
        "提取餐厅/地点名": row["提取餐厅/地点名"],
        "餐饮标签": classify(row),
        "整理状态": status,
        "Google搜索状态": row.get("Google搜索状态", ""),
        "最终纬度": lat,
        "最终经度": lng,
        "Google候选名": row.get("Google候选名", ""),
        "Google候选详情/地址": compact(row.get("Google候选详情", "")),
        "备注": remark,
        "Google Maps查询URL": row.get("Google Maps查询URL", ""),
        "Google页面文件": row.get("Google页面文件", ""),
        "作者小红书号": meta.get("作者小红书号", "") if row["来源"] == "小红书" else "",
        "账号名字": account_name if row["来源"] == "小红书" else "",
        "作者主页链接": meta.get("作者主页链接", "") if row["来源"] == "小红书" else "",
        "原帖链接": meta.get("原帖链接", "") if row["来源"] == "小红书" else "",
        "地址线索": meta.get("地址线索", "") if row["来源"] == "小红书" else "",
        "原帖证据": meta.get("原帖证据", "") if row["来源"] == "小红书" else "",
    }


def main():
    rows = read_csv(MAP_110)
    xhs_meta = load_xhs_meta()
    labeled = [make_row(row, xhs_meta) for row in rows]
    pending = [row for row in labeled if row["整理状态"] == "待用户自行确认"]

    fields = [
        "来源", "序号/名称", "标题/名称", "提取餐厅/地点名", "餐饮标签",
        "整理状态", "Google搜索状态", "最终纬度", "最终经度", "Google候选名",
        "Google候选详情/地址", "备注", "Google Maps查询URL", "Google页面文件",
        "作者小红书号", "账号名字", "作者主页链接", "原帖链接", "地址线索", "原帖证据",
    ]
    write_csv(OUT / "GoogleMaps_110条_整理标注总表.csv", labeled, fields)
    write_csv(OUT / "待用户自行确认_94条_已标注.csv", pending, fields)

    stats = []
    stats.append(f"110条地图查询池总数：{len(labeled)}")
    stats.append(f"已确认详细坐标：{sum(1 for r in labeled if r['整理状态'] == '已确认详细坐标')}")
    stats.append(f"待用户自行确认：{len(pending)}")
    stats.append("")
    stats.append("全部110条标签统计：")
    for key, count in Counter(r["餐饮标签"] for r in labeled).most_common():
        stats.append(f"{key}：{count}")
    stats.append("")
    stats.append("待用户自行确认94条标签统计：")
    for key, count in Counter(r["餐饮标签"] for r in pending).most_common():
        stats.append(f"{key}：{count}")
    stats.append("")
    stats.append("小红书信息完整性：")
    xhs_rows = [r for r in labeled if r["来源"] == "小红书"]
    stats.append(f"小红书行数：{len(xhs_rows)}")
    stats.append(f"有作者小红书号：{sum(1 for r in xhs_rows if r['作者小红书号'])}")
    stats.append(f"有原帖链接：{sum(1 for r in xhs_rows if r['原帖链接'])}")
    stats.append(f"账号名字未提取到：{sum(1 for r in xhs_rows if r['账号名字'] == '未提取到')}")
    (OUT / "整理标注_统计_20260613.txt").write_text("\n".join(stats) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
