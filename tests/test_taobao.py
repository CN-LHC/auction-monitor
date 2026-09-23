import unittest

from collectors.taobao import TaobaoCollector
from configs.taobao import TaobaoConfig
from formatters.auction import AuctionFormatter


class TaobaoFilteringTests(unittest.TestCase):
    def test_ended_items_do_not_reach_report(self):
        states = [
            {"status": "end"},
            {"status": "pause", "timeSuffix": "已结束"},
            {"status": "pause", "feetText": "已结束"},
            {"feetText": "2020年12月14日已结束"},
            {"status": "before", "timeSuffix": "开始"},
            {"status": "ing", "timeSuffix": "倒计时"},
            {"status": "pause", "timeSuffix": "已暂停"},
            {"status": None, "timeSuffix": None, "feetText": None},
        ]
        items = [
            dict(state, itemId=str(index), auctionTitle=f"拍品{index}",
                 auctionLink=f"https://example.com/{index}")
            for index, state in enumerate(states)
        ]
        collector = TaobaoCollector(TaobaoConfig())
        data = {"data": {"data": {"GQL_getPageModulesData": {
            "test": {"items": {"schemeList": items}}
        }}}}
        found, auctions = collector._extract_auction_result(data, "测试")
        self.assertTrue(found)
        self.assertEqual([a.item_id for a in auctions], ["4", "5", "6", "7"])
        self.assertEqual(auctions[1].status_text, "正在进行")
        report = AuctionFormatter().format({"taobao": {"测试": auctions}})
        self.assertIn("共获取：**4** 条", report)
        for index in range(4):
            self.assertNotIn(f"拍品{index}", report)


if __name__ == "__main__":
    unittest.main()
