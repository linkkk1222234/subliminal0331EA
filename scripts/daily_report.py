#!/usr/bin/env python3
"""
忆蚀 Subliminal 24h玩家舆情简报
平台：B站(官方API) + YouTube(官方API) + 小黑盒(公开接口) + TikTok/小红书/Steam/Reddit(DuckDuckGo)
"""

import os
import json
import time
import smtplib
import urllib.request
import urllib.parse
from openai import OpenAI
from duckduckgo_search import DDGS
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── 配置 ────────────────────────────────────────────────────────────────────
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
YOUTUBE_API_KEY    = os.environ["YOUTUBE_API_KEY"]

CST = timezone(timedelta(hours=8))
NOW_CST = datetime.now(CST)
REPORT_DATE = NOW_CST.strftime("%Y年%m月%d日")
REPORT_DATE_SHORT = NOW_CST.strftime("%Y%m%d")
NOW_TS = time.time()
DAY_SECONDS = 86400  # 24小时

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
# ─────────────────────────────────────────────────────────────────────────────


def fetch_url(url, headers=None, timeout=10):
    """通用 HTTP 请求"""
    try:
        req = urllib.request.Request(url, headers=headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️ 请求失败 {url[:60]}: {e}")
        return None


# ── 平台1：B站官方 API ────────────────────────────────────────────────────────
def search_bilibili(keyword, max_results=10):
    results = []
    params = urllib.parse.urlencode({
        "keyword": keyword, "search_type": "video",
        "order": "pubdate", "page": 1,
    })
    data = fetch_url(f"https://api.bilibili.com/x/web-interface/search/type?{params}")
    if not data:
        return results
    for item in (data.get("data", {}).get("result", []) or [])[:max_results]:
        pub_ts = item.get("pubdate", 0)
        if NOW_TS - pub_ts <= DAY_SECONDS:
            title = item.get("title", "").replace('<em class="keyword">', "").replace("</em>", "")
            results.append({
                "title": title,
                "url": f"https://www.bilibili.com/video/{item.get('bvid','')}",
                "body": item.get("description", "") or item.get("tag", ""),
                "author": item.get("author", ""),
                "pub_time": datetime.fromtimestamp(pub_ts, tz=CST).strftime("%m-%d %H:%M"),
                "platform": "B站",
                "query": keyword,
            })
    return results


def collect_bilibili():
    print("🎬 搜索 B站...")
    results = []
    keywords = [GAME_NAME_ZH, GAME_NAME_EN,
                f"{GAME_NAME_ZH} 评测", f"{GAME_NAME_ZH} 游戏",
                f"{GAME_NAME_ZH} 崩溃", f"{GAME_NAME_ZH} 卡顿"]
    for kol in BILIBILI_KOLS:
        keywords.append(f"{kol} {GAME_NAME_ZH}")
    for kw in keywords:
        results.extend(search_bilibili(kw, max_results=5))
        time.sleep(0.3)
    print(f"  → B站找到 {len(results)} 条")
    return results


# ── 平台2：YouTube 官方 API ───────────────────────────────────────────────────
def collect_youtube():
    print("📺 搜索 YouTube...")
    results = []
    published_after = datetime.utcnow() - timedelta(hours=24)
    after_str = published_after.strftime("%Y-%m-%dT%H:%M:%SZ")

    keywords = [GAME_NAME_EN, f"{GAME_NAME_EN} game",
                f"{GAME_NAME_EN} review", f"{GAME_NAME_EN} gameplay",
                f"{GAME_NAME_EN} crash", f"{GAME_NAME_ZH}"]
    for kw in keywords:
        params = urllib.parse.urlencode({
            "part": "snippet", "q": kw, "type": "video",
            "order": "date", "publishedAfter": after_str,
            "maxResults": 10, "key": YOUTUBE_API_KEY,
        })
        data = fetch_url(f"https://www.googleapis.com/youtube/v3/search?{params}", headers={
            "User-Agent": "Mozilla/5.0"
        })
        if not data:
            continue
        for item in data.get("items", []):
            vid_id = item.get("id", {}).get("videoId", "")
            snip = item.get("snippet", {})
            if not vid_id:
                continue
            results.append({
                "title": snip.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid_id}",
                "body": snip.get("description", ""),
                "author": snip.get("channelTitle", ""),
                "pub_time": snip.get("publishedAt", "")[:16].replace("T", " "),
                "platform": "YouTube",
                "query": kw,
            })
        time.sleep(0.3)
    print(f"  → YouTube找到 {len(results)} 条")
    return results


# ── 平台3：小黑盒公开接口 ─────────────────────────────────────────────────────
def collect_xiaoheihe():
    print("🎮 搜索 小黑盒...")
    results = []
    params = urllib.parse.urlencode({
        "keywords": GAME_NAME_ZH, "page": 1, "pageSize": 20,
    })
    data = fetch_url(
        f"https://api.xiaoheihe.cn/bbs/app/api/general/search/v1?{params}",
        headers={
            "User-Agent": "Mozilla/5.0",
            "heybox-app": "1",
        }
    )
    if data and data.get("status") == "ok":
        items = data.get("result", {}).get("items", []) or []
        for item in items[:20]:
            created = item.get("created_at", 0)
            if isinstance(created, str):
                try:
                    created = int(datetime.strptime(created, "%Y-%m-%d %H:%M:%S").timestamp())
                except:
                    created = 0
            if NOW_TS - created <= DAY_SECONDS:
                post_id = item.get("id", "")
                results.append({
                    "title": item.get("title", ""),
                    "url": f"https://www.xiaoheihe.cn/community/thread/{post_id}" if post_id else "https://www.xiaoheihe.cn",
                    "body": item.get("content", "")[:300],
                    "author": item.get("author", {}).get("nickname", "") if isinstance(item.get("author"), dict) else "",
                    "pub_time": datetime.fromtimestamp(created, tz=CST).strftime("%m-%d %H:%M") if created else "",
                    "platform": "小黑盒",
                    "query": GAME_NAME_ZH,
                })
    print(f"  → 小黑盒找到 {len(results)} 条")
    return results


# ── 平台4：DuckDuckGo 覆盖其余平台 ───────────────────────────────────────────
def search_ddg(query, max_results=5):
    try:
        with DDGS() as ddgs:
            return list(ddgs.text(query, timelimit="d", max_results=max_results, safesearch="off"))
    except Exception as e:
        print(f"  ⚠️ DDG失败 [{query[:40]}]: {e}")
        return []


def collect_ddg():
    print("🔍 搜索 其他平台 (DDG)...")
    queries = [
        f"{GAME_NAME_EN} crash bug site:store.steampowered.com OR site:steamcommunity.com",
        f"{GAME_NAME_EN} negative review reddit",
        f"{GAME_NAME_EN} tiktok",
        f"{GAME_NAME_ZH} 小红书",
        f"{GAME_NAME_ZH} 差评 微博",
        f"{GAME_NAME_ZH} NGA 问题",
        f"{GAME_NAME_ZH} taptap 差评",
        f"{GAME_NAME_EN} twitter complaints",
    ]
    results = []
    for q in queries:
        for r in search_ddg(q):
            # 判断平台
            url = r.get("href", "")
            platform = "其他"
            if "steampowered.com" in url or "steamcommunity.com" in url:
                platform = "Steam"
            elif "reddit.com" in url:
                platform = "Reddit"
            elif "tiktok.com" in url:
                platform = "TikTok"
            elif "xiaohongshu.com" in url or "xhs" in url:
                platform = "小红书"
            elif "weibo.com" in url:
                platform = "微博"
            elif "nga.cn" in url:
                platform = "NGA"
            elif "taptap.com" in url or "taptap.cn" in url:
                platform = "TapTap"
            elif "twitter.com" in url or "x.com" in url:
                platform = "Twitter/X"
            results.append({
                "title": r.get("title", ""),
                "url": url,
                "body": r.get("body", ""),
                "author": "",
                "pub_time": "24h内",
                "platform": platform,
                "query": q,
            })
        time.sleep(0.2)
    print(f"  → 其他平台找到 {len(results)} 条")
    return results


# ── 汇总所有平台 ──────────────────────────────────────────────────────────────
def collect_all():
    all_results = []
    all_results.extend(collect_bilibili())
    all_results.extend(collect_youtube())
    all_results.extend(collect_xiaoheihe())
    all_results.extend(collect_ddg())

    # 去重
    seen, unique = set(), []
    for r in all_results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    print(f"\n✅ 全平台汇总：{len(unique)} 条唯一结果")
    platform_counts = {}
    for r in unique:
        p = r.get("platform", "其他")
        platform_counts[p] = platform_counts.get(p, 0) + 1
    for p, c in sorted(platform_counts.items(), key=lambda x: -x[1]):
        print(f"   {p}: {c} 条")
    return unique


# ── DeepSeek 分析 TOP10 ───────────────────────────────────────────────────────
def analyze_top10(raw_results):
    kol_names = "、".join(BILIBILI_KOLS)
    results_text = "\n\n".join([
        f"[{i+1}] 平台：{r.get('platform','')} | 时间：{r.get('pub_time','')}\n"
        f"标题：{r['title']}\n链接：{r['url']}\n"
        f"作者：{r.get('author','')}\n内容：{r['body'][:300]}"
        for i, r in enumerate(raw_results[:80])
    ])

    prompt = f"""
你是游戏舆情分析师，分析《{GAME_NAME_ZH}》（{GAME_NAME_EN}）过去24小时内玩家负面反馈。
今天是 {REPORT_DATE}（北京时间）。

合作主播名单（如内容来自这些主播请标注）：{kol_names}

从以下搜索结果中：
1. 只保留与《{GAME_NAME_ZH}》或《{GAME_NAME_EN}》明确相关的负面内容
2. 按发布时间从新到旧排序（rank 1 = 最新）
3. 优先选择有玩家原话、有链接、问题严重的
4. 必须保留原文链接

选出TOP10负面评价，严格输出JSON，不要有任何其他内容：

{{
  "top10": [
    {{
      "rank": 1,
      "platform": "平台名",
      "is_kol": false,
      "kol_name": null,
      "issue_type": "游戏崩溃/帧率问题/卡顿/加载问题/存档丢失/其他bug/综合差评",
      "severity": "严重/中等/轻微",
      "original_quote": "玩家原话，尽量完整",
      "summary": "一句话总结核心问题",
      "url": "原文链接（必填）",
      "pub_time": "发布时间",
      "time_verified": "24h内确认/时间未确认"
    }}
  ],
  "total_negative_found": 0,
  "platform_coverage": ["B站", "YouTube", "小黑盒", "Steam", "Reddit"],
  "data_note": "数据质量说明"
}}

搜索结果：
{results_text}
"""

    print("🤖 分析提取TOP10...")
    resp = client.chat.completions.create(
        model="deepseek-chat", max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()

    try:
        data = json.loads(text)
        return data.get("top10", []), {
            "total": data.get("total_negative_found", 0),
            "coverage": data.get("platform_coverage", []),
            "note": data.get("data_note", ""),
        }
    except:
        s, e = text.find("{"), text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                data = json.loads(text[s:e])
                return data.get("top10", []), {"total": 0, "coverage": [], "note": "部分解析"}
            except:
                pass
        return [], {"total": 0, "coverage": [], "note": "解析失败"}


# ── 构建 HTML 邮件 ────────────────────────────────────────────────────────────
def build_html(top10, meta):
    sev_styles = {
        "严重": ("#dc2626", "#fef2f2", "#fca5a5"),
        "中等": ("#ea580c", "#fff7ed", "#fed7aa"),
        "轻微": ("#ca8a04", "#fefce8", "#fde68a"),
    }
    issue_icons = {
        "游戏崩溃": "💥", "帧率问题": "📉", "卡顿": "⚡",
        "加载问题": "⏳", "存档丢失": "💾", "其他bug": "🐛", "综合差评": "👎",
    }
    platform_icons = {
        "B站": "🎬", "YouTube": "📺", "小黑盒": "🎮", "Steam": "🕹️",
        "Reddit": "🤖", "TikTok": "🎵", "小红书": "📕",
        "微博": "🔵", "NGA": "🗣️", "TapTap": "📱", "Twitter/X": "🐦",
    }

    coverage_tags = "".join(
        f'<span style="display:inline-block;background:#e0f2fe;color:#0369a1;font-size:11px;padding:2px 8px;border-radius:10px;margin:2px;">{p}</span>'
        for p in meta.get("coverage", [])
    )

    cards = ""
    for item in top10:
        rank = item.get("rank", 0)
        sev = item.get("severity", "中等")
        tc, bg, bc = sev_styles.get(sev, ("#6b7280", "#f9fafb", "#e5e7eb"))
        itype = item.get("issue_type", "其他")
        iicon = issue_icons.get(itype, "⚠️")
        url = item.get("url", "")
        tv = item.get("time_verified", "时间未确认")
        tbg = "#f0fdf4" if tv == "24h内确认" else "#f9fafb"
        tc2 = "#16a34a" if tv == "24h内确认" else "#6b7280"
        ti = "✅" if tv == "24h内确认" else "⚠️"
        platform = item.get("platform", "")
        picon = platform_icons.get(platform, "📌")
        kol_badge = f'<span style="background:#7c3aed;color:#fff;font-size:10px;padding:2px 8px;border-radius:10px;margin-left:4px;">⭐ {item.get("kol_name","")}</span>' if item.get("is_kol") and item.get("kol_name") else ""
        link = f'<a href="{url}" target="_blank" style="display:inline-block;background:#1d4ed8;color:#fff;font-size:12px;padding:5px 14px;border-radius:6px;text-decoration:none;">🔗 查看原文</a>' if url else '<span style="font-size:12px;color:#9ca3af;">暂无链接</span>'
        pub = item.get("pub_time", "")

        cards += f"""
        <div style="background:{bg};border:1px solid {bc};border-left:4px solid {tc};border-radius:10px;padding:16px 18px;margin-bottom:14px;">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:10px;">
            <span style="background:{tc};color:#fff;font-size:13px;font-weight:700;width:26px;height:26px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;">{rank}</span>
            <span style="background:#1e293b;color:#fff;font-size:11px;padding:2px 8px;border-radius:10px;">{picon} {platform}</span>
            <span style="color:{tc};border:1px solid {bc};font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600;">{iicon} {itype} · {sev}</span>
            <span style="background:{tbg};color:{tc2};font-size:10px;padding:2px 8px;border-radius:10px;">{ti} {tv}</span>
            {kol_badge}
          </div>
          <div style="font-size:14px;font-weight:600;color:#111827;margin-bottom:8px;">{item.get("summary","")}</div>
          <blockquote style="margin:0 0 10px;padding:10px 14px;background:rgba(255,255,255,0.7);border-left:3px solid {tc};border-radius:0 6px 6px 0;font-size:13px;color:#374151;line-height:1.6;">"{item.get("original_quote","暂无原话")}"</blockquote>
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <span style="font-size:11px;color:#6b7280;">🕐 {pub}</span>
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
        <div style="font-size:18px;font-weight:700;">{meta.get("total",0)} 条</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">数据范围</div>
        <div style="font-size:13px;font-weight:600;">过去 24 小时</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">覆盖平台</div>
        <div style="font-size:13px;font-weight:600;">B站·YouTube·小黑盒·更多</div>
      </div>
    </div>
  </div>

  <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:12px;color:#0369a1;">
    📡 已覆盖平台：{coverage_tags or "数据收集中"}｜✅ 已过滤24h内内容，按时间从新到旧排序
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 16px;font-size:15px;color:#1e293b;">🔥 TOP10 负面评价（含原文链接）</h2>
    {cards}
  </div>

  <div style="text-align:center;color:#94a3b8;font-size:11px;padding-bottom:12px;">
    Infini Fun 舆情监控 · {REPORT_DATE} 08:00 CST<br>
    B站官方API · YouTube官方API · 小黑盒 · Steam · Reddit · TikTok · 小红书 · 微博 · NGA · TapTap<br>
    点击「查看原文」直达原始评论
  </div>

</div>
</body>
</html>"""


# ── 发送邮件 ──────────────────────────────────────────────────────────────────
def send_gmail(html_body, top10):
    severe = sum(1 for x in top10 if x.get("severity") == "严重")
    tag = f" 🚨 {severe}条严重" if severe else ""
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
        recipients = [r.strip() for r in RECIPIENT_EMAIL.split(",")]
        s.sendmail(SENDER_EMAIL, recipients, msg.as_bytes())
    print("✅ 发送成功！")


# ── 主函数 ────────────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}\n  忆蚀 24h负面舆情简报\n  {REPORT_DATE}\n{'='*60}\n")
    raw = collect_all()
    top10, meta = analyze_top10(raw)
    html = build_html(top10, meta)
    send_gmail(html, top10)
    print(f"\n✅ 完成！共 {len(top10)} 条负面评价")
    severe = [x for x in top10 if x.get("severity") == "严重"]
    if severe:
        print(f"   ⚠️ 严重问题 {len(severe)} 条，请重点关注")


if __name__ == "__main__":
    main()
