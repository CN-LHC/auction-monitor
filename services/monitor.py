from collectors.base import BaseCollector
from models.auction import Auction


class MonitorService:
    def __init__(self, collectors: list[BaseCollector]):
        self.collectors = collectors

    def run(
        self,
        keywords: list[str],
    ) -> dict[str, dict[str, list[Auction]]]:
        all_results: dict[str, dict[str, list[Auction]]] = {}

        for collector in self.collectors:
            print()
            print("=" * 70)
            print(f"开始采集：{collector.name}")
            print("=" * 70)

            try:
                all_results[collector.name] = collector.search(keywords)
            except Exception as exc:
                print(f"✗ {collector.name} 采集失败：{exc}")
                all_results[collector.name] = {}

        return all_results

    @staticmethod
    def print_summary(
        all_results: dict[str, dict[str, list[Auction]]]
    ) -> None:
        print()
        print("=" * 70)
        print("多数据源拍卖监控汇总")
        print("=" * 70)

        total = 0

        for source, keyword_results in all_results.items():
            print()
            print(f"数据源：{source}")

            for keyword, auctions in keyword_results.items():
                print(f"  关键词：{keyword}，数量：{len(auctions)}")
                total += len(auctions)

                for index, auction in enumerate(auctions, start=1):
                    price = f"{auction.price}{auction.price_unit}"
                    print(f"    [{index}] {auction.title}")
                    print(f"        状态：{auction.status_text}")
                    print(f"        当前价：{price}")
                    print(f"        链接：{auction.url}")

        print()
        print(f"拍品总数：{total}")
        print("=" * 70)
