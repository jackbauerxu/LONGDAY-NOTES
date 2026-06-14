import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
SOURCE = OUT / "仍需地图查询_110条_GoogleMaps查询表.csv"


LIVE_RESULTS = {
    52: ("湘聚缘", "高档餐饮·Tashkent, Temiryulchilar Str. 38", "41.2836215", "69.2796498", "Google Maps已确认", "同名结果；地址和坐标来自 Google Maps 读取页。"),
    53: ("Kungfu Malatang", "餐馆·Ulitsa Istiklol 7", "41.3132606", "69.2834973", "Google候选需核名", "候选与“漫漫重庆大碗麻辣烫”不是同名，只能作为近似麻辣烫候选。"),
    54: ("兰州拉面", "中国风味·78M3+5WC, Фарғона Йўли", "41.2829348", "69.3047555", "Google候选需核名", "候选缺少 yusuf 字样，需核名。"),
    55: ("", "", "", "", "Google无同名结果", "未返回“淮扬食府中餐厅”同名或高度相关候选。"),
    56: ("", "", "", "", "Google无有效结果", "页面未返回可用地点卡片。"),
    57: ("重庆搞火锅Чунцинский самовар", "中国风味·DOMDRABAD KO'CHASI", "41.2568108", "69.2043659", "Google候选需核名", "另有 JIANG HU HUOGUO 煮江湖火锅；与“锅气火锅”不完全同名。"),
    58: ("", "", "", "", "Google无同名结果", "返回多条泛化餐厅/火锅结果，未见“锅气小碗菜”同名候选。"),
    59: ("", "", "", "", "Google无同名结果", "返回泛化餐厅列表，未见“幸福小馆”同名候选。"),
    60: ("Xitoyning Chongqing Hotpoti", "火锅·Arnasay ko'chasi 23", "41.2752546", "69.2245032", "Google候选需核名", "候选与“重庆辣德佳火锅”不是同名，只能作为重庆火锅近似候选。"),
    61: ("浙江海鲜楼", "中国风味·Arnasay Street, 斯坦", "41.2799293", "69.2267713", "Google候选需核名", "与“闽浙海鲜餐厅”接近但不是同名。"),
    62: ("遇湘食府", "UZ Imam at-Termeziy ko'chasi 8, Тоshkent, Toshkent, 乌兹别克斯坦", "41.2831119", "69.2452873", "Google Maps已确认", "同名详情页；地址和坐标来自 Google Maps 读取页。"),
    63: ("", "", "", "", "Google无同名结果", "未返回“樽龍私厨”同名或高度相关候选。"),
    64: ("saray uygur taomliri", "中欧餐厅·furqat 15a", "41.3096237", "69.2430459", "Google候选需核名", "Saray+Uyghur 语义接近新疆餐厅，但不是中文同名。"),
    65: ("", "", "", "", "Google无同名结果", "返回泛化餐厅/火锅结果，未见“一站式火锅外卖”同名候选。"),
    66: ("Sakura BBQ", "烧烤·Abdulla Kaxxar ko'chasi 48а", "41.2753514", "69.2633190", "Google Maps已确认", "Sakura 与樱花、BBQ 与烤肉对应，名称高度匹配。"),
    67: ("", "", "", "", "Google无同名结果", "未返回“渝味山庄江湖菜”同名候选。"),
    68: ("China Arena Restaurant", "中国风味；菜单主打餐饮：重庆小面", "41.2863567", "69.2716208", "Google候选需核名", "候选是菜单项匹配，不是店名同名。"),
    69: ("华人餐厅", "中国风味·8728+Q2Q", "41.3019603", "69.2649157", "Google Maps已确认", "同名结果；坐标来自 Google Maps 读取页。"),
    70: ("疆来清真餐厅", "Tashkent, Mahmud Tarobiy ko'chasi, 100047", "41.2863567", "69.2591622", "Google Maps已确认", "同名详情页；地址和坐标来自 Google Maps 读取页。"),
    71: ("中国饭店", "中国风味·77VQ+7PJ", "41.2932131", "69.2892665", "Google Maps已确认", "同名结果；坐标来自 Google Maps 读取页。"),
}

USER_RESULTS = [
    ("Lesnoy", "Istiqbol street, 45", "Lesnoy", "咖啡馆·Istiqbol ko'chasi 45", "41.3031212", "69.2898053", "已确认；更新已有确认坐标", "对应当前已确认表的小红书 seq62 Lesnoy森林；原坐标为 41.3023180,69.2893150。", "work/maps_user_addresses/Lesnoy.md"),
    ("ORA", "Tashkent, Istiqbol street, 41, floor 2", "ORA", "餐馆·ЖК Инфинити, Ташкент, улица Истикбол, этаж 2 41", "41.3022999", "69.2891848", "已确认；未匹配当前总表源记录", "Google Maps 同名结果明确，但当前 228 条总池未检出 ORA 源记录。", "work/maps_user_addresses/ORA.md"),
    ("COCOCHOU BAKERY", "Ташкент, ул. Мирабад, 39", "COCOCHOU BAKERY", "Mirobod ko'chasi 39, 100015, Тоshkent", "41.2928277", "69.2717089", "已确认；匹配当前待查 seq54/seq81", "用户地址与 Google Maps 同名详情页一致。", "work/maps_user_addresses/COCOCHOU_BAKERY.md"),
    ("muza kitchen", "Tashkent, Yashnabad City District, Mahtumquli Street, 45", "Muza Kitchen", "Makhtumkuli 45 / 876M+Q2H, Tashkent", "41.3118078", "69.2826143", "已确认；未匹配当前总表源记录", "Google Maps 同名结果明确，但当前 228 条总池未检出 muza kitchen 源记录。", "work/maps_user_addresses/muza_kitchen.md"),
    ("煮江湖重庆火锅", "Арнасай, 16Б", "JIANG HU HUOGUO 煮江湖火锅", "76HG+GM 塔什干；电话 +998 94 999 57 66", "41.2788045", "69.2266345", "已确认；更新已有确认坐标", "对应当前已确认表的微信“塔什干煮江湖火锅餐厅”；原坐标为 41.3494374,69.2260522。", "work/maps_user_addresses/JIANG_HU_HUOGUO.md"),
    ("湘味小厨", "ул. Кичик Бешагач, 128", "湘味小厨", "Кичик Бешагач161 塔什干市", "41.2799943", "69.2695387", "已确认；未匹配当前总表源记录", "Google Maps 同名结果明确，但门牌显示 161，与用户给的 128 不一致，需保留地址差异备注。", "work/maps_user_addresses/湘味小厨.md"),
    ("Caravan", "112 Abdurahman Jami Street, Tashkent, Uzbekistan", "Restaurant Caravan", "Abdulla Kaxxar ko'chasi 22", "41.2851722", "69.2575792", "地址冲突需核", "Google Maps 返回餐厅地址与用户给的 Abdurahman Jami 112 不一致，不计入确认。", "work/maps_user_addresses/Caravan.md"),
    ("OKO", "152/1, Buyuk Ipak Yuli Road, 100000, Tashkent", "Oko", "152/1, Buyuk Ipak Yuli Road, 100000, Tashkent", "41.3270300", "69.3375740", "已确认；匹配当前待查 seq105", "用户地址与 Google Maps 同名详情页一致。", "work/maps_user_addresses/OKO.md"),
]

USER_OVERLAY = {
    ("小红书", "54"): ("COCOCHOU BAKERY", "Mirobod ko'chasi 39, 100015, Тоshkent", "41.2928277", "69.2717089", "用户补充地址+Google Maps已确认", "用户补充 Cocochou 地址与 Google Maps 同名详情页一致。"),
    ("小红书", "81"): ("COCOCHOU BAKERY", "Mirobod ko'chasi 39, 100015, Тоshkent", "41.2928277", "69.2717089", "用户补充地址+Google Maps已确认", "用户补充 Cocochou 地址与 Google Maps 同名详情页一致。"),
    ("小红书", "105"): ("Oko", "152/1, Buyuk Ipak Yuli Road, 100000, Tashkent", "41.3270300", "69.3375740", "用户补充地址+Google Maps已确认", "用户补充 OKO 地址与 Google Maps 同名详情页一致。"),
}

NEXT_RESULTS = {
    2: ("Jigarim restaurant", "餐馆；Google Maps 详情页", "41.2809066", "69.2928924", "Google Maps已确认", "同名详情页；坐标来自第二批 Google Maps 读取页。"),
    4: ("Plov Museum", "餐馆；Google Maps 详情页", "41.3315216", "69.3124388", "Google Maps已确认", "同名/英文等价详情页；坐标来自第二批 Google Maps 读取页。"),
    5: ("The Host- Indian Restaurant", "Street Oybek 65/4, 100015, Тоshkent", "41.2914696", "69.2827894", "Google Maps已确认", "同名详情页；地址和坐标来自第二批 Google Maps 读取页。"),
    6: ("Lali Restaurant", "餐馆；Google Maps 详情页", "41.3279321", "69.2779741", "Google Maps已确认", "同名详情页；坐标来自第二批 Google Maps 读取页。"),
    23: ("Cafe Dosan", "咖啡店·Tashkent City, Yakub Kolas Street 6", "41.3039384", "69.2704719", "Google Maps已确认", "同名咖啡馆；另有 Dosan 2 显示停业，采用第一条营业候选。"),
    33: ("MISO. RESTAURANT", "68PR+9PJ, Tashkent, Tashkent Region", "41.2359529", "69.3417662", "Google Maps已确认", "同名详情页；坐标来自第二批 Google Maps 读取页。"),
    49: ("Boost Coffee", "76XW+8GP, Tashkent", "", "", "Google有文字候选无坐标", "同名/近名详情页有地址和 Plus Code，但本次页面未给出可换算坐标。"),
    51: ("Hero Tea", "Улица Баходира 69, Тоshkent", "41.2991690", "69.2472376", "Google Maps已确认", "同名详情页；地址和坐标来自第二批 Google Maps 读取页。"),
    83: ("", "", "", "", "Google无有效结果", "页面未返回可用地点卡片。"),
    90: ("长安宴宾楼 | Shuan Hiang Shi Fu", "Sariko'l ko'chasi 2, 100005, Тоshkent", "41.2793276", "69.2852776", "Google候选需核名", "Shuan Hiang Shi Fu 与“川湘食府”疑似音译接近，但中文名不一致，需核名。"),
    98: ("", "", "", "", "Google无同名结果", "返回泛化餐厅列表，未见“来福餐厅”同名候选。"),
    102: ("", "", "", "", "Google无同名结果", "返回中餐/酒店泛化结果，未见“川渝私房菜（东方明珠酒店）”同名候选。"),
    108: ("", "", "", "", "Google无同名结果", "返回 Tashkent 泛化餐厅列表，未见撒马尔罕新疆风味餐厅同名候选。"),
}


def read_source():
    with SOURCE.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = read_source()
    by_idx = {i: row for i, row in enumerate(rows, start=1)}

    live_rows = []
    for idx, result in LIVE_RESULTS.items():
        source = by_idx[idx]
        name, detail, lat, lng, status, note = result
        live_rows.append({
            "原表行号": idx,
            "来源": source["来源"],
            "序号/名称": source["序号/名称"],
            "标题/名称": source["标题/名称"],
            "提取餐厅/地点名": source["提取餐厅/地点名"],
            "Google候选名": name,
            "Google候选详情/地址": detail,
            "Google纬度": lat,
            "Google经度": lng,
            "核验状态": status,
            "备注": note,
            "证据文件": f"work/maps_reads/{idx:03d}_{source['提取餐厅/地点名'].replace('·','').replace(' ','_')}.md",
        })

    write_csv(
        OUT / "GoogleMaps_待打开20条_读取解析结果.csv",
        live_rows,
        ["原表行号", "来源", "序号/名称", "标题/名称", "提取餐厅/地点名", "Google候选名", "Google候选详情/地址", "Google纬度", "Google经度", "核验状态", "备注", "证据文件"],
    )

    user_rows = [
        {
            "用户给的名称": r[0],
            "用户给的地址": r[1],
            "Google候选名": r[2],
            "Google候选详情/地址": r[3],
            "Google纬度": r[4],
            "Google经度": r[5],
            "核验状态": r[6],
            "备注": r[7],
            "证据文件": r[8],
        }
        for r in USER_RESULTS
    ]
    write_csv(
        OUT / "用户补充地址_GoogleMaps核验_20260613.csv",
        user_rows,
        ["用户给的名称", "用户给的地址", "Google候选名", "Google候选详情/地址", "Google纬度", "Google经度", "核验状态", "备注", "证据文件"],
    )

    next_rows = []
    for idx, result in NEXT_RESULTS.items():
        source = by_idx[idx]
        name, detail, lat, lng, status, note = result
        next_rows.append({
            "原表行号": idx,
            "来源": source["来源"],
            "序号/名称": source["序号/名称"],
            "标题/名称": source["标题/名称"],
            "提取餐厅/地点名": source["提取餐厅/地点名"],
            "Google候选名": name,
            "Google候选详情/地址": detail,
            "Google纬度": lat,
            "Google经度": lng,
            "核验状态": status,
            "备注": note,
            "证据文件": f"work/maps_reads_next/{idx:03d}_{source['提取餐厅/地点名'].replace('·','').replace(' ','_')}.md",
        })

    write_csv(
        OUT / "GoogleMaps_第二批13条_读取解析结果.csv",
        next_rows,
        ["原表行号", "来源", "序号/名称", "标题/名称", "提取餐厅/地点名", "Google候选名", "Google候选详情/地址", "Google纬度", "Google经度", "核验状态", "备注", "证据文件"],
    )

    updated = []
    for idx, row in enumerate(rows, start=1):
        row = dict(row)
        if idx in LIVE_RESULTS:
            name, detail, lat, lng, status, note = LIVE_RESULTS[idx]
            row.update({
                "Google候选名": name,
                "Google候选详情": detail,
                "Google纬度": lat,
                "Google经度": lng,
                "Google页面文件": str(ROOT / f"work/maps_reads/{idx:03d}_{row['提取餐厅/地点名'].replace('·','').replace(' ','_')}.md"),
                "Google搜索状态": status,
                "是否可先作为地址候选": "是" if "已确认" in status else "否",
                "备注": note,
            })
        if idx in NEXT_RESULTS:
            name, detail, lat, lng, status, note = NEXT_RESULTS[idx]
            row.update({
                "Google候选名": name,
                "Google候选详情": detail,
                "Google纬度": lat,
                "Google经度": lng,
                "Google页面文件": str(ROOT / f"work/maps_reads_next/{idx:03d}_{row['提取餐厅/地点名'].replace('·','').replace(' ','_')}.md"),
                "Google搜索状态": status,
                "是否可先作为地址候选": "是" if "已确认" in status else "否",
                "备注": note,
            })
        key = (row["来源"], row["序号/名称"])
        if key in USER_OVERLAY:
            name, detail, lat, lng, status, note = USER_OVERLAY[key]
            row.update({
                "Google候选名": name,
                "Google候选详情": detail,
                "Google纬度": lat,
                "Google经度": lng,
                "Google搜索状态": status,
                "是否可先作为地址候选": "是",
                "备注": note,
            })
        updated.append(row)

    write_csv(
        OUT / "仍需地图查询_110条_GoogleMaps查询表_补充读取后.csv",
        updated,
        list(rows[0].keys()),
    )

    confirmed_now = [
        row for row in updated
        if "已确认" in row.get("Google搜索状态", "")
    ]
    live_confirmed = [
        row for row in live_rows
        if "已确认" in row["核验状态"]
    ]
    next_confirmed = [
        row for row in next_rows
        if "已确认" in row["核验状态"]
    ]
    user_matched_confirmed = [("小红书", "54"), ("小红书", "81"), ("小红书", "105")]

    stat_lines = [
        "当前总池：228",
        "原已确认详细坐标：64",
        "按“无可用名字删除”后的删除/放弃：54",
        "本轮开始仍需地图查询：110",
        f"本轮打开 Google Maps 的条目：{len(LIVE_RESULTS)}",
        f"本轮 20 条中可确认：{len(live_confirmed)}",
        f"第二批无坐标/未确认 13 条中可确认：{len(next_confirmed)}",
        f"用户补充地址匹配当前待查并确认：{len(user_matched_confirmed)}",
        "用户补充地址更新既有确认坐标：2（Lesnoy、煮江湖；不增加总数）",
        "用户补充地址暂未匹配当前总表源记录：3（ORA、muza kitchen、湘味小厨）",
        "用户补充地址冲突需核：1（Caravan）",
        "更新后已确认详细坐标：80",
        "更新后仍无详细坐标但有名字待继续核验：94",
        "更新后删除/放弃：54",
    ]
    (OUT / "地图补充后_统计_20260613.txt").write_text("\n".join(stat_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
