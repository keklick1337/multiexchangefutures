import math
import typing as t
from logging import Logger

class BaseFuturesTrade:
    """
    Универсальный базовый класс для торговли на фьючерсах.
    Все методы помечены как NotImplemented, чтобы вы могли переопределить их для любой нужной вам биржи.
    Класс специально сделан синхронным для упрощения вызова (при необходимости 
    можно вызывать через asyncio.to_thread(...) или переопределять методы асинхронно).
    """

    def __init__(self):
        """
        Конструктор базового класса. 
        Можно хранить в self всё, что требуется (API-клиент, ключи и т.д.).
        """
        pass

    @classmethod
    def create(cls, api_key: str, secret_key: str, logger: t.Optional[Logger] = None):
        """
        Фабричный метод для создания экземпляра класса (инициализирует все внутренние подключения, клиенты и т.п.)
        """
        raise NotImplementedError("create() is not implemented in the base class")

    def close(self):
        """
        Закрывает сессии, соединения и иные ресурсы, если это нужно.
        """
        raise NotImplementedError("close() is not implemented in the base class")

    def get_account_info(self) -> dict:
        """
        Получает информацию об аккаунте (балансы, лимиты и т.д.)
        """
        raise NotImplementedError("get_account_info() is not implemented in the base class")

    def get_futures_account_info(self) -> dict:
        """
        Получает информацию о фьючерсном счёте (балансы, текущие позиции, комиссия и т.п.)
        """
        raise NotImplementedError("get_futures_account_info() is not implemented in the base class")

    def get_max_leverage_for_symbol(self, symbol: str) -> int:
        """
        Возвращает максимально возможное плечо для указанного символа.
        """
        raise NotImplementedError("get_max_leverage_for_symbol() is not implemented in the base class")

    def get_trading_symbols(self) -> t.List[dict]:
        """
        Возвращает список доступных символов/инструментов на фьючерсном рынке.
        """
        raise NotImplementedError("get_trading_symbols() is not implemented in the base class")

    def get_open_futures_positions(self) -> t.List[dict]:
        """
        Возвращает список текущих открытых позиций.
        """
        raise NotImplementedError("get_open_futures_positions() is not implemented in the base class")

    def get_all_orders(self) -> t.List[dict]:
        """
        Возвращает список всех ордеров (включая историю).
        """
        raise NotImplementedError("get_all_orders() is not implemented in the base class")

    def get_open_orders(self) -> t.List[dict]:
        """
        Возвращает список открытых (активных) ордеров.
        """
        raise NotImplementedError("get_open_orders() is not implemented in the base class")

    def get_min_quantity(self, symbol_info: dict) -> float:
        """
        Возвращает минимально допустимое количество для символа, исходя из символ-инфо.
        """
        raise NotImplementedError("get_min_quantity() is not implemented in the base class")

    def futures_change_leverage(self, symbol: str, leverage: int) -> dict:
        """
        Меняет плечо (leverage) для конкретного символа.
        """
        raise NotImplementedError("futures_change_leverage() is not implemented in the base class")

    def calculate_quantity_from_usdt(
        self, 
        symbol: str, 
        usdt_amount: float, 
        leverage: int, 
        adjust_to_min_notional: bool = True, 
        take_profit_targets: t.Optional[t.List[float]] = None
    ) -> float:
        """
        Высчитывает количество контракта, исходя из суммы usdt_amount и указанного плеча.
        Параметр adjust_to_min_notional указывает, нужно ли автоматически 
        увеличивать количество до минимально допустимого номинала. 
        """
        raise NotImplementedError("calculate_quantity_from_usdt() is not implemented in the base class")

    def round_more(self, number: float, digits: int) -> float:
        """
        Округляет число number вверх (ceil) до заданного количества знаков digits.
        """
        raise NotImplementedError("round_more() is not implemented in the base class")

    def get_quantity_precision(self, symbol: str) -> int:
        """
        Возвращает точность (количество знаков после запятой) для количества (LOT_SIZE).
        """
        raise NotImplementedError("get_quantity_precision() is not implemented in the base class")

    def get_price_precision(self, symbol: str) -> int:
        """
        Возвращает точность для цены (PRICE_FILTER).
        """
        raise NotImplementedError("get_price_precision() is not implemented in the base class")

    def get_current_price(self, symbol: str) -> float:
        """
        Возвращает текущую рыночную цену для символа.
        """
        raise NotImplementedError("get_current_price() is not implemented in the base class")

    def get_trading_mode(self) -> str:
        """
        Определяет режим торговли (ONE_WAY или HEDGE), 
        если на бирже поддерживаются разные режимы.
        """
        raise NotImplementedError("get_trading_mode() is not implemented in the base class")

    def create_order(
        self, 
        symbol: str, 
        side: str, 
        order_type: str, 
        quantity: float, 
        price: t.Optional[float] = None, 
        stop_loss: t.Optional[float] = None, 
        take_profit_targets: t.Optional[t.List[float]] = None, 
        leverage: int = 1
    ) -> t.Optional[dict]:
        """
        Создаёт ордер (market/limit) с возможными стоп-лоссом и тейк-профитами.
        """
        raise NotImplementedError("create_order() is not implemented in the base class")

    def create_stop_loss(
        self, 
        symbol: str, 
        side: str, 
        stop_loss: t.Optional[float] = None, 
        trading_mode: t.Optional[str] = None
    ) -> None:
        """
        Создаёт стоп-лосс ордер (если stop_loss != None). 
        """
        raise NotImplementedError("create_stop_loss() is not implemented in the base class")

    def bulk_create_take_profits(
        self, 
        symbol: str, 
        side: str, 
        quantity: float, 
        take_profit_targets: t.Optional[t.List[float]] = None, 
        trading_mode: t.Optional[str] = None
    ) -> None:
        """
        Создаёт несколько тейк-профит ордеров (если есть список целей).
        """
        raise NotImplementedError("bulk_create_take_profits() is not implemented in the base class")

    def close_stop_loss_orders(self, symbol: str, position_side: str) -> None:
        """
        Закрывает все STOP_MARKET ордера (стоп-лоссы) для данного symbol и position_side.
        """
        raise NotImplementedError("close_stop_loss_orders() is not implemented in the base class")

    def close_take_profit_orders(self, symbol: str, position_side: str) -> None:
        """
        Закрывает все TAKE_PROFIT_MARKET ордера (тейк-профиты) для данного symbol и position_side.
        """
        raise NotImplementedError("close_take_profit_orders() is not implemented in the base class")

    def get_min_notional(self, symbol: str) -> float:
        """
        Возвращает минимальный номинал (MIN_NOTIONAL) для заданного символа.
        """
        raise NotImplementedError("get_min_notional() is not implemented in the base class")

    def close_order(self, symbol: str, order_id: int) -> dict:
        """
        Отменяет (закрывает) ордер по его ID.
        """
        raise NotImplementedError("close_order() is not implemented in the base class")

    def get_futures_balance(self) -> float:
        """
        Возвращает доступный баланс на фьючерсном аккаунте (по USDT или другой валюте).
        """
        raise NotImplementedError("get_futures_balance() is not implemented in the base class")

    def futures_create_order(self, **kwargs) -> dict:
        """
        Внутренний метод (или публичный) для непосредственного создания ордера на фьючерсном рынке.
        """
        raise NotImplementedError("futures_create_order() is not implemented in the base class")

    def adjust_take_profits(self) -> None:
        """
        Пример вспомогательной логики, которая может переустанавливать 
        тейк-профиты исходя из текущих открытых позиций. 
        """
        raise NotImplementedError("adjust_take_profits() is not implemented in the base class")

    def get_free_margin(self) -> float:
        """
        Возвращает доступную маржу (свободные средства) для торговли.
        """
        raise NotImplementedError("get_free_margin() is not implemented in the base class")
