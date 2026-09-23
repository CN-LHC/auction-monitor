import base64
import hashlib
import hmac
import time
from urllib.parse import quote_plus

import httpx

from configs.dingtalk import DingTalkConfig
from notifiers.base import BaseNotifier


class DingTalkNotifier(BaseNotifier):
    # 钉钉限制 20000 bytes
    # 主动控制在 18KB，给 Markdown 标题等内容留安全空间
    MAX_BYTES = 18 * 1024

    def __init__(self, config: DingTalkConfig):
        self.config = config

    def send(self, message: str) -> None:
        if not self.config.webhook:
            raise ValueError(
                "未配置 DINGTALK_WEBHOOK，"
                "请检查 .env 文件。"
            )

        # 1. 自动拆分
        chunks = self._split_message(message)

        total = len(chunks)

        print(
            f"钉钉消息大小："
            f"{len(message.encode('utf-8'))} bytes"
        )
        print(f"自动拆分为 {total} 条消息")

        # 2. 逐条发送
        for index, chunk in enumerate(chunks, start=1):
            if total > 1:
                title = (
                    f"{self.config.title} "
                    f"（{index}/{total}）"
                )

                content = (
                    f"## {title}\n\n"
                    f"{chunk}"
                )
            else:
                title = self.config.title
                content = chunk

            size = len(content.encode("utf-8"))

            print(
                f"正在发送钉钉消息 "
                f"{index}/{total}，"
                f"{size} bytes"
            )

            self._send_one(
                title=title,
                message=content,
            )

            # 多条消息之间稍微间隔一下
            if index < total:
                time.sleep(1)

        print(
            f"✓ 钉钉消息推送完成，共 {total} 条"
        )

    def _send_one(
        self,
        title: str,
        message: str,
    ) -> None:
        url = self._build_webhook_url()

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": message,
            },
        }

        response = httpx.post(
            url,
            json=payload,
            timeout=self.config.timeout_seconds,
        )

        response.raise_for_status()

        data = response.json()

        if data.get("errcode") != 0:
            raise RuntimeError(
                "钉钉推送失败："
                f"errcode={data.get('errcode')}, "
                f"errmsg={data.get('errmsg')}"
            )

    def _split_message(
        self,
        message: str,
    ) -> list[str]:
        """
        按 Markdown 段落拆分消息。

        规则：
        1. 优先按照空行拆分，尽量保证一个拍品不被拆开。
        2. 每条消息最大 18KB。
        3. 如果单个段落超过 18KB，再按字符安全拆分。
        4. 使用 UTF-8 bytes 计算，而不是 len(str)。
        """

        if not message:
            return ["暂无拍卖数据"]

        # 给分页标题留空间
        safe_limit = self.MAX_BYTES - 1024

        # 本身没有超限
        if len(message.encode("utf-8")) <= safe_limit:
            return [message]

        blocks = message.split("\n\n")

        chunks: list[str] = []
        current_blocks: list[str] = []

        for block in blocks:
            if not block:
                continue

            candidate_blocks = (
                current_blocks + [block]
            )

            candidate = "\n\n".join(
                candidate_blocks
            )

            candidate_size = len(
                candidate.encode("utf-8")
            )

            # 当前消息还放得下
            if candidate_size <= safe_limit:
                current_blocks.append(block)
                continue

            # 当前消息已经有内容
            # 先保存当前消息
            if current_blocks:
                chunks.append(
                    "\n\n".join(current_blocks)
                )

                current_blocks = []

            # 单独一个 block 就已经超限
            if (
                len(block.encode("utf-8"))
                > safe_limit
            ):
                large_chunks = (
                    self._split_large_block(
                        block,
                        safe_limit,
                    )
                )

                chunks.extend(
                    large_chunks[:-1]
                )

                if large_chunks:
                    current_blocks = [
                        large_chunks[-1]
                    ]

            else:
                current_blocks = [block]

        # 最后一部分
        if current_blocks:
            chunks.append(
                "\n\n".join(current_blocks)
            )

        return chunks

    @staticmethod
    def _split_large_block(
        text: str,
        max_bytes: int,
    ) -> list[str]:
        """
        极端情况下单个 Markdown 段落超过限制，
        按 UTF-8 字节安全拆分。

        不直接切 bytes，避免把中文 UTF-8 字符切坏。
        """

        chunks: list[str] = []
        current_chars: list[str] = []
        current_bytes = 0

        for char in text:
            char_bytes = len(
                char.encode("utf-8")
            )

            if (
                current_chars
                and current_bytes + char_bytes
                > max_bytes
            ):
                chunks.append(
                    "".join(current_chars)
                )

                current_chars = []
                current_bytes = 0

            current_chars.append(char)
            current_bytes += char_bytes

        if current_chars:
            chunks.append(
                "".join(current_chars)
            )

        return chunks

    def _build_webhook_url(self) -> str:
        if not self.config.secret:
            return self.config.webhook

        timestamp = str(
            round(time.time() * 1000)
        )

        string_to_sign = (
            f"{timestamp}\n"
            f"{self.config.secret}"
        )

        digest = hmac.new(
            self.config.secret.encode(
                "utf-8"
            ),
            string_to_sign.encode(
                "utf-8"
            ),
            digestmod=hashlib.sha256,
        ).digest()

        sign = quote_plus(
            base64.b64encode(
                digest
            ).decode("utf-8")
        )

        separator = (
            "&"
            if "?" in self.config.webhook
            else "?"
        )

        return (
            f"{self.config.webhook}"
            f"{separator}"
            f"timestamp={timestamp}"
            f"&sign={sign}"
        )