#!/usr/bin/env python3
"""
忆蚀 Subliminal 24h玩家舆情简报
聚焦过去24小时内海内外TOP10负面评价，含原文链接和时间验证
"""

import os
import json
import smtplib
from openai import OpenAI
from duckduckgo_search import DDGS
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GAME_NAME_ZH = "忆蚀"
GAME_NAME_EN = "Subliminal"
PUBLISHER = "Infini Fun"

BILIBILI_KOLS = [
    "与山", "友利奈绪大魔王", "陈子墨大喇叭", "坂本叔",
    "阿虚-Kurv", "半支烟", "Yommyko", "虚构的野心",
    "攸米Youmi", "糯米SnuomiQ", "秃头荷莱鹿", "模拟小羊owo",
    "米开心6", "薯米麻喹", "抛瓜大力", "天明iii",
    "黑泽久留美", "陈三岁", "Gluneko", "你是nana的小可",
    "屯君SOAP",
]

RECIPIENT_EMAIL    = os.environ["REPORT_RECIPIENT_EMAIL"]
SENDER_EMAIL       = os.environ["GMAIL_SENDER_EMAIL"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
DEEPSEEK_API_KEY   = os.environ["DEEPSEEK_API_KEY"]

CST = timezone(timedelta(hours=8))
NOW_CST = datetime.now(CST)
REPORT_DATE = NOW_CST.strftime("%Y年%m月%d日")
REPORT_DATE_SHORT = NOW_CST.strftime("%Y%m%d")

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def search_web(query, max_results=5):
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, timelimit="d", max_results=max_results, safesearch="off"))
        return results
    except Exception as e:
        print(f"  ⚠️ 搜索失败 [{query[:40]}]: {e}")
        return []


def collect_negative_feedback():
    all_results = []
    queries = [
        f"{GAME_NAME_EN} game crash bug",
        f"{GAME_NAME_EN} fps lag stutter performance",
        f"{GAME_NAME_EN} negative review",
        f"{GAME_NAME_ZH} 崩溃 闪退",
        f"{GAME_NAME_ZH} 卡顿 帧率",
        f"{GAME_NAME_ZH} 差评 bug",
        f"{GAME_NAME_ZH} steam 评测",
        f"{GAME_NAME_EN} steam review",
        f"{GAME_NAME_EN} reddit",
        f"{GAME_NAME_ZH} taptap 评价",
        f"{GAME_NAME_ZH} NGA",
        f"{GAME_NAME_ZH} 微博",
    ]
    for kol in BILIBILI_KOLS:
        queries.append(f"bilibili {kol} {GAME_NAME_ZH}")

    print(f"🔍 开始搜索，共 {len(queries)} 个查询...")
    for i, q in enumerate(queries):
        print(f"  [{i+1}/{len(queries)}] {q[:50]}")
        for r in search_web(q):
            all_results.append({
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "body": r.get("body", ""),
                "query": q,
            })

    seen = set()
    unique = []
    for r in all_results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    print(f"✅ 搜索完成，共 {len(unique)} 条唯一结果")
    return unique


def analyze_top10(raw_results):
    kol_names = "、".join(BILIBILI_KOLS)
    results_text = "\n\n".join([
        f"[{i+1}] 标题：{r['title']}\n链接：{r['url']}\n内容：{r['body'][:400]}"
        for i, r in enumerate(raw_results[:80])
    ])

    prompt = f"""
你是游戏舆情分析师，分析《{GAME_NAME_ZH}》（{GAME_NAME_EN}）过去24小时内玩家负面反馈。
今天是 {REPORT_DATE}（北京时间）。

请从以下搜索结果中：
1. 只保留与《{GAME_NAME_ZH}》或《{GAME_NAME_EN}》明确相关的负面内容
2. 优先选择有玩家原话、有链接、问题严重的内容
3. 识别是否来自合作主播：{kol_names}
4. 验证时间是否在24h内

选出TOP10负面评价，严格输出以下JSON，不要有任何其他内容：

{{
  "top10": [
    {{
      "rank": 1,
      "platform": "Steam/Reddit/B站/微博/NGA/TapTap/Twitter/YouTube等",
      "is_kol": false,
      "kol_name": null,
      "issue_type": "游戏崩溃/帧率问题/卡顿/加载问题/存档丢失/其他bug/综合差评",
      "severity": "严重/中等/轻微",
      "original_quote": "玩家原话，尽量完整保留",
      "summary": "一句话总结核心问题",
      "url": "原文链接（从搜索结果链接字段取，必填）",
      "time_verified": "24h内确认/时间未确认",
      "time_note": "如：今日发布/昨日/无时间标记"
    }}
  ],
  "total_negative_found": 0,
  "search_coverage": "覆盖平台说明",
  "data_note": "数据质量说明"
}}

搜索结果：
{results_text}
"""

    print("🤖 正在分析提取TOP10...")
    resp = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()

    try:
        data = json.loads(text)
        return data.get("top10", []), {
            "total_negative_found": data.get("total_negative_found", 0),
            "search_coverage": data.get("search_coverage", ""),
            "data_note": data.get("data_note", ""),
        }
    except:
        start, end = text.find("{"), text.rfind("}") + 1
        if start != -1 and end > start:
            try:
                data = json.loads(text[start:end])
                return data.get("top10", []), {"total_negative_found": 0, "search_coverage": "部分解析", "data_note": ""}
            except:
                pass
        return [], {"total_negative_found": 0, "search_coverage": "解析失败", "data_note": "JSON解析异常"}


def build_html(top10, meta):
    severity_styles = {
        "严重": ("#dc2626", "#fef2f2", "#fca5a5"),
        "中等": ("#ea580c", "#fff7ed", "#fed7aa"),
        "轻微": ("#ca8a04", "#fefce8", "#fde68a"),
    }
    issue_icons = {
        "游戏崩溃": "💥", "帧率问题": "📉", "卡顿": "⚡",
        "加载问题": "⏳", "存档丢失": "💾", "其他bug": "🐛", "综合差评": "👎",
    }

    cards = ""
    for item in top10:
        rank = item.get("rank", 0)
        sev = item.get("severity", "中等")
        tc, bg, bc = severity_styles.get(sev, ("#6b7280", "#f9fafb", "#e5e7eb"))
        itype = item.get("issue_type", "其他")
        icon = issue_icons.get(itype, "⚠️")
        url = item.get("url", "")
        tv = item.get("time_verified", "时间未确认")
        tbg = "#f0fdf4" if tv == "24h内确认" else "#f9fafb"
        tc2 = "#16a34a" if tv == "24h内确认" else "#6b7280"
        ti = "✅" if tv == "24h内确认" else "⚠️"
        kol = f'<span style="background:#7c3aed;color:#fff;font-size:10px;padding:2px 8px;border-radius:10px;margin-left:6px;">⭐ {item.get("kol_name","")}</span>' if item.get("is_kol") and item.get("kol_name") else ""
        link = f'<a href="{url}" target="_blank" style="display:inline-block;background:#1d4ed8;color:#fff;font-size:12px;padding:5px 14px;border-radius:6px;text-decoration:none;">🔗 查看原文</a>' if url else '<span style="font-size:12px;color:#9ca3af;">暂无链接</span>'

        cards += f"""
        <div style="background:{bg};border:1px solid {bc};border-left:4px solid {tc};border-radius:10px;padding:16px 18px;margin-bottom:14px;">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
            <span style="background:{tc};color:#fff;font-size:13px;font-weight:700;width:26px;height:26px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}</span>
            <span style="background:#1e293b;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px;">{item.get("platform","")}</span>
            <span style="color:{tc};border:1px solid {bc};font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;">{icon} {itype} · {sev}</span>
            <span style="background:{tbg};color:{tc2};font-size:10px;padding:2px 8px;border-radius:10px;">{ti} {tv}</span>
            {kol}
          </div>
          <div style="font-size:14px;font-weight:600;color:#111827;margin-bottom:8px;">{item.get("summary","")}</div>
          <blockquote style="margin:0 0 10px;padding:10px 14px;background:rgba(255,255,255,0.7);border-left:3px solid {tc};border-radius:0 6px 6px 0;font-size:13px;color:#374151;line-height:1.6;">"{item.get("original_quote","暂无原话")}"</blockquote>
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <span style="font-size:11px;color:#6b7280;">🕐 {item.get("time_note","")}</span>
            {link}
          </div>
        </div>"""

    if not cards:
        cards = '<div style="padding:20px;text-align:center;color:#6b7280;background:#f9fafb;border-radius:8px;">过去24小时内暂未检索到明显负面评价</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:660px;margin:0 auto;padding:20px 16px;">

  <div style="background:linear-gradient(135deg,#1e1b4b 0%,#7c2d12 100%);border-radius:12px;padding:24px 28px;margin-bottom:16px;color:#fff;">
    <div style="font-size:11px;opacity:0.7;margin-bottom:4px;letter-spacing:1px;">INFINI FUN · 负面舆情监控</div>
    <div style="font-size:22px;font-weight:700;margin-bottom:4px;">《忆蚀 Subliminal》</div>
    <div style="font-size:13px;opacity:0.85;">24h玩家负面评价 TOP10 · {REPORT_DATE}</div>
    <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;">
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">检索到负面评价</div>
        <div style="font-size:18px;font-weight:700;">{meta.get("total_negative_found",0)} 条</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">数据范围</div>
        <div style="font-size:13px;font-weight:600;">过去 24 小时</div>
      </div>
    </div>
  </div>

  <div style="background:#fefce8;border:1px solid #fde68a;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:12px;color:#92400e;">
    📊 {meta.get("search_coverage","")}｜{meta.get("data_note","")}｜✅ 已过滤24h内内容
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 16px;font-size:15px;color:#1e293b;">🔥 TOP10 负面评价（含原文链接）</h2>
    {cards}
  </div>

  <div style="text-align:center;color:#94a3b8;font-size:11px;padding-bottom:12px;">
    Infini Fun 舆情监控 · {REPORT_DATE} 08:00 CST · 点击「查看原文」直达原始评论
  </div>

</div>
</body>
</html>"""


def send_gmail(html_body, top10):
    severe_count = sum(1 for x in top10 if x.get("severity") == "严重")
    tag = f" 🚨 {severe_count}条严重" if severe_count else ""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【忆蚀-{REPORT_DATE_SHORT}-24h玩家舆情简报】{tag}"
    msg["From"]    = f"忆蚀舆情监控 <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL
    plain = f"忆蚀 24h负面简报 {REPORT_DATE}\n\n"
    for x in top10:
        plain += f"#{x.get('rank')} [{x.get('platform')}] {x.get('summary')}\n原文：{x.get('url','无')}\n\n"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    print(f"📧 发送中...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        s.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_bytes())
    print("✅ 发送成功！")


def main():
    print(f"\n{'='*60}\n  忆蚀 24h负面舆情简报\n  {REPORT_DATE}\n{'='*60}\n")
    raw = collect_negative_feedback()
    top10, meta = analyze_top10(raw)
    html = build_html(top10, meta)
    send_gmail(html, top10)
    print(f"\n✅ 完成！共 {len(top10)} 条负面评价")


if __name__ == "__main__":
    main()
