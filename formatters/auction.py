from datetime import datetime, timedelta, timezone

from models.auction import Auction


SOURCE_NAMES = {
    "taobao": "淘宝拍卖",
    "jd": "京东拍卖",
}


class AuctionFormatter:
    def __init__(self, title: str = "拍卖监控日报"):
        self.title = title

    def format(
        self,
        all_results: dict[str, dict[str, list[Auction]]],
    ) -> str:
        now = datetime.now(timezone(timedelta(hours=8)))
        total = sum(
            len(auctions)
            for keyword_results in all_results.values()
            for auctions in keyword_results.values()
        )

        lines = [
            f"## {self.title}",
            "",
            f"> 采集时间：{now:%Y-%m-%d %H:%M}（北京时间）",
            f"> 共获取：**{total}** 条",
            "",
        ]

        if not all_results:
            lines.append("本次没有可用的数据源结果。")
            return "\n".join(lines)

        for source, keyword_results in all_results.items():
            source_name = SOURCE_NAMES.get(source, source)
            source_total = sum(
                len(items)
                for items in keyword_results.values()
            )

            lines.extend([
                "---",
                "",
                f"### {source_name}（{source_total} 条）",
                "",
            ])

            if not keyword_results:
                lines.append("> 数据源采集失败或没有返回结果。")
                lines.append("")
                continue

            for keyword, auctions in keyword_results.items():
                lines.append(
                    f"#### 关键词：{keyword}（{len(auctions)} 条）"
                )
                lines.append("")

                if not auctions:
                    lines.append("> 未检索到拍品")
                    lines.append("")
                    continue

                for index, auction in enumerate(auctions, start=1):
                    lines.extend(
                        self._format_auction(index, auction)
                    )

        return "\n".join(lines).strip()

    @staticmethod
    def _format_auction(
        index: int,
        auction: Auction,
    ) -> list[str]:
        lines = [
            f"**{index}. {auction.title}**",
            "",
        ]

        if auction.status_text:
            lines.append(f"- 状态：{auction.status_text}")

        if auction.price:
            lines.append(
                f"- 当前价：{auction.price}{auction.price_unit}"
            )

        if auction.initial_price:
            lines.append(
                "- 起始价："
                f"{auction.initial_price}"
                f"{auction.initial_price_unit}"
            )

        time_text = (
            f"{auction.time_prefix}"
            f"{auction.time_centre}"
            f"{auction.time_suffix}"
        ).strip()

        if time_text:
            lines.append(f"- 拍卖时间：{time_text}")

        if auction.end_time:
            lines.append(f"- 结束时间：{auction.end_time}")

        if auction.shop_name:
            lines.append(f"- 机构：{auction.shop_name}")

        lines.append(
            "- 数据："
            f"围观 {auction.views} / "
            f"报名 {auction.apply_count} / "
            f"出价 {auction.bid_count}"
        )

        if auction.benefits:
            lines.append(
                "- 信息：" + " / ".join(auction.benefits)
            )

        if auction.url:
            lines.append(f"- [查看拍品]({auction.url})")

        lines.append("")
        return lines
