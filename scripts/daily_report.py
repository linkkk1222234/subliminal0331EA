#!/usr/bin/env python3
"""
忆蚀 Subliminal 玩家舆情日报
使用 DeepSeek API，每日自动抓取过去 24 小时内玩家讨论，重点关注性能问题，通过 Gmail 发送报告。
"""

import os
import json
import smtplib
from openai import OpenAI
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── 配置 ────────────────────────────────────────────────────────────────────
GAME_NAME_ZH = "忆蚀"
GAME_NAME_EN = "Subliminal"
PUBLISHER = "Infini Fun"

# B站预热合作主播名单（需重点关注其视频及评论区）
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

# DeepSeek 客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)
# ─────────────────────────────────────────────────────────────────────────────


def call_deepseek(prompt: str, max_tokens: int = 4000) -> str:
    """调用 DeepSeek API"""
    response = client.chat.completions.create(
        model="deepseek-chat",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def collect_player_discussions() -> str:
    """让 DeepSeek 基于训练知识 + 联网搜索，整理玩家讨论信息"""
    kol_list_str = "、".join(BILIBILI_KOLS)
    kol_search_queries = "\n".join(
        f"   - {kol} 的B站视频评论区关于《{GAME_NAME_ZH}》的讨论"
        for kol in BILIBILI_KOLS
    )

    prompt = f"""
你是一名游戏舆情分析助手，负责为发行商 {PUBLISHER} 监测独立游戏《{GAME_NAME_ZH}》（英文名 {GAME_NAME_EN}）的玩家反馈。

今天是 {REPORT_DATE}，请基于你能获取到的最新信息，收集并整理玩家对该游戏的讨论，重点关注：

━━━━━━ 【A. 通用平台】 ━━━━━━
1. Steam 评测与社区讨论
2. Reddit 相关讨论
3. Twitter/X 玩家反馈
4. 微博、NGA、贴吧讨论
5. TapTap 评测
6. YouTube 评论与视频

━━━━━━ 【B. B站合作主播（重点）】 ━━━━━━
以下是合作预热主播，请重点关注：
{kol_list_str}

关注内容：
{kol_search_queries}

━━━━━━ 【C. 性能问题关键词】 ━━━━━━
重点识别：帧率/FPS/掉帧、卡顿/lag/stuttering、崩溃/crash/闪退、
加载慢、内存泄漏、黑屏白屏花屏、存档丢失

请尽可能详细整理以上信息，对每条记录平台、来源、内容摘要、情感倾向、是否涉及技术问题。
如果游戏刚上线或数据有限，请说明情况并尽力整理已知信息。
"""

    print("🔍 正在收集玩家讨论数据...")
    result = call_deepseek(prompt, max_tokens=3000)
    print(f"✅ 数据收集完成，获取 {len(result)} 字符")
    return result


def analyze_and_generate_report(raw_data: str) -> dict:
    """对原始数据进行分析，生成结构化日报"""
    kol_list_str = "、".join(BILIBILI_KOLS)

    prompt = f"""
你是资深游戏发行商舆情分析师，请对以下《{GAME_NAME_ZH}》玩家讨论数据进行深度分析，生成专业日报。

**B站合作主播名单：** {kol_list_str}

━━━━━━ 原始数据 ━━━━━━
{raw_data}
━━━━━━━━━━━━━━━━━━━━━━

请严格只输出以下 JSON 格式，不要有任何 JSON 之外的内容，不要有 markdown 代码块：

{{
  "report_date": "{REPORT_DATE}",
  "overall_sentiment": "正面/负面/中立/混合",
  "sentiment_score": 75,
  "total_discussions": 50,
  "executive_summary": "3-4句话的核心摘要",
  "kol_monitoring": {{
    "summary": "合作主播整体动态概述",
    "active_kols": [
      {{
        "name": "主播名",
        "platform": "bilibili",
        "content_type": "视频/动态/评论",
        "attitude": "正面/负面/中立",
        "key_points": "内容核心要点",
        "performance_complaints": false,
        "performance_detail": null,
        "audience_reaction": "评论区受众反应",
        "action_needed": "是否需要关注及建议"
      }}
    ],
    "inactive_kols": ["未发布相关内容的主播名"],
    "alert_kols": ["需紧急关注的主播名"]
  }},
  "performance_issues": {{
    "has_critical_issues": false,
    "severity": "无",
    "issues": [],
    "performance_summary": "性能问题总结"
  }},
  "discussion_highlights": [
    {{
      "platform": "平台名",
      "source": "来源",
      "type": "正面亮点/负面反馈/技术问题/其他",
      "content": "讨论要点",
      "impact": "高/中/低"
    }}
  ],
  "hot_topics": ["话题1", "话题2", "话题3"],
  "positive_feedback": ["好评要点1", "好评要点2"],
  "negative_feedback": ["差评要点1", "差评要点2"],
  "platform_breakdown": {{
    "bilibili_kol": "B站合作主播概述",
    "bilibili_general": "B站普通玩家概述",
    "steam": "Steam概述",
    "reddit": "Reddit概述",
    "social_media_cn": "国内社媒概述",
    "twitter": "Twitter概述",
    "youtube": "YouTube概述"
  }},
  "action_items": [
    {{
      "priority": "P0紧急/P1高/P2中/P3低",
      "action": "具体行动建议",
      "owner": "开发团队/市场团队/客服团队/KOL运营"
    }}
  ],
  "data_availability": "数据说明"
}}
"""

    print("🤖 正在分析数据生成报告...")
    result = call_deepseek(prompt, max_tokens=4000)

    # 清理可能的 markdown 格式
    result = result.replace("```json", "").replace("```", "").strip()

    try:
        report = json.loads(result)
    except json.JSONDecodeError:
        # 尝试提取 JSON 部分
        start = result.find("{")
        end = result.rfind("}") + 1
        if start != -1 and end > start:
            try:
                report = json.loads(result[start:end])
            except:
                report = {
                    "report_date": REPORT_DATE,
                    "overall_sentiment": "中立",
                    "sentiment_score": 50,
                    "total_discussions": 0,
                    "executive_summary": result[:300],
                    "kol_monitoring": {"summary": "解析失败", "active_kols": [], "inactive_kols": [], "alert_kols": []},
                    "performance_issues": {"has_critical_issues": False, "severity": "未知", "issues": [], "performance_summary": ""},
                    "discussion_highlights": [],
                    "hot_topics": [],
                    "positive_feedback": [],
                    "negative_feedback": [],
                    "platform_breakdown": {},
                    "action_items": [],
                    "data_availability": "数据解析异常"
                }
        else:
            report = {
                "report_date": REPORT_DATE,
                "overall_sentiment": "中立",
                "sentiment_score": 50,
                "total_discussions": 0,
                "executive_summary": "报告生成异常，请检查日志",
                "kol_monitoring": {"summary": "", "active_kols": [], "inactive_kols": [], "alert_kols": []},
                "performance_issues": {"has_critical_issues": False, "severity": "未知", "issues": [], "performance_summary": ""},
                "discussion_highlights": [],
                "hot_topics": [],
                "positive_feedback": [],
                "negative_feedback": [],
                "platform_breakdown": {},
                "action_items": [],
                "data_availability": "数据解析异常"
            }

    print("✅ 报告生成完成")
    return report


def build_html_email(report: dict) -> str:
    """将结构化报告渲染为 HTML 邮件"""

    perf = report.get("performance_issues", {})
    has_critical = perf.get("has_critical_issues", False)
    severity = perf.get("severity", "无")
    severity_color = {
        "严重": "#dc2626", "中等": "#ea580c",
        "轻微": "#ca8a04", "无": "#16a34a", "未知": "#6b7280"
    }.get(severity, "#6b7280")

    sentiment_score = report.get("sentiment_score", 50)

    # ── 合作主播监测 ─────────────────────────────────────────
    kol_data = report.get("kol_monitoring", {})
    alert_kols = kol_data.get("alert_kols", [])
    inactive_kols = kol_data.get("inactive_kols", [])
    active_kols = kol_data.get("active_kols", [])

    kol_cards_html = ""
    attitude_styles = {
        "正面": ("#16a34a", "#f0fdf4", "👍"),
        "负面": ("#dc2626", "#fef2f2", "👎"),
        "中立": ("#6b7280", "#f9fafb", "😐"),
    }
    for kol in active_kols:
        attitude = kol.get("attitude", "中立")
        color, bg, icon = attitude_styles.get(attitude, ("#6b7280", "#f9fafb", "📌"))
        perf_badge = '<span style="background:#dc2626;color:#fff;font-size:10px;padding:1px 6px;border-radius:10px;margin-left:6px;">⚡ 含性能投诉</span>' if kol.get("performance_complaints") else ""
        perf_detail_html = f'<div style="margin-top:6px;font-size:12px;color:#dc2626;background:#fef2f2;border-radius:4px;padding:6px 8px;">⚠️ {kol.get("performance_detail","")}</div>' if kol.get("performance_complaints") and kol.get("performance_detail") else ""
        action_html = f'<div style="margin-top:6px;font-size:12px;color:#1d4ed8;background:#eff6ff;border-radius:4px;padding:6px 8px;">💡 {kol.get("action_needed","")}</div>' if kol.get("action_needed") else ""

        kol_cards_html += f"""
        <div style="background:{bg};border:1px solid {color}33;border-left:3px solid {color};border-radius:8px;padding:12px 14px;margin-bottom:10px;">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;flex-wrap:wrap;">
            <span style="font-weight:700;color:#111827;font-size:14px;">{icon} {kol.get('name','')}</span>
            <span style="background:{color};color:#fff;font-size:10px;padding:1px 7px;border-radius:10px;">{attitude}</span>
            <span style="background:#e2e8f0;color:#475569;font-size:10px;padding:1px 7px;border-radius:10px;">{kol.get('content_type','')}</span>
            {perf_badge}
          </div>
          <div style="font-size:13px;color:#374151;margin-bottom:4px;">{kol.get('key_points','')}</div>
          <div style="font-size:12px;color:#64748b;">受众反应：{kol.get('audience_reaction','')}</div>
          {perf_detail_html}
          {action_html}
        </div>"""

    if not kol_cards_html:
        kol_cards_html = '<div style="color:#6b7280;font-size:13px;padding:12px;background:#f9fafb;border-radius:8px;">过去24小时内，合作主播暂未发布相关内容</div>'

    inactive_html = ""
    if inactive_kols:
        inactive_tags = "".join(
            f'<span style="display:inline-block;background:#f1f5f9;color:#94a3b8;border:1px solid #e2e8f0;font-size:11px;padding:2px 8px;border-radius:10px;margin:2px;">{n}</span>'
            for n in inactive_kols
        )
        inactive_html = f'<div style="margin-top:10px;"><div style="font-size:12px;color:#94a3b8;margin-bottom:5px;">以下主播今日无相关内容：</div><div>{inactive_tags}</div></div>'

    alert_kol_banner = ""
    if alert_kols:
        alert_names = "、".join(alert_kols)
        alert_kol_banner = f'<div style="background:#fef2f2;border:1px solid #fca5a5;border-radius:6px;padding:10px 14px;margin-bottom:10px;font-size:13px;color:#991b1b;">🚨 需紧急关注主播：<strong>{alert_names}</strong></div>'

    # ── 性能问题 ─────────────────────────────────────────────
    perf_issues_html = ""
    for issue in perf.get("issues", []):
        if isinstance(issue, str):
            continue
        platforms = "、".join(issue.get("platforms_affected", []))
        quote = issue.get("sample_quote", "")
        quote_html = f'<blockquote style="margin:8px 0 0;padding:8px 12px;background:#fef3c7;border-left:3px solid #f59e0b;color:#92400e;font-size:13px;border-radius:0 4px 4px 0;">"{quote}"</blockquote>' if quote else ""
        perf_issues_html += f"""
        <div style="background:#fff7ed;border:1px solid #fed7aa;border-radius:8px;padding:14px;margin-bottom:10px;">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
            <span style="background:#ea580c;color:#fff;font-size:11px;padding:2px 8px;border-radius:12px;font-weight:600;">{issue.get('type','')}</span>
            <span style="color:#78350f;font-size:12px;">频率：{issue.get('frequency','')}</span>
          </div>
          <div style="font-size:13px;color:#431407;">影响平台：{platforms}</div>
          {quote_html}
          <div style="margin-top:8px;font-size:12px;color:#9a3412;background:#fff;border-radius:4px;padding:6px 8px;">💡 建议：{issue.get('suggested_action','')}</div>
        </div>"""

    if not perf_issues_html:
        perf_issues_html = '<div style="color:#16a34a;padding:12px;background:#f0fdf4;border-radius:8px;font-size:14px;">✅ 过去 24 小时内未发现明显性能投诉</div>'

    # ── 讨论亮点 ─────────────────────────────────────────────
    highlights_html = ""
    type_colors = {
        "正面亮点": "#16a34a", "负面反馈": "#dc2626",
        "功能建议": "#2563eb", "技术问题": "#ea580c", "其他": "#6b7280"
    }
    for h in report.get("discussion_highlights", [])[:6]:
        t = h.get("type", "其他")
        c = type_colors.get(t, "#6b7280")
        impact_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}.get(h.get("impact", "低"), "⚪")
        highlights_html += f"""
        <div style="border-left:3px solid {c};padding:10px 14px;margin-bottom:8px;background:#fafafa;border-radius:0 6px 6px 0;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="color:{c};font-size:11px;font-weight:600;">[{h.get('platform','')}] {t}</span>
            <span style="font-size:11px;">{impact_icon} 影响度：{h.get('impact','')}</span>
          </div>
          <div style="font-size:13px;color:#374151;">{h.get('content','')}</div>
        </div>"""

    # ── 行动建议 ─────────────────────────────────────────────
    actions_html = ""
    priority_styles = {
        "P0紧急": ("🚨", "#dc2626", "#fef2f2"),
        "P1高":   ("🔴", "#ea580c", "#fff7ed"),
        "P2中":   ("🟡", "#ca8a04", "#fefce8"),
        "P3低":   ("🟢", "#16a34a", "#f0fdf4"),
    }
    for a in report.get("action_items", []):
        p = a.get("priority", "P3低")
        icon, color, bg = priority_styles.get(p, ("⚪", "#6b7280", "#f9fafb"))
        actions_html += f"""
        <tr>
          <td style="padding:10px 12px;font-size:12px;font-weight:700;color:{color};background:{bg};white-space:nowrap;">{icon} {p}</td>
          <td style="padding:10px 12px;font-size:13px;color:#111827;">{a.get('action','')}</td>
          <td style="padding:10px 12px;font-size:12px;color:#6b7280;white-space:nowrap;">{a.get('owner','')}</td>
        </tr>"""

    # ── 平台概览 ─────────────────────────────────────────────
    platform_data = report.get("platform_breakdown", {})
    platforms_html = ""
    platform_icons = {
        "bilibili_kol": "⭐", "bilibili_general": "📺",
        "steam": "🎮", "reddit": "🤖",
        "social_media_cn": "🇨🇳", "twitter": "🐦", "youtube": "▶️"
    }
    platform_names = {
        "bilibili_kol": "B站合作主播", "bilibili_general": "B站普通玩家",
        "steam": "Steam", "reddit": "Reddit",
        "social_media_cn": "国内社媒", "twitter": "Twitter/X", "youtube": "YouTube"
    }
    for key, summary in platform_data.items():
        icon = platform_icons.get(key, "📌")
        name = platform_names.get(key, key)
        if summary:
            platforms_html += f"""
            <div style="padding:12px;background:#f8fafc;border-radius:8px;margin-bottom:8px;">
              <div style="font-weight:600;color:#1e293b;margin-bottom:4px;">{icon} {name}</div>
              <div style="font-size:13px;color:#475569;">{summary}</div>
            </div>"""

    # ── 热议话题 ─────────────────────────────────────────────
    tags_html = " ".join(
        f'<span style="display:inline-block;background:#eff6ff;color:#1d4ed8;border:1px solid #bfdbfe;font-size:12px;padding:3px 10px;border-radius:20px;margin:3px;"># {t}</span>'
        for t in report.get("hot_topics", [])
    )

    def list_items(items, color, icon):
        return "".join(
            f'<li style="padding:5px 0;color:{color};font-size:13px;">{icon} {item}</li>'
            for item in items
        ) or f'<li style="color:#9ca3af;font-size:13px;">暂无数据</li>'

    pos_items = list_items(report.get("positive_feedback", []), "#166534", "✅")
    neg_items = list_items(report.get("negative_feedback", []), "#991b1b", "⚠️")

    overall_sentiment = report.get("overall_sentiment", "中立")
    sentiment_emoji = {"正面": "😊", "负面": "😟", "中立": "😐", "混合": "🔄"}.get(overall_sentiment, "📊")

    alert_banner = ""
    if has_critical:
        alert_banner = f"""
        <div style="background:#fef2f2;border:2px solid #dc2626;border-radius:10px;padding:16px;margin-bottom:24px;">
          <div style="display:flex;align-items:center;gap:10px;">
            <span style="font-size:24px;">🚨</span>
            <div>
              <div style="font-weight:700;color:#dc2626;font-size:15px;">发现严重性能问题！需要立即关注</div>
              <div style="color:#991b1b;font-size:13px;margin-top:2px;">已检测到玩家大量反馈技术问题，请研发团队优先处理</div>
            </div>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:680px;margin:0 auto;padding:24px 16px;">

  <div style="background:linear-gradient(135deg,#1e1b4b 0%,#312e81 50%,#4338ca 100%);border-radius:14px;padding:28px 32px;margin-bottom:20px;color:#fff;">
    <div style="font-size:12px;opacity:0.7;margin-bottom:4px;letter-spacing:1px;">INFINI FUN · 发行商日报</div>
    <div style="font-size:24px;font-weight:700;margin-bottom:2px;">《忆蚀 Subliminal》</div>
    <div style="font-size:14px;opacity:0.8;">玩家舆情日报 · {REPORT_DATE}</div>
    <div style="margin-top:16px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;">
        <div style="font-size:11px;opacity:0.7;">整体情感</div>
        <div style="font-size:16px;font-weight:700;">{sentiment_emoji} {overall_sentiment}</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;">
        <div style="font-size:11px;opacity:0.7;">情感分数</div>
        <div style="font-size:16px;font-weight:700;">{sentiment_score}/100</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;">
        <div style="font-size:11px;opacity:0.7;">讨论量</div>
        <div style="font-size:16px;font-weight:700;">~{report.get('total_discussions', 0)} 条</div>
      </div>
      <div style="background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;">
        <div style="font-size:11px;opacity:0.7;">性能问题</div>
        <div style="font-size:16px;font-weight:700;color:{severity_color};">⚡ {severity}</div>
      </div>
    </div>
  </div>

  {alert_banner}

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">📋 执行摘要</h2>
    <p style="margin:0;font-size:14px;color:#475569;line-height:1.7;">{report.get('executive_summary', '暂无摘要')}</p>
    <div style="margin-top:12px;font-size:12px;color:#94a3b8;padding-top:10px;border-top:1px dashed #e2e8f0;">
      📌 数据说明：{report.get('data_availability', '数据已收集')}
    </div>
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:2px solid #7c3aed;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <h2 style="margin:0;font-size:15px;color:#1e293b;">⭐ B站合作主播监测</h2>
      <span style="background:#7c3aed;color:#fff;font-size:11px;padding:3px 10px;border-radius:20px;">共 {len(BILIBILI_KOLS)} 位主播</span>
    </div>
    <div style="font-size:12px;color:#64748b;margin-bottom:12px;padding:8px 12px;background:#faf5ff;border-radius:6px;">
      📋 {kol_data.get('summary', '正在监测合作主播动态...')}
    </div>
    {alert_kol_banner}
    {kol_cards_html}
    {inactive_html}
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:2px solid {severity_color};">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
      <h2 style="margin:0;font-size:15px;color:#1e293b;">⚡ 性能 & 技术问题监测</h2>
      <span style="background:{severity_color};color:#fff;font-size:12px;padding:3px 10px;border-radius:20px;font-weight:600;">{severity}</span>
    </div>
    {perf_issues_html}
    <div style="margin-top:10px;font-size:13px;color:#475569;">{perf.get('performance_summary','')}</div>
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 12px;font-size:15px;color:#1e293b;">🔥 热议话题</h2>
    <div>{tags_html or '<span style="color:#9ca3af;font-size:13px;">暂无热议话题数据</span>'}</div>
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 14px;font-size:15px;color:#1e293b;">💬 讨论亮点</h2>
    {highlights_html or '<div style="color:#9ca3af;font-size:13px;">暂无讨论亮点数据</div>'}
  </div>

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px;">
    <div style="background:#f0fdf4;border-radius:12px;padding:18px 20px;border:1px solid #bbf7d0;">
      <h3 style="margin:0 0 10px;font-size:14px;color:#166534;">👍 玩家好评</h3>
      <ul style="margin:0;padding-left:0;list-style:none;">{pos_items}</ul>
    </div>
    <div style="background:#fef2f2;border-radius:12px;padding:18px 20px;border:1px solid #fecaca;">
      <h3 style="margin:0 0 10px;font-size:14px;color:#991b1b;">👎 玩家差评</h3>
      <ul style="margin:0;padding-left:0;list-style:none;">{neg_items}</ul>
    </div>
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:16px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 14px;font-size:15px;color:#1e293b;">🌐 各平台概览</h2>
    {platforms_html or '<div style="color:#9ca3af;font-size:13px;">暂无平台数据</div>'}
  </div>

  <div style="background:#fff;border-radius:12px;padding:20px 24px;margin-bottom:20px;border:1px solid #e2e8f0;">
    <h2 style="margin:0 0 14px;font-size:15px;color:#1e293b;">✅ 行动建议</h2>
    <table style="width:100%;border-collapse:collapse;border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
      <thead>
        <tr style="background:#f8fafc;">
          <th style="padding:10px 12px;text-align:left;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0;">优先级</th>
          <th style="padding:10px 12px;text-align:left;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0;">行动建议</th>
          <th style="padding:10px 12px;text-align:left;font-size:12px;color:#64748b;border-bottom:1px solid #e2e8f0;">负责方</th>
        </tr>
      </thead>
      <tbody>
        {actions_html or '<tr><td colspan="3" style="padding:12px;text-align:center;color:#9ca3af;font-size:13px;">暂无行动建议</td></tr>'}
      </tbody>
    </table>
  </div>

  <div style="text-align:center;color:#94a3b8;font-size:11px;padding-bottom:16px;">
    此报告由 Infini Fun 舆情监控系统自动生成（DeepSeek AI 驱动）<br>
    报告时间：{REPORT_DATE} 08:00 (CST) · 数据来源：Steam / Reddit / 微博 / B站 / NGA / TapTap / Twitter/X / YouTube
  </div>

</div>
</body>
</html>"""

    return html


def send_gmail(html_body: str, report: dict):
    """通过 Gmail SMTP 发送 HTML 报告"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"【忆蚀日报】{REPORT_DATE} 玩家舆情 · {report.get('overall_sentiment','中立')}" + \
                     (" 🚨 发现性能问题！" if report.get("performance_issues", {}).get("has_critical_issues") else "")
    msg["From"]    = f"忆蚀舆情监控 <{SENDER_EMAIL}>"
    msg["To"]      = RECIPIENT_EMAIL

    plain_text = f"""忆蚀 Subliminal 玩家舆情日报 - {REPORT_DATE}

执行摘要：
{report.get('executive_summary', '暂无摘要')}

性能问题：{report.get('performance_issues', {}).get('severity', '无')}
整体情感：{report.get('overall_sentiment', '中立')} ({report.get('sentiment_score', 50)}/100)

---
Infini Fun 舆情监控系统自动生成（DeepSeek AI 驱动）
"""

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"📧 正在发送邮件至 {RECIPIENT_EMAIL} ...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_bytes())
    print("✅ 邮件发送成功！")


def main():
    print(f"\n{'='*60}")
    print(f"  忆蚀 Subliminal 舆情日报生成器（DeepSeek 版）")
    print(f"  报告日期：{REPORT_DATE}")
    print(f"{'='*60}\n")

    raw_data  = collect_player_discussions()
    report    = analyze_and_generate_report(raw_data)
    html_body = build_html_email(report)
    send_gmail(html_body, report)

    print("\n✅ 日报任务完成！")
    print(f"   整体情感：{report.get('overall_sentiment')}（{report.get('sentiment_score')}/100）")
    print(f"   性能问题：{report.get('performance_issues', {}).get('severity', '无')}")
    print(f"   行动建议：{len(report.get('action_items', []))} 条")


if __name__ == "__main__":
    main()
