from collectors.taobao import TaobaoCollector
from configs.common import KEYWORDS
from configs.dingtalk import DINGTALK_CONFIG
from configs.taobao import TAOBAO_CONFIG
from formatters.auction import AuctionFormatter
from notifiers.dingtalk import DingTalkNotifier
from services.monitor import MonitorService


def main():
    collectors = []

    if TAOBAO_CONFIG.enabled:
        collectors.append(
            TaobaoCollector(TAOBAO_CONFIG)
        )

    # 1. 采集所有网站
    monitor = MonitorService(collectors)
    results = monitor.run(KEYWORDS)

    # 2. 控制台汇总
    monitor.print_summary(results)

    # 3. 格式化为钉钉 Markdown
    formatter = AuctionFormatter(
        title=DINGTALK_CONFIG.title
    )
    message = formatter.format(results)

    # 4. 推送钉钉
    if DINGTALK_CONFIG.enabled:
        notifier = DingTalkNotifier(
            DINGTALK_CONFIG
        )
        notifier.send(message)


if __name__ == "__main__":
    main()
