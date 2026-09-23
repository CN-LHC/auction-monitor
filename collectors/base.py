from abc import ABC, abstractmethod

from models.auction import Auction


class BaseCollector(ABC):
    name = "base"

    @abstractmethod
    def search(self, keywords: list[str]) -> dict[str, list[Auction]]:
        raise NotImplementedError
