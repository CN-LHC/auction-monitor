import json
from urllib.parse import parse_qs

from playwright.sync_api import (
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)

from collectors.base import BaseCollector
from configs.taobao import TaobaoConfig
from models.auction import Auction
from utils.url import absolute_url


class TaobaoCollector(BaseCollector):
    name = "taobao"

    def __init__(self, config: TaobaoConfig):
        self.config = config

    def search(self, keywords: list[str]) -> dict[str, list[Auction]]:
        results: dict[str, list[Auction]] = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.config.headless
            )
            context = browser.new_context()
            page = context.new_page()

            try:
                print("打开淘宝资产搜索页面")

                page.goto(
                    self.config.search_url,
                    wait_until="domcontentloaded",
                    timeout=self.config.navigation_timeout_ms,
                )

                page.locator("#input").wait_for(
                    state="visible",
                    timeout=self.config.response_timeout_ms,
                )

                for index, keyword in enumerate(keywords, start=1):
                    print()
                    print(f"[{index}/{len(keywords)}]")

                    try:
                        results[keyword] = self._search_keyword(
                            page,
                            keyword,
                        )
                    except Exception as exc:
                        print(f"✗ {keyword} 搜索失败：{exc}")
                        results[keyword] = []

            finally:
                browser.close()

        return results

    def _search_keyword(
        self,
        page,
        keyword: str,
    ) -> list[Auction]:
        print()
        print("#" * 70)
        print(f"开始搜索：{keyword}")
        print("#" * 70)

        search_input = page.locator("#input")
        search_input.wait_for(
            state="visible",
            timeout=self.config.response_timeout_ms,
        )
        search_input.fill(keyword)

        search_button = page.get_by_text(
            "搜索",
            exact=True,
        )
        search_button.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        print("① 点击搜索，等待无区域关键词 Response")

        try:
            with page.expect_response(
                lambda response: self._is_keyword_search_request(
                    response.request,
                    keyword,
                ),
                timeout=self.config.response_timeout_ms,
            ) as response_info:
                search_button.click()

            keyword_response = response_info.value

        except PlaywrightTimeoutError:
            print(f"✗ 关键词搜索超时：{keyword}")
            return []

        success, _, ret = self._response_success(
            keyword_response
        )

        if not success:
            print(f"✗ 关键词搜索接口异常：{ret}")
            return []

        print("✓ 关键词搜索完成")

        try:
            district = self._prepare_location(page)
        except PlaywrightTimeoutError as exc:
            print(
                "✗ 区域三级联动失败："
                f"{self.config.province} → "
                f"{self.config.city} → "
                f"{self.config.district}"
            )
            print(exc)
            return []

        print(
            "② 等待最终区域搜索："
            f"keyword={keyword}, "
            f"locationCodes=[{self.config.location_code}]"
        )

        try:
            with page.expect_response(
                lambda response: self._is_final_search_request(
                    response.request,
                    keyword,
                ),
                timeout=self.config.response_timeout_ms,
            ) as response_info:
                district.click()

            final_response = response_info.value

        except PlaywrightTimeoutError:
            print("✗ 最终区域搜索超时")
            return []

        success, data, ret = self._response_success(
            final_response
        )

        if not success or data is None:
            print(f"✗ 最终搜索接口异常：{ret}")
            return []

        found_result, auctions = self._extract_auction_result(
            data,
            keyword,
        )

        if not found_result:
            print("✗ Response 中没有找到 schemeList")
            return []

        print(
            f"✓ {keyword} 搜索完成，"
            f"找到 {len(auctions)} 个拍品"
        )

        return auctions

    def _prepare_location(self, page):
        print(
            "选择区域："
            f"{self.config.province} → "
            f"{self.config.city} → "
            f"{self.config.district}"
        )

        city = self._select_province(page)
        district = self._select_city(page, city)

        return district

    def _select_province(self, page):
        province = page.get_by_text(
            self.config.province,
            exact=True,
        ).first

        province.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        print(f"→ 选择省份：{self.config.province}")
        province.click()

        container = self._get_location_container(page)
        container.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        city_lists = container.locator(
            'div[class*="pc-filter--cityList"]'
        )

        city_level = city_lists.nth(0)
        city_level.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        city = city_level.get_by_text(
            self.config.city,
            exact=True,
        )

        city.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        print(
            f"✓ {self.config.province} 下级城市"
            f" {self.config.city} 已加载"
        )

        return city

    def _select_city(self, page, city):
        print(f"→ 选择城市：{self.config.city}")
        city.click()

        container = self._get_location_container(page)

        district_level = container.locator(
            'div[class*="pc-filter--cityList"]'
        ).nth(1)

        district_level.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        district = district_level.get_by_text(
            self.config.district,
            exact=True,
        )

        district.wait_for(
            state="visible",
            timeout=self.config.action_timeout_ms,
        )

        print(
            f"✓ {self.config.city} 下级区域"
            f" {self.config.district} 已加载"
        )

        return district

    @staticmethod
    def _get_location_container(page):
        return page.locator(
            'div[class*="pc-filter--cityListContainer"]'
        ).first

    def _is_target_request(self, request) -> bool:
        url = request.url.lower()

        return (
            self.config.target_api in url
            and "type=originaljson" in url
        )

    def _is_keyword_search_request(
        self,
        request,
        keyword: str,
    ) -> bool:
        if not self._is_target_request(request):
            return False

        info = self._parse_search_request(request)

        if not info:
            return False

        if info["keyword"] != keyword:
            return False

        return not info.get("location_codes", [])

    def _is_final_search_request(
        self,
        request,
        keyword: str,
    ) -> bool:
        if not self._is_target_request(request):
            return False

        info = self._parse_search_request(request)

        if not info:
            return False

        if info["keyword"] != keyword:
            return False

        location_codes = info.get(
            "location_codes",
            [],
        )

        if not isinstance(location_codes, list):
            return False

        return str(self.config.location_code) in {
            str(code) for code in location_codes
        }

    @staticmethod
    def _parse_search_request(request):
        try:
            payload = request.post_data_json
        except Exception:
            payload = None

        # MTOP 常见的是 application/x-www-form-urlencoded。
        # 如果 Playwright 没有直接解析成功，则手动解析 post_data。
        if not isinstance(payload, dict):
            raw_post_data = request.post_data or ""

            try:
                form = parse_qs(raw_post_data)
                raw_data = form.get("data", [None])[0]

                if raw_data is None:
                    return None

                payload = {
                    "data": raw_data
                }

            except Exception:
                return None

        try:
            data_value = payload.get("data")

            if isinstance(data_value, str):
                data_value = json.loads(data_value)

            if not isinstance(data_value, dict):
                return None

            df_variables = data_value.get(
                "dfVariables"
            )

            if isinstance(df_variables, str):
                df_variables = json.loads(
                    df_variables
                )

            if not isinstance(df_variables, dict):
                return None

            context = df_variables.get("context")

            if not isinstance(context, dict):
                return None

            for key, value in context.items():
                if not key.endswith(":items"):
                    continue

                if isinstance(value, str):
                    value = json.loads(value)

                if not isinstance(value, dict):
                    continue

                return {
                    "keyword": value.get(
                        "keyword",
                        "",
                    ),
                    "location_codes": value.get(
                        "locationCodes",
                        [],
                    ),
                    "page": value.get(
                        "page",
                        "",
                    ),
                }

        except Exception:
            return None

        return None

    @staticmethod
    def _response_success(response):
        try:
            data = response.json()
            ret = data.get("ret", [])

            success = any(
                "SUCCESS" in str(value)
                for value in ret
            )

            return success, data, ret

        except Exception as exc:
            return False, None, [str(exc)]

    def _extract_auction_result(
        self,
        data: dict,
        keyword: str,
    ) -> tuple[bool, list[Auction]]:
        gql_data = (
            data
            .get("data", {})
            .get("data", {})
            .get(
                "GQL_getPageModulesData",
                {},
            )
        )

        if not isinstance(gql_data, dict):
            return False, []

        found_result = False
        auctions: list[Auction] = []

        for module_id, module_data in gql_data.items():
            if not isinstance(module_data, dict):
                continue

            items = module_data.get("items")

            if not isinstance(items, dict):
                continue

            if "schemeList" not in items:
                continue

            scheme_list = items.get("schemeList")

            if not isinstance(scheme_list, list):
                continue

            found_result = True

            print(
                f"  ✓ 结果模块 {module_id}："
                f"{len(scheme_list)} 条"
            )

            for item in scheme_list:
                if not self._is_real_auction_item(item):
                    continue

                # 已结束的拍品不进入汇总和钉钉上报结果。
                if item.get("status") == "end":
                    continue

                auctions.append(
                    self._parse_item(
                        item,
                        keyword,
                    )
                )

        return found_result, auctions

    @staticmethod
    def _is_real_auction_item(item: dict) -> bool:
        return (
            isinstance(item, dict)
            and bool(item.get("itemId"))
            and bool(item.get("auctionTitle"))
            and bool(item.get("auctionLink"))
        )

    @staticmethod
    def _format_status(item: dict) -> str:
        status = item.get("status")

        status_map = {
            "before": "即将开始",
            "doing": "正在进行",
            "end": "已结束",
        }

        return status_map.get(
            status,
            item.get("timeSuffix")
            or status
            or "未知",
        )

    def _parse_item(
        self,
        item: dict,
        keyword: str,
    ) -> Auction:
        return Auction(
            source=self.name,
            item_id=str(item.get("itemId", "")),
            title=item.get("auctionTitle", ""),
            url=absolute_url(
                item.get("auctionLink", "")
            ),
            keyword=keyword,
            status=item.get("status", ""),
            status_text=self._format_status(item),
            price=item.get("price", ""),
            price_unit=item.get("priceUnit", ""),
            initial_price=item.get(
                "displayInitialPrice",
                "",
            ),
            initial_price_unit=item.get(
                "displayInitialPriceUnit",
                "",
            ),
            time_prefix=item.get(
                "timePrefix",
                "",
            ),
            time_centre=item.get(
                "timeCentre",
                "",
            ),
            time_suffix=item.get(
                "timeSuffix",
                "",
            ),
            end_time=item.get(
                "endTimeConfig",
                "",
            ),
            views=item.get("pv", 0),
            apply_count=item.get(
                "applyCnt",
                0,
            ),
            bid_count=item.get(
                "bidCnt",
                0,
            ),
            subscribe_count=item.get(
                "subscribeCnt",
                0,
            ),
            shop_name=item.get(
                "shopName",
                "",
            ),
            image=absolute_url(
                item.get("pictureUrl", "")
            ),
            benefits=item.get(
                "auctionBenefits",
                [],
            ) or [],
        )
