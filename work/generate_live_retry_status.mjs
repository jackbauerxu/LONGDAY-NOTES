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
    "剩余序号": "1",
    "提取名": "念家湘湘菜馆",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页、用户原帖、经营者主页、地点相关笔记；仅确认塔什干、电话、夏日酒店/华成商务酒店关系，未得到可核验地址或地图地点详情",
    "原帖链接": "https://www.xiaohongshu.com/explore/67e15d50000000001d03b5da?xsec_token=ABSjbROGibr6YvnxefwZ5zliCxwUru-bjNkgOJGVgQ6RQ=&xsec_source=",
    "作者昵称/用户名": "噗💨🤓；塔什干《念家湘湘菜馆》+998772622888",
    "作者小红书号": "经营者主页：26482737803",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/65990d2b0000000022014029?xsec_token=ABZgXI68uCkxo3O83OB6bc3idKI2YD0kwFFJtuSOjARrQ=&xsec_source=pc_search",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_01_念家湘湘菜馆_post1.md; outputs/final16_live_retry_01_念家湘湘菜馆_profile_phone.md; outputs/final16_live_retry_01_念家湘湘菜馆_post_huacheng.md",
  },
  {
    "剩余序号": "2",
    "提取名": "中乌饭店",
    "处理结果": "保留-地址坐标已核验",
    "原因": "小红书原帖给出明确地址；Yandex 地址详情页给出同一地址坐标。地图结果为地址/建筑物详情，不是同名餐厅 POI",
    "原帖链接": "https://www.xiaohongshu.com/explore/6885148a000000001002412f?xsec_token=ABWhs2SRqQxSdKmW6ZjpfaLjrUSfH9H1P80R2Ga5vlEX0=&xsec_source=",
    "作者昵称/用户名": "噗💨🤓",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/5a05865411be1027ee4ab2cf?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=AB7sIuClz-AUPGnwSSBxpRsX3wNo1Wx9KSW_ucMK9pU2E=&xsec_source=pc_note",
    "地址/坐标": "Улица Нукусская 83 А / Nukus Street, 83A, Tashkent; 41.286675, 69.271661",
    "地图核验": "Yandex 地址详情：Nukus Street, 83A, Tashkent; Coordinates: 41.286675, 69.271661",
    "证据文件": "outputs/final16_live_retry_02_中乌饭店_post1.md; outputs/final16_live_retry_02_中乌饭店_yandex_nukus83a.md",
  },
  {
    "剩余序号": "3",
    "提取名": "成都饭店",
    "处理结果": "删除放弃",
    "原因": "已读取原帖和疑似官方主页；原帖只确认塔什干中餐语境，主页仅有账号名和小红书号，未得到可核验地址或地图地点详情",
    "原帖链接": "https://www.xiaohongshu.com/explore/694fc617000000002103cd6c?xsec_token=ABhoWXRS5FACLGrVPoOjdBxq-JhdrtG-zA-YLmp26WBJM=&xsec_source=",
    "作者昵称/用户名": "每天都想炒老板；塔什干成都饭店",
    "作者小红书号": "疑似官方主页：26484846050",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/5d2f4573000000001200968c?xsec_token=ABdw3p5SpWxkxsp3jScS5ytzT1YPsmJddt5GFbARJfSdA=&xsec_source=pc_comment",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_03_成都饭店_post1.md; outputs/final16_live_retry_03_成都饭店_profile_official.md",
  },
  {
    "剩余序号": "4",
    "提取名": "川湘食府",
    "处理结果": "保留-地址坐标已核验",
    "原因": "小红书原帖给出明确地址；Yandex 地址详情页给出同一地址坐标。地图结果为地址/建筑物详情，不是同名餐厅 POI",
    "原帖链接": "https://www.xiaohongshu.com/explore/66fadb96000000001b0220c0?xsec_token=ABFabGpLu8U56g5QxZRrQSN7rHsGu7a0Ziw0o8s0T0FCA=&xsec_source=",
    "作者昵称/用户名": "噗💨🤓",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/5a05865411be1027ee4ab2cf?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=AB7sIuClz-AUPGnwSSBxpRsX3wNo1Wx9KSW_ucMK9pU2E=&xsec_source=pc_note",
    "地址/坐标": "Ташкент, улица Сарыкуль, 4 / Sarykul Street, 4, Tashkent; 41.286715, 69.282845",
    "地图核验": "Yandex 地址详情：Sarykul Street, 4, Tashkent; Coordinates: 41.286715, 69.282845",
    "证据文件": "outputs/final16_live_retry_04_川湘食府_post1.md; outputs/final16_live_retry_04_川湘食府_yandex_sarykul4.md",
  },
  {
    "剩余序号": "5",
    "提取名": "长安巷·融合菜",
    "处理结果": "保留-用户补充地址坐标已核验",
    "原因": "搜索页有同名结果“长安巷🇺🇿”，但原帖访问异常；用户补充地址 Tashkent, Katta Mirobod Street, 139，Yandex 地址详情页给出同一地址坐标。地图结果为地址/建筑物详情，不是同名餐厅 POI",
    "原帖链接": "https://www.xiaohongshu.com/search_result/68a88ebd000000001c0145b4?xsec_token=ABv3SCXK2O8Q4E222dqxYe9jTiX38AJSVWPrimj2mSLvY=&xsec_source=",
    "作者昵称/用户名": "噗💨🤓",
    "作者小红书号": "",
    "作者主页链接": "",
    "地址/坐标": "Tashkent, Katta Mirobod Street, 139 / Katta Mirabad Street, 139, Tashkent; 41.288402, 69.267654",
    "地图核验": "Yandex 地址详情：Katta Mirabad Street, 139, Tashkent; Coordinates: 41.288402, 69.267654",
    "证据文件": "outputs/final16_live_retry_05_长安巷_融合菜_search.md; outputs/final16_live_retry_05_长安巷_融合菜_post1.md; outputs/final16_remote_retry_05_长安巷_融合菜_post1.md; outputs/user_address_yandex_长安巷_katta_mirobod_139.md",
  },
  {
    "剩余序号": "6",
    "提取名": "成都蜀味汤火锅",
    "处理结果": "保留-地址坐标已核验",
    "原因": "小红书原帖给出明确地址；Yandex 地址详情页给出同一地址坐标。地图结果为地址/建筑物详情，不是同名餐厅 POI",
    "原帖链接": "https://www.xiaohongshu.com/explore/68dfbc020000000007035799?xsec_token=ABD61I67y0jkr2zimBoxlPiX56L843fpLFcvPTyI-Za4s=&xsec_source=",
    "作者昵称/用户名": "噗💨🤓",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/5a05865411be1027ee4ab2cf?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=AB7sIuClz-AUPGnwSSBxpRsX3wNo1Wx9KSW_ucMK9pU2E=&xsec_source=pc_note",
    "地址/坐标": "Abdurauf Fitrat 97 / Abdurauf Fitrat Street, 97, Tashkent; 41.268926, 69.298970",
    "地图核验": "Yandex 地址详情：Abdurauf Fitrat Street, 97, Tashkent; Coordinates: 41.268926, 69.298970",
    "证据文件": "outputs/final16_live_retry_06_成都蜀味汤火锅_search_after_verify.md; outputs/final16_live_retry_06_成都蜀味汤火锅_post1.md; outputs/final16_live_retry_06_成都蜀味汤火锅_yandex_fitrat97.md",
  },
  {
    "剩余序号": "7",
    "提取名": "西南川菜馆",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页；结果为泛川菜/中餐结果，未出现同名或强相关原帖，也未得到可核验地址或地图地点详情",
    "原帖链接": "",
    "作者昵称/用户名": "",
    "作者小红书号": "",
    "作者主页链接": "",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_07_西南川菜馆_search.md",
  },
  {
    "剩余序号": "8",
    "提取名": "VINO GALAXY 酒水管家",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页；结果为塔什干酒吧/酒庄等泛结果，未出现同名或强相关店铺原帖，也未得到可核验地址或地图地点详情",
    "原帖链接": "",
    "作者昵称/用户名": "",
    "作者小红书号": "",
    "作者主页链接": "",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_08_VINO_GALAXY_search.md",
  },
  {
    "剩余序号": "9",
    "提取名": "包子客牛肉汤包",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页和两篇高相关原帖；第一篇仅确认店名和早餐语境，第二篇为山东语境，均未得到可核验地址或地图地点详情",
    "原帖链接": "https://www.xiaohongshu.com/explore/684cd92f00000000210187e8?xsec_token=ABn-SuCUf1pFivLxxplyLvKa62PJPHo-sabQ8_gT7FOT4=&xsec_source=; https://www.xiaohongshu.com/explore/6849759d000000002202eb20?xsec_token=ABe1qAFO71hvVDmRy2u-e9QgjrkWkJY5bZcpCs1Di11AU=&xsec_source=",
    "作者昵称/用户名": "芹香子；新雨初霁",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/5a03aae94eacab0ed84430dc?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=ABT3Xn90nGyNN_xVQaNJ5sBhjNbs6KcENlRiNzB2a9KLI=&xsec_source=pc_note; https://www.xiaohongshu.com/user/profile/616463ba000000000202486b?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=ABk0rKEbmVFgmKSgUYA8zarcwvnZoXXm_l1HyrBqE0WyQ=&xsec_source=pc_note",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_09_包子客牛肉汤包_search.md; outputs/final16_live_retry_09_包子客牛肉汤包_post1.md; outputs/final16_live_retry_09_包子客牛肉汤包_post2.md",
  },
  {
    "剩余序号": "10",
    "提取名": "川渝私房菜（东方明珠酒店）",
    "处理结果": "保留-用户补充地址坐标已核验",
    "原因": "已读取搜索页和原帖正文评论，原帖只确认塔什干川渝私房菜语境；用户补充地址 Hamal koʻchasi, 25/2，Yandex 地址详情页给出同一地址坐标。地图显示楼内为 Vostok 酒店，未确认东方明珠酒店关系",
    "原帖链接": "https://www.xiaohongshu.com/explore/686def420000000022033edc?xsec_token=AB2KQvfcoBPXPrwksbcLWo-TEKO7jqZc2ISTu0MzcMMLA=&xsec_source=",
    "作者昵称/用户名": "信女愿天下有心人终能下签",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/59f4c19e4eacab582e014872?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=ABt-PMFvwAAGkfIXUrU8a5rjP6vq8OF804Jvy8MigCUbM=&xsec_source=pc_note",
    "地址/坐标": "Hamal koʻchasi, 25/2 / Hamal Street, 25/2, Tashkent; 41.284059, 69.302194",
    "地图核验": "Yandex 地址详情：Hamal Street, 25/2, Tashkent; Coordinates: 41.284059, 69.302194；楼内显示 Vostok 酒店",
    "证据文件": "outputs/final16_live_retry_10_川渝私房菜_post1.md; outputs/user_address_yandex_川渝私房菜_hamal_street_25_2.md",
  },
  {
    "剩余序号": "11",
    "提取名": "土窑烧烤",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页和高相关“土窑坑烤”原帖；原帖为天津语境，不对应塔什干，且未得到可核验地址或地图地点详情",
    "原帖链接": "https://www.xiaohongshu.com/explore/6822c8820000000022004ca5?xsec_token=ABfRKRDLP_Mo4urvl9wJjbBXHc29oBqmuKYmnnO459Owg=&xsec_source=",
    "作者昵称/用户名": "Winnie",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/589de314a9b2ed495823a89d?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=AB40tRRClqRCD9aG69FoM3nuqcJt1cd9ThhLW4ItYrYBw=&xsec_source=pc_note",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_11_土窑烧烤_search.md; outputs/final16_live_retry_11_土窑烧烤_post1.md",
  },
  {
    "剩余序号": "12",
    "提取名": "万记川湘菜",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页和同名原帖；正文仅评价菜品，评论仅有人询问位置，未得到可核验地址或地图地点详情",
    "原帖链接": "https://www.xiaohongshu.com/explore/68a61ae0000000001b0305e3?xsec_token=ABJIoXZe-0j5wYfD5_ODaAhBkfrVmzBigyNZs3pCQwFM0=&xsec_source=",
    "作者昵称/用户名": "爱吃的杨",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/60c4ad980000000001007832?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=AB3h4psCpQvHHO0QHNVPLQLoH3SBQ6JcAAAzK4QIqw5ZQ=&xsec_source=pc_note",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_12_万记川湘菜_search.md; outputs/final16_live_retry_12_万记川湘菜_post1.md",
  },
  {
    "剩余序号": "13",
    "提取名": "阿尔马雷克市好运中餐厅",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页；未出现同名或强相关原帖，只有泛中餐结果和联想词，未得到可核验地址或地图地点详情",
    "原帖链接": "",
    "作者昵称/用户名": "",
    "作者小红书号": "",
    "作者主页链接": "",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_13_阿尔马雷克市好运中餐厅_search.md",
  },
  {
    "剩余序号": "14",
    "提取名": "长安大饭店",
    "处理结果": "保留-地址坐标已核验",
    "原因": "小红书原帖及评论给出撒马尔罕、火车站附近、48学校旁边和明确打车地址；Yandex 地址详情页给出同一门牌坐标。地图结果为地址/建筑物详情，不是同名餐厅 POI",
    "原帖链接": "https://www.xiaohongshu.com/explore/6857f523000000001001093f?xsec_token=AB-N6el5-DcqqUa1lTKqtbtuvUvt5A3cCzJ5rPgqqPKd8=&xsec_source=",
    "作者昵称/用户名": "噗💨🤓",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/5a05865411be1027ee4ab2cf?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=AB7sIuClz-AUPGnwSSBxpRsX3wNo1Wx9KSW_ucMK9pU2E=&xsec_source=pc_note",
    "地址/坐标": "Улица Ибн Холдун 10а / Ibn Xoldun koʻchasi, 10А, Samarkand; 39.683305, 66.925845",
    "地图核验": "Yandex 地址详情：Ibn Xoldun koʻchasi, 10А, Samarkand; Coordinates: 39.683305, 66.925845",
    "证据文件": "outputs/final16_live_retry_14_长安大饭店_search.md; outputs/final16_live_retry_14_长安大饭店_post1.md; outputs/final16_live_retry_14_长安大饭店_yandex_ibn_kholdun10a.md",
  },
  {
    "剩余序号": "15",
    "提取名": "撒马尔罕新疆风味餐厅",
    "处理结果": "删除放弃",
    "原因": "已读取搜索页和两篇新疆菜相关候选原帖；候选未给出撒马尔罕具体地址或可核验地图详情，且部分结果明显不是撒马尔罕语境",
    "原帖链接": "https://www.xiaohongshu.com/explore/698f9918000000001a034827?xsec_token=ABPemTQ128IN9dsgPXRqz4Euf4QLcP581JdgcfBpPe_K4=&xsec_source=; https://www.xiaohongshu.com/explore/66ce4796000000001f03f7f6?xsec_token=ABUFY1BxEnfJuk9rdMJt3UZQy6T2xiWvOMrml6IwXhl1E=&xsec_source=",
    "作者昵称/用户名": "观鸟区即将迎来大变；许甜心💍",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/67893d70000000000e013ee7?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=ABjATuaZBWhJMspVtRIQjvHKqvkKPOEXtp-tzmbw285mQ=&xsec_source=pc_note; https://www.xiaohongshu.com/user/profile/5a180a4b11be107ff962dd86?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=ABlup0boFcIVG13y98LGcPBcwBEuB3PETOoH1Iuh_V_fg=&xsec_source=pc_note",
    "地址/坐标": "",
    "地图核验": "",
    "证据文件": "outputs/final16_live_retry_15_撒马尔罕新疆风味餐厅_search.md; outputs/final16_live_retry_15_撒马尔罕新疆风味餐厅_post1.md; outputs/final16_live_retry_15_撒马尔罕新疆风味餐厅_post2.md",
  },
  {
    "剩余序号": "16",
    "提取名": "安集延国际酒店中餐厅（川湘菜）",
    "处理结果": "保留-地址坐标已核验",
    "原因": "小红书原帖给出酒店英文名和地址，并说明二楼中餐厅为川湘菜；Yandex 同名酒店地点详情页确认地址。地图结果为酒店 POI，中餐厅位于酒店二楼",
    "原帖链接": "https://www.xiaohongshu.com/explore/68f8915c000000000301f1af?xsec_token=ABpw-LsJWh931BZeU6TTUva8w2D6HIb1nJ4PUOdcQgGJk=&xsec_source=",
    "作者昵称/用户名": "bigdb",
    "作者小红书号": "",
    "作者主页链接": "https://www.xiaohongshu.com/user/profile/609cfe610000000001000daf?channel_type=web_note_detail_r10&parent_page_channel_type=web_profile_board&xsec_token=ABo8YN6Slo4Aka8_yBEaE4najq-54_GbUnXIxSNDtl9b8=&xsec_source=pc_note",
    "地址/坐标": "ANDIJON INTERNATIONAL HOTEL / Andizhan, Barhayot ko'chasi, 38; 40.782043, 72.331515",
    "地图核验": "Yandex 酒店地点详情：Andijan Hotel / Andizhan, Barhayot ko'chasi, 38; 坐标取自详情页 URL ll=72.331515,40.782043",
    "证据文件": "outputs/final16_live_retry_16_安集延国际酒店中餐厅_search.md; outputs/final16_live_retry_16_安集延国际酒店中餐厅_post1.md; outputs/final16_live_retry_16_安集延国际酒店中餐厅_yandex_andijon_international.md",
  },
];

const allRows = rows.sort((a, b) => Number(a["剩余序号"]) - Number(b["剩余序号"]));
const header = Object.keys(allRows[0]);
writeCsv("final16_继续读取_处理结果.csv", header, allRows);
writeCsv("final16_继续读取_保留确认.csv", header, allRows.filter((r) => r["处理结果"].startsWith("保留")));
writeCsv("final16_继续读取_删除放弃.csv", header, allRows.filter((r) => r["处理结果"] === "删除放弃"));
writeCsv("final16_继续读取_暂停或未继续.csv", header, allRows.filter((r) => !r["处理结果"].startsWith("保留") && r["处理结果"] !== "删除放弃"));

const keepRows = allRows.filter((r) => r["处理结果"].startsWith("保留"));
const deleteRows = allRows.filter((r) => r["处理结果"] === "删除放弃");
const pausedRows = allRows.filter((r) => !r["处理结果"].startsWith("保留") && r["处理结果"] !== "删除放弃");

const md = `# final16 继续读取处理结果

## 本轮结果

- 保留确认：${keepRows.length} 条
- 删除放弃：${deleteRows.length} 条
- 暂停或未继续：${pausedRows.length} 条

## 保留确认

- 2. 中乌饭店：原帖地址为 Улица Нукусская 83 А；Yandex 地址详情坐标 41.286675, 69.271661。
- 4. 川湘食府：原帖地址为 Ташкент, улица Сарыкуль, 4；Yandex 地址详情坐标 41.286715, 69.282845。
- 5. 长安巷·融合菜：用户补充地址为 Tashkent, Katta Mirobod Street, 139；Yandex 地址详情坐标 41.288402, 69.267654。
- 6. 成都蜀味汤火锅：原帖地址为 Abdurauf Fitrat 97；Yandex 地址详情坐标 41.268926, 69.298970。
- 10. 川渝私房菜（东方明珠酒店）：用户补充地址为 Hamal koʻchasi, 25/2；Yandex 地址详情坐标 41.284059, 69.302194。楼内显示 Vostok 酒店，未确认东方明珠酒店关系。
- 14. 长安大饭店：原帖评论地址为 Улица Ибн Холдун 10а；Yandex 地址详情坐标 39.683305, 66.925845。
- 16. 安集延国际酒店中餐厅（川湘菜）：原帖给出 ANDIJON INTERNATIONAL HOTEL / Barhayot ko'chasi, 38，二楼中餐厅；Yandex 酒店地点详情坐标 40.782043, 72.331515。

## 删除放弃

- 1. 念家湘湘菜馆：读过搜索页、原帖、经营者主页、地点相关笔记，仍无可核验地址或地图详情。
- 3. 成都饭店：读过原帖和疑似官方主页，仍无可核验地址或地图详情。
- 7. 西南川菜馆：搜索页无同名或强相关原帖，仍无可核验地址或地图详情。
- 8. VINO GALAXY 酒水管家：搜索页无同名或强相关店铺原帖，仍无可核验地址或地图详情。
- 9. 包子客牛肉汤包：读过两篇高相关原帖，仍无可核验地址或地图详情。
- 11. 土窑烧烤：高相关原帖为天津语境，不对应塔什干。
- 12. 万记川湘菜：同名原帖无地址，评论仅有人询问位置。
- 13. 阿尔马雷克市好运中餐厅：搜索页无同名或强相关原帖。
- 15. 撒马尔罕新疆风味餐厅：两篇新疆菜相关候选均无撒马尔罕具体地址或可核验地图详情。

## 暂停原因

- 无。

## 输出文件

- final16_继续读取_处理结果.csv
- final16_继续读取_保留确认.csv
- final16_继续读取_删除放弃.csv
- final16_继续读取_暂停或未继续.csv
`;

fs.writeFileSync(path.join(outDir, "final16_继续读取_说明.md"), md);
console.log(JSON.stringify({
  total: allRows.length,
  keep: keepRows.length,
  delete: deleteRows.length,
  paused_or_pending: pausedRows.length,
}, null, 2));
