import fs from "node:fs";
import path from "node:path";

const sourceDir = "/Users/g90/xiaohongshu_tandian_recovered/tandian_only/xiaohongshu_research_for_unresolved56";
const outDir = "/Users/g90/Documents/Codex/2026-06-13/hermes/outputs";

const mainCsv = path.join(sourceDir, "final16_本地已保存解析结果.csv");
const retryCsv = path.join(sourceDir, "final16_slow_retry_02_中乌饭店_解析结果.csv");
const retryPage = path.join(sourceDir, "final16_slow_retry_pages/02_中乌饭店_retry2.md");

function parseCsv(text) {
  text = text.replace(/^\uFEFF/, "");
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];
    if (inQuotes) {
      if (ch === '"' && next === '"') {
        field += '"';
        i++;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(field);
      field = "";
    } else if (ch === "\n") {
      row.push(field.replace(/\r$/, ""));
      rows.push(row);
      row = [];
      field = "";
    } else {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field.replace(/\r$/, ""));
    rows.push(row);
  }
  return rows.filter((r) => r.some((v) => v !== ""));
}

function toObjects(rows) {
  const header = rows[0];
  return rows.slice(1).map((row) => Object.fromEntries(header.map((name, i) => [name, row[i] ?? ""])));
}

function escapeCsv(value) {
  const s = String(value ?? "");
  return /[",\n\r]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

function writeCsv(file, header, rows) {
  const body = [header.join(","), ...rows.map((row) => header.map((h) => escapeCsv(row[h])).join(","))].join("\n") + "\n";
  fs.writeFileSync(file, "\uFEFF" + body);
}

fs.mkdirSync(outDir, { recursive: true });

const mainRows = toObjects(parseCsv(fs.readFileSync(mainCsv, "utf8")));
const retryRows = toObjects(parseCsv(fs.readFileSync(retryCsv, "utf8")));
const retry = retryRows[0];

const crossEvidence = {
  "3": {
    result: "小红书搜索待读帖",
    reason: "其他本地已保存搜索页含同名/近似文本：成都饭店、成都饭店主理人-塔什干",
    next: "读取相关小红书帖子确认地址/定位",
    evidence: "中乌饭店 塔什干 - 小红书搜索 | 成都饭店 36 | 每天都想炒老板 37 | 2025-12-27 37；东方红餐厅 塔什干 - 小红书搜索 | 成都饭店 20 | 成都饭店主理人-塔什干 22",
    page: `${sourceDir}/final16_slow_retry_pages/02_中乌饭店_retry2.md; ${sourceDir}/batch4_xhs_search_pages/10_东方红餐厅.md`,
  },
  "4": {
    result: "小红书搜索待读帖",
    reason: "其他本地已保存搜索页含同名/近似文本：川湘食府、塔什干川湘食府",
    next: "读取相关小红书帖子确认地址/定位",
    evidence: "塔什干遇湘食府 - 小红书搜索 | 塔什干川湘食府 | 川湘食府🇺🇿｜一家上菜极快的川菜馆 78 | 噗💨🤓 24 | 2024-10-01 24",
    page: `${sourceDir}/batch3_xhs_search_pages/09_塔什干遇湘食府.md`,
  },
  "10": {
    result: "小红书搜索待读帖",
    reason: "其他本地已保存搜索页含近似文本：川渝私房菜；未确认是否对应东方明珠酒店",
    next: "读取相关小红书帖子确认地址/定位，并核对是否为东方明珠酒店内餐厅",
    evidence: "渝味山庄江湖菜 塔什干 - 小红书搜索 | 塔什干川渝私房菜 | 塔什干探店之川渝私房菜 25 | 信女愿天下有心人终能下签 26 | 2025-07-09 26",
    page: `${sourceDir}/batch4_xhs_search_pages/04_渝味山庄江湖菜.md`,
  },
};

const merged = mainRows.map((row) => {
  if (row["剩余序号"] === "2") return {
    ...row,
    "处理结果": retry["处理结果"],
    "原因": retry["原因"],
    "后续动作": retry["后续动作"],
    "证据摘录": retry["证据摘录"],
    "本地搜索页": retryPage,
  };
  const cross = crossEvidence[row["剩余序号"]];
  if (!cross) return { ...row };
  return {
    ...row,
    "处理结果": cross.result,
    "原因": cross.reason,
    "后续动作": cross.next,
    "证据摘录": cross.evidence,
    "本地搜索页": cross.page,
  };
});

const header = Object.keys(mainRows[0]);
const kept = merged.filter((row) => row["处理结果"] === "小红书搜索待读帖");
const pending = merged.filter((row) => row["处理结果"] !== "小红书搜索待读帖");

const counts = merged.reduce((acc, row) => {
  acc[row["处理结果"]] = (acc[row["处理结果"]] ?? 0) + 1;
  return acc;
}, {});

writeCsv(path.join(outDir, "final16_合并慢速重试_处理结果.csv"), header, merged);
writeCsv(path.join(outDir, "final16_合并慢速重试_保留待读帖.csv"), header, kept);
writeCsv(path.join(outDir, "final16_合并慢速重试_未成功读取或需恢复后再读.csv"), header, pending);

const md = [
  "# final16 合并慢速重试当前版",
  "",
  `来源目录：${sourceDir}`,
  "",
  "## 统计",
  "",
  `- 小红书搜索待读帖：${counts["小红书搜索待读帖"] ?? 0}`,
  `- 读取失败/疑似访问验证：${counts["读取失败/疑似安全验证"] ?? 0}`,
  `- 未读取：${counts["未读取"] ?? 0}`,
  "",
  "## 本次合并",
  "",
  "- 第 1 条「念家湘湘菜馆」：保留为小红书搜索待读帖。搜索页含同名与近似结果，但还没有原帖正文或地图地点详情证据。",
  "- 第 2 条「中乌饭店」：使用慢速重试文件更新为小红书搜索待读帖。搜索页含「中乌饭店」「塔什干中餐厅丨中乌饭店」等结果，但还没有原帖正文或地图地点详情证据。",
  "- 第 3 条「成都饭店」：在其他本地已保存搜索页中找到同名/近似结果，更新为小红书搜索待读帖。",
  "- 第 4 条「川湘食府」：在其他本地已保存搜索页中找到同名/近似结果，更新为小红书搜索待读帖。",
  "- 第 10 条「川渝私房菜（东方明珠酒店）」：在其他本地已保存搜索页中找到近似结果，更新为小红书搜索待读帖；后续必须核对是否对应东方明珠酒店。",
  "- 第 5-9、11-13 条：本地页为访问验证/登录/访问异常提示，且未找到足够明确的交叉线索，继续标记为未成功读取，不采信。",
  "- 第 14-16 条：本地没有已保存页面，继续标记为未读取。",
  "",
  "## 后续队列",
  "",
  "### 已找到搜索结果，待读原帖",
  "",
  ...kept.map((row) => `- ${row["剩余序号"]}. ${row["提取名"]}：${row["后续动作"]}`),
  "",
  "### 需恢复后再读",
  "",
  ...pending.map((row) => `- ${row["剩余序号"]}. ${row["提取名"]}：${row["处理结果"]}`),
  "",
  "## 交付文件",
  "",
  "- final16_合并慢速重试_处理结果.csv",
  "- final16_合并慢速重试_保留待读帖.csv",
  "- final16_合并慢速重试_未成功读取或需恢复后再读.csv",
].join("\n");

fs.writeFileSync(path.join(outDir, "final16_合并慢速重试_说明.md"), md + "\n");

console.log(JSON.stringify({ counts, total: merged.length, kept: kept.length, pending: pending.length }, null, 2));
