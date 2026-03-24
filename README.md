# 《忆蚀 Subliminal》玩家舆情日报系统

> **Infini Fun** 出品 · 每天北京时间 08:00 自动发送

每天自动抓取过去 24 小时内玩家在 Steam、Reddit、微博、B站、NGA、TapTap、Twitter/X、YouTube 等平台的讨论，重点检测帧率、卡顿、崩溃等性能问题，生成精美 HTML 日报通过 Gmail 发送。

---

## 🚀 三步完成部署

### 第一步：Fork 或上传到你的 GitHub 仓库

```bash
git init
git add .
git commit -m "feat: 添加忆蚀舆情日报系统"
git remote add origin https://github.com/你的账号/subliminal-daily-report.git
git push -u origin main
```

### 第二步：配置 4 个 GitHub Secrets

进入仓库页面 → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret 名称 | 值 | 获取方式 |
|---|---|---|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...` | [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_SENDER_EMAIL` | `yourname@gmail.com` | 你的 Gmail 地址 |
| `GMAIL_APP_PASSWORD` | `xxxx xxxx xxxx xxxx` | 见下方说明 ↓ |
| `REPORT_RECIPIENT_EMAIL` | `boss@infinifun.com` | 报告收件人邮箱 |

#### 如何获取 Gmail 应用专用密码：
1. 登录 Gmail → Google 账号 → **安全性**
2. 开启**两步验证**（必须先开启）
3. 搜索"应用专用密码" → 创建 → 选择"邮件" → 复制 16 位密码

### 第三步：验证触发

进入 **Actions** → **忆蚀 Subliminal 玩家舆情日报** → **Run workflow** 手动测试一次。

---

## ⏰ 触发时间

| 触发方式 | 说明 |
|---|---|
| 自动定时 | 每天北京时间 **08:00**（UTC 00:00） |
| 手动触发 | GitHub Actions 页面点击 "Run workflow" |

---

## 📊 报告内容

每封邮件包含：

- **执行摘要** — 高管快速阅读版
- **⚡ 性能问题监测** — 帧率/卡顿/崩溃问题，标注严重程度
- **🔥 热议话题** — 玩家讨论焦点标签
- **💬 讨论亮点** — 各平台重要反馈
- **👍/👎 正负面反馈** — 玩家好评与差评汇总
- **🌐 各平台概览** — Steam / Reddit / 国内社媒 / Twitter / YouTube
- **✅ 行动建议** — 按优先级排列（P0紧急 → P3低）

---

## 🛠 本地测试

```bash
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
export GMAIL_SENDER_EMAIL="your@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export REPORT_RECIPIENT_EMAIL="you@example.com"

python scripts/daily_report.py
```

---

## 📁 项目结构

```
subliminal-daily-report/
├── .github/
│   └── workflows/
│       └── daily-report.yml     # GitHub Actions 定时任务
├── scripts/
│   └── daily_report.py          # 主脚本
├── requirements.txt             # Python 依赖（仅 anthropic）
├── CLAUDE.md                    # Claude Code 项目描述
└── README.md                    # 本文件
```
