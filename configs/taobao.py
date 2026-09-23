'''
Author: liuhanchuan 1005293916
Date: 2026-09-23 06:57:52
LastEditors: liuhanchuan 1005293916
LastEditTime: 2026-09-23 15:40:25
FilePath: /auction-monitor-dingtalk/configs/taobao.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from dataclasses import dataclass


@dataclass(frozen=True)
class TaobaoConfig:
    enabled: bool = True
    search_url: str = (
        "https://zc-paimai.taobao.com/"
        "wow/pm/default/pc/zichansearch"
    )
    target_api: str = "mtop.taobao.datafront.invoke.auctionwalle"
    province: str = "湖北"
    city: str = "武汉"
    district: str = "洪山"
    location_code: str = "420111"
    headless: bool = True
    navigation_timeout_ms: int = 60_000
    action_timeout_ms: int = 10_000
    response_timeout_ms: int = 30_000


TAOBAO_CONFIG = TaobaoConfig()
