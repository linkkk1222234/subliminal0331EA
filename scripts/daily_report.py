#!/usr/bin/env python3
"""忆蚀 Subliminal 24h玩家反馈洞察简报 - 重设计版"""

import os, json, time, smtplib, urllib.request, urllib.parse
from openai import OpenAI
from duckduckgo_search import DDGS
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GAME_NAME_ZH = "忆蚀"
GAME_NAME_EN = "Subliminal"
PUBLISHER = "Infini Fun"
LOGO_B64 = "data:image/png;base64,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"

BILIBILI_KOLS = [
    "与山","友利奈绪大魔王","陈子墨大喇叭","坂本叔","阿虚-Kurv","半支烟",
    "Yommyko","虚构的野心","攸米Youmi","糯米SnuomiQ","秃头荷莱鹿","模拟小羊owo",
    "米开心6","薯米麻喹","抛瓜大力","天明iii","黑泽久留美","陈三岁",
    "Gluneko","你是nana的小可","屯君SOAP",
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
            params = urllib.parse.urlencode({"keyword": kw, "search_type": "video", "order": "pubdate", "page": 1})
            data = fetch_url(f"https://api.bilibili.com/x/web-interface/search/type?{params}")
            if not data: continue
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
            print(f"  ⚠️ B站失败 [{kw}]: {e}")
    print(f"  → B站找到 {len(results)} 条")
    return results

def collect_youtube():
    print("📺 搜索 YouTube...")
    results = []
    after = (datetime.utcnow() - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for kw in [GAME_NAME_EN, f"{GAME_NAME_EN} game", f"{GAME_NAME_EN} review", f"{GAME_NAME_EN} gameplay", f"{GAME_NAME_ZH}"]:
        try:
            params = urllib.parse.urlencode({"part":"snippet","q":kw,"type":"video","order":"date","publishedAfter":after,"maxResults":10,"key":YOUTUBE_API_KEY})
            data = fetch_url(f"https://www.googleapis.com/youtube/v3/search?{params}", headers={"User-Agent":"Mozilla/5.0"})
            if not data: continue
            for item in data.get("items", []):
                vid_id = item.get("id", {}).get("videoId", "")
                snip = item.get("snippet", {})
                if vid_id:
                    results.append({
                        "title": snip.get("title",""), "url": f"https://www.youtube.com/watch?v={vid_id}",
                        "body": snip.get("description",""), "author": snip.get("channelTitle",""),
                        "pub_time": snip.get("publishedAt","")[:16].replace("T"," "),
                        "platform": "YouTube", "is_kol": False, "kol_name": None,
                    })
            time.sleep(0.3)
        except Exception as e:
            print(f"  ⚠️ YouTube失败: {e}")
    print(f"  → YouTube找到 {len(results)} 条")
    return results

def collect_xiaoheihe():
    print("🎮 搜索 小黑盒...")
    results = []
    try:
        params = urllib.parse.urlencode({"keywords": GAME_NAME_ZH, "page": 1, "pageSize": 20})
        data = fetch_url(f"https://api.xiaoheihe.cn/bbs/app/api/general/search/v1?{params}", headers={"User-Agent":"Mozilla/5.0","heybox-app":"1"})
        if data and data.get("status") == "ok":
            for item in (data.get("result", {}).get("items", []) or [])[:20]:
                created = item.get("created_at", 0)
                if isinstance(created, str):
                    try: created = int(datetime.strptime(created, "%Y-%m-%d %H:%M:%S").timestamp())
                    except: created = 0
                if NOW_TS - created <= DAY_SECONDS:
                    post_id = item.get("id","")
                    results.append({
                        "title": item.get("title",""),
                        "url": f"https://www.xiaoheihe.cn/community/thread/{post_id}" if post_id else "https://www.xiaoheihe.cn",
                        "body": item.get("content","")[:300], "author": "",
                        "pub_time": datetime.fromtimestamp(created, tz=CST).strftime("%m-%d %H:%M") if created else "",
                        "platform": "小黑盒", "is_kol": False, "kol_name": None,
                    })
    except Exception as e:
        print(f"  ⚠️ 小黑盒失败: {e}")
    print(f"  → 小黑盒找到 {len(results)} 条")
    return results

def collect_ddg():
    print("🔍 搜索 其他平台...")
    queries = [
        f"{GAME_NAME_EN} steam review", f"{GAME_NAME_EN} reddit discussion",
        f"{GAME_NAME_EN} tiktok", f"{GAME_NAME_ZH} 小红书 评价",
        f"{GAME_NAME_ZH} 微博 评价", f"{GAME_NAME_ZH} NGA",
        f"{GAME_NAME_ZH} taptap 评价", f"{GAME_NAME_EN} twitter review",
        f"{GAME_NAME_ZH} 评测", f"{GAME_NAME_EN} game feedback",
    ]
    platform_map = {
        "steampowered.com":"Steam","steamcommunity.com":"Steam","reddit.com":"Reddit",
        "tiktok.com":"TikTok","xiaohongshu.com":"小红书","weibo.com":"微博",
        "nga.cn":"NGA","taptap.com":"TapTap","taptap.cn":"TapTap",
        "twitter.com":"Twitter/X","x.com":"Twitter/X",
    }
    results = []
    try:
        for q in queries:
            with DDGS() as ddgs:
                for r in ddgs.text(q, timelimit="d", max_results=5, safesearch="off"):
                    url = r.get("href","")
                    platform = next((v for k,v in platform_map.items() if k in url), "其他")
                    results.append({"title":r.get("title",""),"url":url,"body":r.get("body",""),"author":"","pub_time":"24h内","platform":platform,"is_kol":False,"kol_name":None})
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
            seen.add(r["url"]); unique.append(r)
    print(f"\n✅ 全平台汇总：{len(unique)} 条唯一结果")
    return unique

def analyze_insights(raw_results):
    kol_names = "、".join(BILIBILI_KOLS)
    results_text = "\n\n".join([
        f"[{i+1}] 平台：{r.get('platform','')} | 时间：{r.get('pub_time','')} | 作者：{r.get('author','')}\n标题：{r['title']}\n链接：{r['url']}\n内容：{r['body'][:300]}"
        for i, r in enumerate(raw_results[:80])
    ])
    prompt = f"""
你是资深游戏发行商舆情分析师，分析《{GAME_NAME_ZH}》（{GAME_NAME_EN}）过去24小时内玩家反馈。
今天是 {REPORT_DATE}。合作主播名单：{kol_names}

从搜索结果提取玩家反馈洞察，每个维度找3-5条最具代表性内容，必须保留原文链接。

严格输出JSON，不要任何其他内容：
{{
  "total_found": 总条数,
  "platform_coverage": ["平台列表"],
  "data_note": "数据说明",
  "overall_sentiment": "正面/负面/中立/混合",
  "sentiment_score": 0到100,
  "hot_topics": [
    {{"topic":"话题名","summary":"概述","sentiment":"正面/负面/中立/混合","representative_url":"链接","platform":"平台"}}
  ],
  "positive_highlights": [
    {{"aspect":"好评维度","quote":"玩家原话","url":"链接","platform":"平台","pub_time":"时间","is_kol":false,"kol_name":null}}
  ],
  "pain_points": [
    {{"aspect":"差评维度","severity":"严重/中等/轻微","quote":"玩家原话","url":"链接","platform":"平台","pub_time":"时间","is_kol":false,"kol_name":null}}
  ],
  "performance_issues": [
    {{"type":"问题类型","severity":"严重/中等/轻微","quote":"玩家原话","url":"链接","platform":"平台","pub_time":"时间"}}
  ],
  "suggestions": [
    {{"content":"建议内容","url":"链接","platform":"平台"}}
  ],
  "kol_activity": [
    {{"kol_name":"主播名","content_summary":"内容概述","sentiment":"正面/负面/中立","url":"链接","pub_time":"时间"}}
  ],
  "action_items": [
    {{"priority":"P0紧急/P1高/P2中/P3低","content":"建议","owner":"负责方"}}
  ]
}}

搜索结果：
{results_text}
"""
    print("🤖 分析中...")
    resp = client.chat.completions.create(model="deepseek-chat", max_tokens=5000, messages=[{"role":"user","content":prompt}])
    text = resp.choices[0].message.content.strip().replace("","").strip()
    try: return json.loads(text)
    except:
        s, e = text.find("{"), text.rfind("}") + 1
        if s != -1 and e > s:
            try: return json.loads(text[s:e])
            except: pass
    return {}

def build_html(data):
    # ── 颜色体系 ──
    sev_colors = {"严重": "#E53E3E", "中等": "#DD6B20", "轻微": "#D69E2E"}
    sent_colors = {"正面": "#38A169", "负面": "#E53E3E", "中立": "#718096", "混合": "#805AD5"}
    priority_config = {
        "P0紧急": ("#E53E3E", "#FFF5F5", "🔴"),
        "P1高":   ("#DD6B20", "#FFFAF0", "🟠"),
        "P2中":   ("#D69E2E", "#FFFFF0", "🟡"),
        "P3低":   ("#38A169", "#F0FFF4", "🟢"),
    }
    platform_icons = {
        "B站":"🎬","YouTube":"📺","小黑盒":"🎮","Steam":"🕹️",
        "Reddit":"💬","TikTok":"🎵","小红书":"📕","微博":"🔵",
        "NGA":"🗣️","TapTap":"📱","Twitter/X":"🐦","其他":"📌"
    }

    # ── 工具函数 ──
    def pill(text, color, bg=""):
        bg = bg or color + "18"
        return f'<span style="display:inline-block;background:{bg};color:{color};font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;letter-spacing:0.3px">{text}</span>'

    def platform_pill(p):
        icon = platform_icons.get(p, "📌")
        return f'<span style="display:inline-block;background:#EDF2F7;color:#4A5568;font-size:11px;padding:3px 9px;border-radius:20px;">{icon} {p}</span>'

    def link_btn(url, label="查看原文 →"):
        if not url: return ""
        return f'<a href="{url}" target="_blank" style="display:inline-block;color:#4A5568;font-size:11px;text-decoration:none;border-bottom:1px solid #CBD5E0;padding-bottom:1px;white-space:nowrap;">{label}</a>'

    def quote_block(text, color="#4A5568"):
        return f'<p style="margin:8px 0 0;font-size:13px;color:{color};line-height:1.65;font-style:italic;">"{text}"</p>'

    def section_header(icon, title, color="#1A202C"):
        return f'<h2 style="margin:0 0 16px;font-size:14px;font-weight:700;color:{color};letter-spacing:0.5px;text-transform:uppercase;display:flex;align-items:center;gap:6px;">{icon} <span>{title}</span></h2>'

    # ── 情感分数 ──
    score = data.get("sentiment_score", 50)
    overall = data.get("overall_sentiment", "中立")
    score_color = sent_colors.get(overall, "#718096")
    score_bar = f'<div style="height:4px;background:#E2E8F0;border-radius:2px;margin-top:6px;"><div style="height:4px;width:{score}%;background:{score_color};border-radius:2px;"></div></div>'

    # ── 热议话题 ──
    hot_html = ""
    for i, t in enumerate((data.get("hot_topics") or [])[:5]):
        sc = sent_colors.get(t.get("sentiment","中立"), "#718096")
        hot_html += f"""
        <div style="display:flex;gap:12px;padding:12px 0;{'border-bottom:1px solid #F7FAFC;' if i < 4 else ''}">
          <div style="flex-shrink:0;width:28px;height:28px;background:{sc}18;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;color:{sc};">{i+1}</div>
          <div style="flex:1;min-width:0;">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">
              <span style="font-size:13px;font-weight:600;color:#1A202C;">{t.get("topic","")}</span>
              {pill(t.get("sentiment",""), sc)}
            </div>
            <p style="margin:0 0 6px;font-size:12px;color:#718096;line-height:1.5;">{t.get("summary","")}</p>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
              {platform_pill(t.get("platform",""))}
              {link_btn(t.get("representative_url",""))}
            </div>
          </div>
        </div>"""

    # ── 好评亮点 ──
    pos_html = ""
    for p in (data.get("positive_highlights") or [])[:4]:
        kol = f'<span style="display:inline-block;background:#553C9A18;color:#553C9A;font-size:10px;padding:2px 7px;border-radius:20px;">⭐ {p.get("kol_name","")}</span>' if p.get("is_kol") and p.get("kol_name") else ""
        pos_html += f"""
        <div style="padding:12px;background:#F0FFF4;border-radius:8px;margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">
            {pill(p.get("aspect",""), "#38A169", "#C6F6D5")}
            {platform_pill(p.get("platform",""))}
            {kol}
            <span style="font-size:10px;color:#A0AEC0;">{p.get("pub_time","")}</span>
          </div>
          {quote_block(p.get("quote",""), "#276749")}
          <div style="margin-top:8px;">{link_btn(p.get("url",""))}</div>
        </div>"""
    if not pos_html:
        pos_html = '<p style="color:#A0AEC0;font-size:13px;padding:8px 0;margin:0;">暂无好评数据</p>'

    # ── 差评痛点 ──
    pain_html = ""
    for p in (data.get("pain_points") or [])[:4]:
        sc = sev_colors.get(p.get("severity","轻微"), "#D69E2E")
        kol = f'<span style="display:inline-block;background:#553C9A18;color:#553C9A;font-size:10px;padding:2px 7px;border-radius:20px;">⭐ {p.get("kol_name","")}</span>' if p.get("is_kol") and p.get("kol_name") else ""
        pain_html += f"""
        <div style="padding:12px;background:#FFF5F5;border-radius:8px;margin-bottom:8px;">
          <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">
            {pill(p.get("aspect",""), sc, sc + "18")}
            {pill(p.get("severity",""), sc, sc + "18")}
            {platform_pill(p.get("platform",""))}
            {kol}
            <span style="font-size:10px;color:#A0AEC0;">{p.get("pub_time","")}</span>
          </div>
          {quote_block(p.get("quote",""), "#742A2A")}
          <div style="margin-top:8px;">{link_btn(p.get("url",""))}</div>
        </div>"""
    if not pain_html:
        pain_html = '<p style="color:#A0AEC0;font-size:13px;padding:8px 0;margin:0;">暂无差评数据</p>'

    # ── 性能问题 ──
    perf_items = data.get("performance_issues") or []
    perf_html = ""
    for p in perf_items[:4]:
        sc = sev_colors.get(p.get("severity","轻微"), "#D69E2E")
        perf_html += f"""
        <div style="display:flex;gap:10px;padding:10px 0;border-bottom:1px solid #FFF5F5;">
          <div style="flex-shrink:0;">
            <span style="display:inline-block;width:8px;height:8px;background:{sc};border-radius:50%;margin-top:5px;"></span>
          </div>
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:4px;">
              {pill(p.get("type",""), sc, sc+"18")}
              {pill(p.get("severity",""), sc, sc+"18")}
              {platform_pill(p.get("platform",""))}
              <span style="font-size:10px;color:#A0AEC0;">{p.get("pub_time","")}</span>
            </div>
            {quote_block(p.get("quote",""), "#742A2A")}
            <div style="margin-top:6px;">{link_btn(p.get("url",""))}</div>
          </div>
        </div>"""
    perf_bg = "#FFF5F5" if perf_items else "#F0FFF4"
    perf_border = "#FC8181" if perf_items else "#9AE6B4"
    perf_empty = "" if perf_html else '<p style="color:#38A169;font-size:13px;margin:0;">✓ 过去24小时内未发现明显性能投诉</p>'

    # ── 合作主播动态 ──
    kol_html = ""
    for k in (data.get("kol_activity") or [])[:5]:
        sc = sent_colors.get(k.get("sentiment","中立"), "#718096")
        kol_html += f"""
        <div style="display:flex;gap:12px;padding:10px 0;border-bottom:1px solid #FAF5FF;">
          <div style="flex-shrink:0;width:36px;height:36px;background:linear-gradient(135deg,#667EEA,#764BA2);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;">⭐</div>
          <div style="flex:1;">
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-bottom:4px;">
              <span style="font-size:13px;font-weight:600;color:#1A202C;">{k.get("kol_name","")}</span>
              {pill(k.get("sentiment",""), sc)}
              <span style="font-size:10px;color:#A0AEC0;">{k.get("pub_time","")}</span>
            </div>
            <p style="margin:0 0 6px;font-size:12px;color:#4A5568;line-height:1.5;">{k.get("content_summary","")}</p>
            {link_btn(k.get("url",""), "查看视频 →")}
          </div>
        </div>"""
    if not kol_html:
        kol_html = '<p style="color:#A0AEC0;font-size:13px;padding:8px 0;margin:0;">过去24小时内合作主播暂无相关内容</p>'

    # ── 玩家建议 ──
    sug_html = ""
    for s in (data.get("suggestions") or [])[:4]:
        sug_html += f"""
        <div style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid #EBF8FF;">
          <span style="color:#3182CE;font-size:16px;flex-shrink:0;line-height:1.4;">→</span>
          <div style="flex:1;">
            <p style="margin:0 0 4px;font-size:13px;color:#2D3748;">{s.get("content","")}</p>
            <div style="display:flex;align-items:center;gap:8px;">{platform_pill(s.get("platform",""))} {link_btn(s.get("url",""))}</div>
          </div>
        </div>"""
    if not sug_html:
        sug_html = '<p style="color:#A0AEC0;font-size:13px;padding:8px 0;margin:0;">暂无玩家建议</p>'

    # ── 行动建议 ──
    action_html = ""
    for a in (data.get("action_items") or []):
        p = a.get("priority","P3低")
        color, bg, icon = priority_config.get(p, ("#718096","#F7FAFC","⚪"))
        action_html += f"""
        <div style="display:flex;align-items:flex-start;gap:12px;padding:10px 14px;background:{bg};border-radius:8px;margin-bottom:6px;border-left:3px solid {color};">
          <span style="font-size:13px;font-weight:700;color:{color};white-space:nowrap;">{icon} {p}</span>
          <div style="flex:1;">
            <p style="margin:0 0 2px;font-size:13px;color:#2D3748;">{a.get("content","")}</p>
            <span style="font-size:11px;color:#A0AEC0;">{a.get("owner","")}</span>
          </div>
        </div>"""

    coverage = " · ".join(data.get("platform_coverage") or [])
    total = data.get("total_found", 0)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>忆蚀舆情简报 {REPORT_DATE}</title>
</head>
<body style="margin:0;padding:0;background:#F7FAFC;font-family:-apple-system,BlinkMacSystemFont,'PingFang SC','Helvetica Neue',sans-serif;-webkit-font-smoothing:antialiased;">

<div style="max-width:640px;margin:0 auto;padding:24px 16px 40px;">

  <!-- ══ 页眉 ══ -->
  <div style="background:linear-gradient(135deg,#0F0C29 0%,#302B63 50%,#24243E 100%);border-radius:16px 16px 0 0;padding:32px 32px 24px;position:relative;overflow:hidden;">
    <!-- 装饰圆 -->
    <div style="position:absolute;top:-40px;right:-40px;width:160px;height:160px;background:rgba(255,255,255,0.03);border-radius:50%;"></div>
    <div style="position:absolute;bottom:-20px;left:20px;width:80px;height:80px;background:rgba(255,255,255,0.02);border-radius:50%;"></div>

    <!-- Logo + 日期 行 -->
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
      <img src="{LOGO_B64}" alt="YOKAVERSE" style="height:28px;opacity:0.9;">
      <span style="font-size:11px;color:rgba(255,255,255,0.45);letter-spacing:1px;">PLAYER INSIGHT REPORT</span>
    </div>

    <!-- 游戏名 -->
    <div style="margin-bottom:16px;">
      <div style="font-size:11px;color:rgba(255,255,255,0.4);letter-spacing:2px;margin-bottom:6px;">INFINI FUN · 发行商日报</div>
      <h1 style="margin:0;font-size:28px;font-weight:800;color:#FFFFFF;letter-spacing:-0.5px;line-height:1.2;">《忆蚀 Subliminal》</h1>
      <div style="font-size:13px;color:rgba(255,255,255,0.55);margin-top:4px;">24h 玩家反馈洞察 · {REPORT_DATE}</div>
    </div>

    <!-- 统计栏 -->
    <div style="display:flex;gap:12px;flex-wrap:wrap;">
      <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 16px;min-width:80px;">
        <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-bottom:2px;">收集内容</div>
        <div style="font-size:20px;font-weight:700;color:#FFF;">{total}</div>
      </div>
      <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 16px;min-width:80px;">
        <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-bottom:2px;">整体情感</div>
        <div style="font-size:15px;font-weight:700;color:{score_color};">{overall}</div>
        {score_bar}
      </div>
      <div style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:10px 16px;flex:1;min-width:120px;">
        <div style="font-size:10px;color:rgba(255,255,255,0.45);margin-bottom:4px;">覆盖平台</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.7);line-height:1.5;">{coverage or "多平台"}</div>
      </div>
    </div>
  </div>

  <!-- ══ 正文容器 ══ -->
  <div style="background:#FFFFFF;border-radius:0 0 16px 16px;padding:0 24px 24px;box-shadow:0 4px 24px rgba(0,0,0,0.06);">

    <!-- 热议话题 -->
    <div style="padding:24px 0 0;">
      {section_header("🔥", "热议话题")}
      {hot_html or '<p style="color:#A0AEC0;font-size:13px;">暂无热议话题</p>'}
    </div>

    <div style="height:1px;background:#F7FAFC;margin:20px 0;"></div>

    <!-- 好评亮点 -->
    <div>
      {section_header("👍", "好评亮点", "#276749")}
      {pos_html}
    </div>

    <div style="height:1px;background:#F7FAFC;margin:20px 0;"></div>

    <!-- 差评痛点 -->
    <div>
      {section_header("👎", "差评痛点", "#742A2A")}
      {pain_html}
    </div>

    <div style="height:1px;background:#F7FAFC;margin:20px 0;"></div>

    <!-- 性能问题 -->
    <div style="background:{perf_bg};border-radius:12px;padding:16px 18px;border:1px solid {perf_border};">
      {section_header("⚡", "性能 & 技术问题监测", "#744210")}
      {perf_html}
      {perf_empty}
    </div>

    <div style="height:20px;"></div>

    <!-- 合作主播 -->
    <div style="background:#FAF5FF;border-radius:12px;padding:16px 18px;border:1px solid #D6BCFA;">
      {section_header("⭐", "B站合作主播动态", "#44337A")}
      {kol_html}
    </div>

    <div style="height:1px;background:#F7FAFC;margin:20px 0;"></div>

    <!-- 玩家建议 -->
    <div style="background:#EBF8FF;border-radius:12px;padding:16px 18px;border:1px solid #BEE3F8;">
      {section_header("💡", "玩家建议", "#2C5282")}
      {sug_html}
    </div>

    <div style="height:1px;background:#F7FAFC;margin:20px 0;"></div>

    <!-- 行动建议 -->
    <div>
      {section_header("✅", "行动建议")}
      {action_html or '<p style="color:#A0AEC0;font-size:13px;">暂无行动建议</p>'}
    </div>

  </div>

  <!-- ══ 页脚 ══ -->
  <div style="margin-top:20px;padding:20px 24px;background:#FFFFFF;border-radius:12px;display:flex;align-items:center;justify-content:space-between;box-shadow:0 2px 8px rgba(0,0,0,0.04);">
    <div>
      <img src="{LOGO_B64}" alt="YOKAVERSE" style="height:20px;opacity:0.6;display:block;margin-bottom:4px;">
      <div style="font-size:10px;color:#A0AEC0;">Infini Fun 舆情监控系统 · 自动生成</div>
    </div>
    <div style="text-align:right;">
      <div style="font-size:11px;color:#718096;font-weight:500;">{REPORT_DATE} 08:00 CST</div>
      <div style="font-size:10px;color:#A0AEC0;margin-top:2px;">B站 · YouTube · 小黑盒 · Steam · Reddit · 更多</div>
    </div>
  </div>

</div>
</body>
</html>"""

def send_gmail(html_body, data):
    perfs = data.get("performance_issues") or []
    severe = sum(1 for p in perfs if p.get("severity") == "严重")
    tag = f" 🚨 {severe}条严重性能问题" if severe else ""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【忆蚀-{REPORT_DATE_SHORT}-24h玩家反馈洞察】{tag}"
    msg["From"]    = f"忆蚀舆情监控 <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL
    plain = f"忆蚀 24h玩家反馈洞察 {REPORT_DATE}\n整体情感：{data.get('overall_sentiment','')}\n"
    for t in (data.get("hot_topics") or [])[:3]:
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
