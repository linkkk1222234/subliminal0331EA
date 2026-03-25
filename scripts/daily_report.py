#!/usr/bin/env python3
"""
忆蚀 Subliminal 24h玩家反馈洞察简报
全维度分析：好评亮点 / 差评痛点 / 性能问题 / 功能建议 / 热议话题
平台：B站(官方API) + YouTube(官方API) + 小黑盒 + 其余平台(DuckDuckGo)
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
DAY_SECONDS = 86400

client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")


def fetch_url(url, headers=None, timeout=10):
    try:
        req = urllib.request.Request(url, headers=headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️ 请求失败: {e}")
        return None


def collect_bilibili():
    print("🎬 搜索 B站...")
    results = []
    keywords = [
        GAME_NAME_ZH, GAME_NAME_EN,
        f"{GAME_NAME_ZH} 评测", f"{GAME_NAME_ZH} 游戏",
        f"{GAME_NAME_ZH} 好评", f"{GAME_NAME_ZH} 差评",
        f"{GAME_NAME_ZH} 崩溃", f"{GAME_NAME_ZH} 卡顿",
        f"{GAME_NAME_ZH} 剧情", f"{GAME_NAME_ZH} 画面",
    ]
    for kol in BILIBILI_KOLS:
        keywords.append(f"{kol} {GAME_NAME_ZH}")

    for kw in keywords:
        try:
            params = urllib.parse.urlencode({
                "keyword": kw, "search_type": "video",
                "order": "pubdate", "page": 1,
            })
            data = fetch_url(f"https://api.bilibili.com/x/web-interface/search/type?{params}")
            if not data:
                continue
            for item in (data.get("data", {}).get("result", []) or [])[:5]:
                pub_ts = item.get("pubdate", 0)
                if NOW_TS - pub_ts <= DAY_SECONDS:
                    title = item.get("title","").replace('<em class="keyword">','').replace('</em>','')
                    results.append({
                        "title": title,
                        "url": f"https://www.bilibili.com/video/{item.get('bvid','')}",
                        "body": item.get("description","") or item.get("tag",""),
                        "author": item.get("author",""),
                        "pub_time": datetime.fromtimestamp(pub_ts, tz=CST).strftime("%m-%d %H:%M"),
                        "platform": "B站",
                        "is_kol": any(kol in kw for kol in BILIBILI_KOLS),
                        "kol_name": next((kol for kol in BILIBILI_KOLS if kol in kw), None),
                    })
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ B站搜索失败 [{kw}]: {e}")

    print(f"  → B站找到 {len(results)} 条")
    return results


def collect_youtube():
    print("📺 搜索 YouTube...")
    results = []
    after = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    keywords = [
        GAME_NAME_EN, f"{GAME_NAME_EN} game",
        f"{GAME_NAME_EN} review", f"{GAME_NAME_EN} gameplay",
        f"{GAME_NAME_EN} horror", f"{GAME_NAME_ZH}",
    ]
    for kw in keywords:
        try:
            params = urllib.parse.urlencode({
                "part": "snippet", "q": kw, "type": "video",
                "order": "date", "publishedAfter": after,
                "maxResults": 10, "key": YOUTUBE_API_KEY,
            })
            data = fetch_url(f"https://www.googleapis.com/youtube/v3/search?{params}",
                           headers={"User-Agent": "Mozilla/5.0"})
            if not data:
                continue
            for item in data.get("items", []):
                vid_id = item.get("id", {}).get("videoId", "")
                snip = item.get("snippet", {})
                if vid_id:
                    results.append({
                        "title": snip.get("title", ""),
                        "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "body": snip.get("description", ""),
                        "author": snip.get("channelTitle", ""),
                        "pub_time": snip.get("publishedAt","")[:16].replace("T"," "),
                        "platform": "YouTube",
                        "is_kol": False, "kol_name": None,
                    })
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ YouTube搜索失败 [{kw}]: {e}")

    print(f"  → YouTube找到 {len(results)} 条")
    return results


def collect_xiaoheihe():
    print("🎮 搜索 小黑盒...")
    results = []
    try:
        params = urllib.parse.urlencode({"keywords": GAME_NAME_ZH, "page": 1, "pageSize": 20})
        data = fetch_url(
            f"https://api.xiaoheihe.cn/bbs/app/api/general/search/v1?{params}",
            headers={"User-Agent": "Mozilla/5.0", "heybox-app": "1"}
        )
        if data and data.get("status") == "ok":
            for item in (data.get("result", {}).get("items", []) or [])[:20]:
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
                        "is_kol": False, "kol_name": None,
                    })
    except Exception as e:
        print(f"  ⚠️ 小黑盒失败: {e}")
    print(f"  → 小黑盒找到 {len(results)} 条")
    return results


def collect_ddg():
    print("🔍 搜索 其他平台...")
    queries = [
        f"{GAME_NAME_EN} steam review",
        f"{GAME_NAME_EN} reddit discussion",
        f"{GAME_NAME_EN} tiktok",
        f"{GAME_NAME_ZH} 小红书 评价",
        f"{GAME_NAME_ZH} 微博 评价",
        f"{GAME_NAME_ZH} NGA",
        f"{GAME_NAME_ZH} taptap 评价",
        f"{GAME_NAME_EN} twitter review",
        f"{GAME_NAME_ZH} 评测",
        f"{GAME_NAME_EN} game feedback",
    ]
    results = []
    platform_map = {
        "steampowered.com": "Steam", "steamcommunity.com": "Steam",
        "reddit.com": "Reddit", "tiktok.com": "TikTok",
        "xiaohongshu.com": "小红书", "weibo.com": "微博",
        "nga.cn": "NGA", "taptap.com": "TapTap", "taptap.cn": "TapTap",
        "twitter.com": "Twitter/X", "x.com": "Twitter/X",
    }
    try:
        for q in queries:
            with DDGS() as ddgs:
                for r in ddgs.text(q, timelimit="d", max_results=5, safesearch="off"):
                    url = r.get("href", "")
                    platform = next((v for k, v in platform_map.items() if k in url), "其他")
                    results.append({
                        "title": r.get("title", ""),
                        "url": url,
                        "body": r.get("body", ""),
                        "author": "",
                        "pub_time": "24h内",
                        "platform": platform,
                        "is_kol": False, "kol_name": None,
                    })
            time.sleep(0.2)
    except Exception as e:
        print(f"  ⚠️ DDG失败: {e}")
    print(f"  → 其他平台找到 {len(results)} 条")
    return results


def collect_all():
    all_results = []
    all_results.extend(collect_bilibili())
    all_results.extend(collect_youtube())
    all_results.extend(collect_xiaoheihe())
    all_results.extend(collect_ddg())
    seen, unique = set(), []
    for r in all_results:
        if r["url"] and r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)
    print(f"\n✅ 全平台汇总：{len(unique)} 条唯一结果")
    return unique


def analyze_insights(raw_results):
    kol_names = "、".join(BILIBILI_KOLS)
    results_text = "\n\n".join([
        f"[{i+1}] 平台：{r.get('platform','')} | 时间：{r.get('pub_time','')} | 作者：{r.get('author','')}\n"
        f"标题：{r['title']}\n链接：{r['url']}\n内容：{r['body'][:300]}"
        for i, r in enumerate(raw_results[:80])
    ])

    prompt = f"""
你是资深游戏发行商舆情分析师，分析《{GAME_NAME_ZH}》（{GAME_NAME_EN}）过去24小时内玩家反馈。
今天是 {REPORT_DATE}（北京时间）。
合作主播名单：{kol_names}

请从搜索结果中提取玩家反馈洞察，按以下维度分析，每个维度找3-5条最有代表性的内容，必须保留原文链接。

严格输出以下JSON，不要有任何其他内容：

{{
  "total_found": 搜索到的总条数,
  "platform_coverage": ["覆盖的平台列表"],
  "data_note": "数据说明",

  "hot_topics": [
    {{
      "topic": "热议话题名称",
      "summary": "话题概述",
      "sentiment": "正面/负面/中立/混合",
      "mention_count": 提及次数估算,
      "representative_url": "最具代表性的链接",
      "platform": "来自哪个平台"
    }}
  ],

  "positive_highlights": [
    {{
      "aspect": "好评维度（如：剧情/画面/音乐/氛围/玩法等）",
      "quote": "玩家原话",
      "url": "原文链接",
      "platform": "平台",
      "pub_time": "发布时间",
      "is_kol": false,
      "kol_name": null
    }}
  ],

  "pain_points": [
    {{
      "aspect": "差评维度（如：性能/价格/内容量/难度/汉化等）",
      "severity": "严重/中等/轻微",
      "quote": "玩家原话",
      "url": "原文链接",
      "platform": "平台",
      "pub_time": "发布时间",
      "is_kol": false,
      "kol_name": null
    }}
  ],

  "performance_issues": [
    {{
      "type": "问题类型（崩溃/帧率/卡顿/加载/黑屏等）",
      "severity": "严重/中等/轻微",
      "quote": "玩家原话",
      "url": "原文链接",
      "platform": "平台",
      "pub_time": "发布时间"
    }}
  ],

  "suggestions": [
    {{
      "content": "玩家建议内容",
      "url": "原文链接",
      "platform": "平台"
    }}
  ],

  "kol_activity": [
    {{
      "kol_name": "主播名",
      "platform": "bilibili",
      "content_summary": "发布内容概述",
      "sentiment": "正面/负面/中立",
      "url": "视频链接",
      "pub_time": "发布时间"
    }}
  ],

  "action_items": [
    {{
      "priority": "P0紧急/P1高/P2中/P3低",
      "content": "具体建议",
      "owner": "开发团队/市场团队/客服/KOL运营"
    }}
  ]
}}

搜索结果：
{results_text}
"""

    print("🤖 分析玩家反馈洞察...")
    resp = client.chat.completions.create(
        model="deepseek-chat", max_tokens=5000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(text)
    except:
        s, e = text.find("{"), text.rfind("}") + 1
        if s != -1 and e > s:
            try:
                return json.loads(text[s:e])
            except:
                pass
    return {}


def build_html(data):
    platform_icons = {
        "B站":"🎬","YouTube":"📺","小黑盒":"🎮","Steam":"🕹️",
        "Reddit":"🤖","TikTok":"🎵","小红书":"📕",
        "微博":"🔵","NGA":"🗣️","TapTap":"📱","Twitter/X":"🐦","其他":"📌"
    }
    sev_colors = {"严重":"#dc2626","中等":"#ea580c","轻微":"#ca8a04"}
    sent_colors = {"正面":"#16a34a","负面":"#dc2626","中立":"#6b7280","混合":"#7c3aed"}
    priority_styles = {
        "P0紧急":("🚨","#dc2626","#fef2f2"),
        "P1高":("🔴","#ea580c","#fff7ed"),
        "P2中":("🟡","#ca8a04","#fefce8"),
        "P3低":("🟢","#16a34a","#f0fdf4"),
    }

    def link_btn(url, label="🔗 查看原文"):
        if url:
            return f'<a href="{url}" target="_blank" style="display:inline-block;background:#1d4ed8;color:#fff;font-size:11px;padding:4px 10px;border-radius:5px;text-decoration:none;white-space:nowrap;">{label}</a>'
        return ''

    def platform_tag(p):
        icon = platform_icons.get(p, "📌")
        return f'<span style="background:#1e293b;color:#fff;font-size:10px;padding:1px 6px;border-radius:8px;">{icon} {p}</span>'

    def kol_tag(is_kol, name):
        if is_kol and name:
            return f'<span style="background:#7c3aed;color:#fff;font-size:10px;padding:1px 6px;border-radius:8px;margin-left:3px;">⭐ {name}</span>'
        return ''

    def time_tag(t):
        if t:
            return f'<span style="font-size:10px;color:#94a3b8;">🕐 {t}</span>'
        return ''

    # ── 热议话题 ──
    hot_html = ""
    for t in (data.get("hot_topics") or [])[:5]:
        sc = sent_colors.get(t.get("sentiment","中立"), "#6b7280")
        hot_html += f"""
        <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #f1f5f9;">
          <span style="background:{sc};color:#fff;font-size:10px;padding:2px 7px;border-radius:10px;white-space:nowrap;margin-top:2px;">{t.get("sentiment","")}</span>
          <div style="flex:1;">
            <div style="font-size:13px;font-weight:600;color:#111827;">{t.get("topic","")}</div>
            <div style="font-size:12px;color:#475569;margin-top:2px;">{t.get("summary","")}</div>
            <div style="display:flex;align-items:center;gap:6px;margin-top:5px;flex-wrap:wrap;">
              {platform_tag(t.get("platform",""))}
              {link_btn(t.get("representative_url",""))}
            </div>
          </div>
        </div>"""
    if not hot_html:
        hot_html = '<div style="color:#9ca3af;font-size:13px;padding:10px 0;">暂无热议话题数据</div>'

    # ── 好评亮点 ──
    pos_html = ""
    for p in (data.get("positive_highlights") or [])[:5]:
        pos_html += f"""
        <div style="border-left:3px solid #16a34a;padding:10px 14px;margin-bottom:8px;background:#f0fdf4;border-radius:0 8px 8px 0;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;flex-wrap:wrap;">
            <span style="background:#16a34a;color:#fff;font-size:11px;padding:1px 8px;border-radius:10px;font-weight:600;">{p.get("aspect","")}</span>
            {platform_tag(p.get("platform",""))}
            {kol_tag(p.get("is_kol"), p.get("kol_name"))}
            {time_tag(p.get("pub_time",""))}
          </div>
          <div style="font-size:13px;color:#166534;font-style:italic;margin-bottom:6px;">"{p.get("quote","")}"</div>
          {link_btn(p.get("url",""))}
        </div>"""
    if not pos_html:
        pos_html = '<div style="color:#9ca3af;font-size:13px;padding:10px;">暂无好评数据</div>'

    # ── 差评痛点 ──
    pain_html = ""
    for p in (data.get("pain_points") or [])[:5]:
        sc = sev_colors.get(p.get("severity","轻微"), "#ca8a04")
        pain_html += f"""
        <div style="border-left:3px solid {sc};padding:10px 14px;margin-bottom:8px;background:#fafafa;border-radius:0 8px 8px 0;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;flex-wrap:wrap;">
            <span style="background:{sc};color:#fff;font-size:11px;padding:1px 8px;border-radius:10px;font-weight:600;">{p.get("aspect","")}</span>
            <span style="color:{sc};font-size:10px;border:1px solid {sc};padding:1px 6px;border-radius:8px;">{p.get("severity","")}</span>
            {platform_tag(p.get("platform",""))}
            {kol_tag(p.get("is_kol"), p.get("kol_name"))}
            {time_tag(p.get("pub_time",""))}
          </div>
          <div style="font-size:13px;color:#374151;font-style:italic;margin-bottom:6px;">"{p.get("quote","")}"</div>
          {link_btn(p.get("url",""))}
        </div>"""
    if not pain_html:
        pain_html = '<div style="color:#9ca3af;font-size:13px;padding:10px;">暂无差评数据</div>'

    # ── 性能问题 ──
    perf_html = ""
    for p in (data.get("performance_issues") or [])[:5]:
        sc = sev_colors.get(p.get("severity","轻微"), "#ca8a04")
        perf_html += f"""
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-left:3px solid {sc};border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;flex-wrap:wrap;">
            <span style="background:{sc};color:#fff;font-size:11px;padding:1px 8px;border-radius:10px;font-weight:600;">⚡ {p.get("type","")}</span>
            <span style="color:{sc};font-size:10px;border:1px solid {sc};padding:1px 6px;border-radius:8px;">{p.get("severity","")}</span>
            {platform_tag(p.get("platform",""))}
            {time_tag(p.get("pub_time",""))}
          </div>
          <div style="font-size:13px;color:#374151;font-style:italic;margin-bottom:6px;">"{p.get("quote","")}"</div>
          {link_btn(p.get("url",""))}
        </div>"""
    if not perf_html:
        perf_html = '<div style="color:#16a34a;font-size:13px;padding:10px;background:#f0fdf4;border-radius:8px;">✅ 过去24小时内未发现明显性能投诉</div>'

    # ── 合作主播动态 ──
    kol_html = ""
    for k in (data.get("kol_activity") or [])[:6]:
        sc = sent_colors.get(k.get("sentiment","中立"), "#6b7280")
        kol_html += f"""
        <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #f1f5f9;">
          <span style="background:{sc};color:#fff;font-size:10px;padding:2px 7px;border-radius:10px;white-space:nowrap;margin-top:2px;">{k.get("sentiment","")}</span>
          <div style="flex:1;">
            <div style="font-size:13px;font-weight:600;color:#111827;">⭐ {k.get("kol_name","")}</div>
            <div style="font-size:12px;color:#475569;margin-top:2px;">{k.get("content_summary","")}</div>
            <div style="display:flex;align-items:center;gap:6px;margin-top:5px;flex-wrap:wrap;">
              {time_tag(k.get("pub_time",""))}
              {link_btn(k.get("url",""), "🔗 查看视频")}
            </div>
          </div>
        </div>"""
    if not kol_html:
        kol_html = '<div style="color:#9ca3af;font-size:13px;padding:10px 0;">过去24小时内合作主播暂无相关内容</div>'

    # ── 玩家建议 ──
    sug_html = ""
    for s in (data.get("suggestions") or [])[:4]:
        sug_html += f"""
        <div style="display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:#f8fafc;border-radius:6px;margin-bottom:6px;gap:10px;">
          <div style="font-size:13px;color:#374151;flex:1;">{s.get("content","")}</div>
          <div style="display:flex;align-items:center;gap:6px;flex-shrink:0;">
            {platform_tag(s.get("platform",""))}
            {link_btn(s.get("url",""))}
          </div>
        </div>"""
    if not sug_html:
        sug_html = '<div style="color:#9ca3af;font-size:13px;">暂无玩家建议</div>'

    # ── 行动建议 ──
    action_html = ""
    for a in (data.get("action_items") or []):
        p = a.get("priority","P3低")
        icon, color, bg = priority_styles.get(p, ("⚪","#6b7280","#f9fafb"))
        action_html += f"""
        <tr>
          <td style="padding:8px 12px;font-size:12px;font-weight:700;color:{color};background:{bg};white-space:nowrap;">{icon} {p}</td>
          <td style="padding:8px 12px;font-size:13px;color:#111827;">{a.get("content","")}</td>
          <td style="padding:8px 12px;font-size:12px;color:#6b7280;white-space:nowrap;">{a.get("owner","")}</td>
        </tr>"""
    if not action_html:
        action_html = '<tr><td colspan="3" style="padding:12px;text-align:center;color:#9ca3af;font-size:13px;">暂无行动建议</td></tr>'

    coverage = "、".join(data.get("platform_coverage") or [])
    total = data.get("total_found", 0)
    note = data.get("data_note", "")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:20px 16px;">

  <div style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#4338ca 100%);border-radius:14px;padding:26px 30px;margin-bottom:16px;color:#fff;">
    <div style="font-size:11px;opacity:0.7;margin-bottom:4px;letter-spacing:1px;">INFINI FUN · 玩家反馈洞察</div>
    <div style="font-size:22px;font-weight:700;margin-bottom:4px;">《忆蚀 Subliminal》</div>
    <div style="font-size:13px;opacity:0.85;">24h玩家反馈洞察简报 · {REPORT_DATE}</div>
    <div style="margin-top:14px;display:flex;gap:10px;flex-wrap:wrap;">
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">收集内容</div>
        <div style="font-size:18px;font-weight:700;">{total} 条</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">数据范围</div>
        <div style="font-size:13px;font-weight:600;">过去 24 小时</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:7px 14px;">
        <div style="font-size:10px;opacity:0.7;">覆盖平台</div>
        <div style="font-size:12px;font-weight:600;">{coverage or "多平台"}</div>
      </div>
    </div>
  </div>

  <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:10px 16px;margin-bottom:16px;font-size:12px;color:#0369a1;">
    📊 {note}
  </div>

  <!-- 热议话题 -->
  <div style="background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:14px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">🔥 热议话题</h2>
    {hot_html}
  </div>

  <!-- 好评亮点 + 差评痛点 -->
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px;">
    <div style="background:#fff;border-radius:12px;padding:18px 16px;border:1px solid #e2e8f0;">
      <h2 style="margin:0 0 12px;font-size:14px;color:#166534;">👍 好评亮点</h2>
      {pos_html}
    </div>
    <div style="background:#fff;border-radius:12px;padding:18px 16px;border:1px solid #e2e8f0;">
      <h2 style="margin:0 0 12px;font-size:14px;color:#991b1b;">👎 差评痛点</h2>
      {pain_html}
    </div>
  </div>

  <!-- 性能问题 -->
  <div style="background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:14px;border:2px solid #ea580c;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">⚡ 性能 & 技术问题</h2>
    {perf_html}
  </div>

  <!-- 合作主播动态 -->
  <div style="background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:14px;border:2px solid #7c3aed;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">⭐ B站合作主播动态</h2>
    {kol_html}
  </div>

  <!-- 玩家建议 -->
  <div style="background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:14px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">💡 玩家建议</h2>
    {sug_html}
  </div>

  <!-- 行动建议 -->
  <div style="background:#fff;border-radius:12px;padding:18px 20px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">✅ 行动建议</h2>
    <table style="width:100%;border-collapse:collapse;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
      <thead><tr style="background:#f8fafc;">
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0;">优先级</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0;">建议</th>
        <th style="padding:8px 12px;text-align:left;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0;">负责方</th>
      </tr></thead>
      <tbody>{action_html}</tbody>
    </table>
  </div>

  <div style="text-align:center;color:#94a3b8;font-size:11px;padding-bottom:12px;">
    Infini Fun 舆情监控 · {REPORT_DATE} 08:00 CST<br>
    B站官方API · YouTube官方API · 小黑盒 · Steam · Reddit · TikTok · 小红书 · 微博 · NGA · TapTap<br>
    点击各条目「查看原文」直达原始内容
  </div>

</div>
</body>
</html>"""


def send_gmail(html_body, data):
    hot = data.get("hot_topics") or []
    perfs = data.get("performance_issues") or []
    severe = sum(1 for p in perfs if p.get("severity") == "严重")
    tag = f" 🚨 {severe}条严重性能问题" if severe else ""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【忆蚀-{REPORT_DATE_SHORT}-24h玩家反馈洞察】{tag}"
    msg["From"]    = f"忆蚀舆情监控 <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL
    plain = f"忆蚀 24h玩家反馈洞察 {REPORT_DATE}\n\n"
    for t in hot[:3]:
        plain += f"热议：{t.get('topic','')} - {t.get('summary','')}\n"
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))
    print("📧 发送中...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        recipients = [r.strip() for r in RECIPIENT_EMAIL.split(",")]
        s.sendmail(SENDER_EMAIL, recipients, msg.as_bytes())
    print("✅ 发送成功！")


def main():
    print(f"\n{'='*60}\n  忆蚀 24h玩家反馈洞察简报\n  {REPORT_DATE}\n{'='*60}\n")
    raw = collect_all()
    data = analyze_insights(raw)
    html = build_html(data)
    send_gmail(html, data)
    print("\n✅ 完成！")


if __name__ == "__main__":
    main()
