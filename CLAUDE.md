# 忆蚀 Subliminal 舆情日报系统

## 项目概述
为发行商 **Infini Fun** 自动监测独立游戏《忆蚀 Subliminal》上线后的玩家讨论，每天北京时间 08:00 通过 Gmail 发送 HTML 格式日报。

## 核心文件
- `scripts/daily_report.py` — 主脚本：搜索 → 分析 → 发送邮件
- `.github/workflows/daily-report.yml` — GitHub Actions 定时任务（每天 UTC 00:00）
- `requirements.txt` — 仅依赖 `anthropic` SDK

## 技术架构
```
GitHub Actions (cron 0 0 * * *)
    └─▶ daily_report.py
            ├─▶ Claude API + web_search_20250305 工具
            │       └─▶ 搜索 Steam / Reddit / 微博 / B站 / NGA / TapTap / Twitter / YouTube
            ├─▶ Claude API (分析) → 结构化 JSON 报告
            └─▶ Gmail SMTP (TLS 465) → HTML 邮件
```

## 必须配置的 GitHub Secrets
在仓库 Settings → Secrets and variables → Actions 中添加：

| Secret 名称 | 说明 |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API 密钥 |
| `GMAIL_SENDER_EMAIL` | 发件 Gmail 地址 |
| `GMAIL_APP_PASSWORD` | Gmail 应用专用密码（16位） |
| `REPORT_RECIPIENT_EMAIL` | 收件人邮箱（可与发件相同） |

## 本地测试方法
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export GMAIL_SENDER_EMAIL="your@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export REPORT_RECIPIENT_EMAIL="boss@infinifun.com"
python scripts/daily_report.py
```

## 重点监测指标
脚本会特别关注以下性能问题关键词：
- 帧率/FPS/帧数/掉帧
- 卡顿/lag/stuttering/stutter  
- 游戏崩溃/crash/闪退
- 加载慢/loading
- 内存泄漏/memory leak
- 黑屏/白屏/花屏
- 存档丢失/bug

## 定制修改指南
- **修改发送时间**：编辑 `.github/workflows/daily-report.yml` 中的 cron 表达式
  - `0 0 * * *` = 北京时间 08:00（UTC 00:00）
  - `0 1 * * *` = 北京时间 09:00（UTC 01:00）
- **添加监测平台**：修改 `daily_report.py` 中 `collect_player_discussions()` 的 `search_prompt`
- **修改报告收件人**：更新 GitHub Secret `REPORT_RECIPIENT_EMAIL`
