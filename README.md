# auction-monitor

多数据源拍卖监控：Collector → Monitor → Formatter → Notifier。

当前：
- 淘宝拍卖采集
- 钉钉 Markdown 推送
- 淘宝拍卖采集后过滤已结束的拍品（`status=end`、`timeSuffix` 为“已结束”或 `feetText` 以“已结束”结尾），不计入汇总和钉钉上报
- 不做历史数据库/去重，每次推送本次采集并筛选后的全部结果

## 1. 安装

```bash
uv sync
uv run playwright install chromium
```

## 2. 配置钉钉

复制环境变量模板：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
DINGTALK_WEBHOOK=你的机器人Webhook
DINGTALK_SECRET=你的加签密钥
```

如果机器人没有启用“加签”，`DINGTALK_SECRET` 留空。

不要把 `.env` 提交到 Git；项目的 `.gitignore` 已忽略它。

## 3. 运行

```bash
uv run main.py
```

流程：

```text
各网站 Collector
    ↓
MonitorService
    ↓
统一 Auction
    ↓
AuctionFormatter
    ↓
DingTalkNotifier
    ↓
钉钉群
```

## 4. 多网站扩展

每个网站拆分自己的配置与采集器，例如：

```text
configs/
├── common.py
├── taobao.py
├── dingtalk.py
└── jd.py

collectors/
├── base.py
├── taobao.py
└── jd.py
```

新增网站只需要实现 `BaseCollector.search()` 并返回统一 `Auction` 对象。
