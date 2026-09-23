from dataclasses import dataclass, field


@dataclass
class Auction:
    source: str
    item_id: str
    title: str
    url: str
    keyword: str = ""
    status: str = ""
    status_text: str = ""
    price: str = ""
    price_unit: str = ""
    initial_price: str = ""
    initial_price_unit: str = ""
    time_prefix: str = ""
    time_centre: str = ""
    time_suffix: str = ""
    end_time: str = ""
    views: int | str = 0
    apply_count: int | str = 0
    bid_count: int | str = 0
    subscribe_count: int | str = 0
    shop_name: str = ""
    image: str = ""
    benefits: list[str] = field(default_factory=list)
