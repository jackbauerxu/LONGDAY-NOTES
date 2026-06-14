import fs from "node:fs";
import path from "node:path";

const outDir = "/Users/g90/Documents/Codex/2026-06-13/hermes/outputs";
fs.mkdirSync(outDir, { recursive: true });

function csvEscape(value) {
  const s = String(value ?? "");
  return /[",\n\r]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

function writeCsv(name, header, rows) {
  const body = [header.join(","), ...rows.map((row) => header.map((h) => csvEscape(row[h])).join(","))].join("\n") + "\n";
  fs.writeFileSync(path.join(outDir, name), "\uFEFF" + body);
}

const rows = [
  {
    "名称": "中乌长安美食城",
    "用户补充地址": "Geydar Aliyev koʻchasi, 189",
    "地图核验状态": "已核验-地址详情",
    "地图名称/地址": "Geydar Aliyev Street, 189, Tashkent",
    "坐标": "41.276910, 69.274203",
    "备注": "Yandex 为具体门牌详情；楼内显示 Shaanxi Snacks 等商户，不是同名餐厅 POI",
    "证据文件": "outputs/user_address_yandex_中乌长安美食城_geydar_aliyev_189.md",
  },
  {
    "名称": "长安巷·融合菜",
    "用户补充地址": "Tashkent, Katta Mirobod Street, 139",
    "地图核验状态": "已核验-地址详情；已同步 final16 第 5 条",
    "地图名称/地址": "Katta Mirabad Street, 139, Tashkent",
    "坐标": "41.288402, 69.267654",
    "备注": "Yandex 为具体门牌详情；楼内显示 Marakand Palace，不是同名餐厅 POI",
    "证据文件": "outputs/user_address_yandex_长安巷_katta_mirobod_139.md",
  },
  {
    "名称": "巴蜀印象",
    "用户补充地址": "Abdulla Qahhor 49",
    "地图核验状态": "已核验-地址详情",
    "地图名称/地址": "Abdulla Qahhor Street, 49, Tashkent",
    "坐标": "41.277357, 69.263738",
    "备注": "Yandex 为具体门牌详情；楼内显示 Atlet.uz、Mitesoro、VinTash 等商户，不是同名餐厅 POI",
    "证据文件": "outputs/user_address_yandex_巴蜀印象_abdulla_qahhor_49.md",
  },
  {
    "名称": "川渝私房菜（东方明珠酒店）",
    "用户补充地址": "Hamal koʻchasi, 25/2",
    "地图核验状态": "已核验-地址详情；已同步 final16 第 10 条",
    "地图名称/地址": "Hamal Street, 25/2, Tashkent",
    "坐标": "41.284059, 69.302194",
    "备注": "Yandex 为具体门牌详情；楼内显示 Vostok 酒店，未确认东方明珠酒店关系",
    "证据文件": "outputs/user_address_yandex_川渝私房菜_hamal_street_25_2.md",
  },
  {
    "名称": "塔什干川蓉燚中餐厅",
    "用户补充地址": "Small Ring Rd 16",
    "地图核验状态": "已核验-地址详情",
    "地图名称/地址": "Small Ring Road, 16, Tashkent",
    "坐标": "41.320287, 69.193471",
    "备注": "Yandex 为具体门牌详情；楼内显示 Zoda Cheesecake Factory、Paul Branco、Casa Deco 等商户，不是同名餐厅 POI",
    "证据文件": "outputs/user_address_yandex_川蓉燚_small_ring_16.md",
  },
  {
    "名称": "塔什干｜中餐｜四川酒店",
    "用户补充地址": "Ташкент, улица Шахжахан, 2А",
    "地图核验状态": "已核验-地址详情；楼内有同名酒店 POI",
    "地图名称/地址": "Shahjahan Street, 2A, Tashkent",
    "坐标": "41.285706, 69.248915",
    "备注": "Yandex 门牌详情楼内显示 Sichuan Hotel / 四川饭店",
    "证据文件": "outputs/user_address_yandex_四川酒店_shakhzhakhan_2a.md",
  },
  {
    "名称": "China Chuan Chuan",
    "用户补充地址": "Улица Мирабад, 9а / Mirabad Street, 9A",
    "地图核验状态": "已核验-同名地点详情",
    "地图名称/地址": "China Chuan Chuan, Tashkent, Mirabad Street, 9А",
    "坐标": "41.294387, 69.269155",
    "备注": "地址来自用户截图；Yandex 为同名餐厅地点详情",
    "证据文件": "outputs/user_address_yandex_china_chuan_chuan_mirabad_9a.md; /var/folders/m7/1dwxpyq514l6l3nh87pbfgdm0000gn/T/codex-clipboard-439131d1-57ec-4249-8417-625e02e6a700.png",
  },
];

const header = Object.keys(rows[0]);
writeCsv("用户补充地址_地图核验.csv", header, rows);

const md = `# 用户补充地址地图核验

共 ${rows.length} 条，均已用 Yandex 打开到地址详情或地点详情。

## 已同步到 final16

- 长安巷·融合菜：Katta Mirabad Street, 139, Tashkent；41.288402, 69.267654。
- 川渝私房菜（东方明珠酒店）：Hamal Street, 25/2, Tashkent；41.284059, 69.302194。楼内显示 Vostok 酒店，未确认东方明珠酒店关系。

## 作为补充地址保留

- 中乌长安美食城：Geydar Aliyev Street, 189, Tashkent；41.276910, 69.274203。
- 巴蜀印象：Abdulla Qahhor Street, 49, Tashkent；41.277357, 69.263738。
- 塔什干川蓉燚中餐厅：Small Ring Road, 16, Tashkent；41.320287, 69.193471。
- 塔什干｜中餐｜四川酒店：Shahjahan Street, 2A, Tashkent；41.285706, 69.248915。
- China Chuan Chuan：Mirabad Street, 9A, Tashkent；41.294387, 69.269155。
`;

fs.writeFileSync(path.join(outDir, "用户补充地址_地图核验.md"), md);
console.log(JSON.stringify({ total: rows.length }, null, 2));
