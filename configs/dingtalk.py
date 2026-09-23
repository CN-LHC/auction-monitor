import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class DingTalkConfig:
    enabled: bool = True
    webhook: str = os.getenv("DINGTALK_WEBHOOK", "")
    secret: str = os.getenv("DINGTALK_SECRET", "")
    timeout_seconds: float = 15.0
    title: str = "拍卖监控日报"


DINGTALK_CONFIG = DingTalkConfig()
