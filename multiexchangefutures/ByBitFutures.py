import typing as t
from logging import Logger

from pybit.unified_trading import HTTP as BybitHTTP

from .base_futures_trade import BaseFuturesTrade


class BybitFuturesTrade(BaseFuturesTrade):
    """
    Пример реальной имплементации базового класса для торговли на фьючерсах через Bybit.
    Использует неофициальную библиотеку pybit (unified_trading HTTP).
    Методы синхронные для упрощения логики.
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        logger: t.Optional[Logger] = None,
        testnet: bool = False
    ):
        """
        Конструктор класса BybitFuturesTrade.
        :param api_key: Ваш API ключ для Bybit.
        :param api_secret: Ваш секретный ключ для Bybit.
        :param logger: Опциональный логгер.
        :param testnet: Флаг для работы c тестнетом (по умолчанию False).
        """
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.logger = logger

        # Создаём HTTP-клиент библиотеки pybit для работы с Bybit
        self._session = BybitHTTP(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=testnet,
            # Можно задать ещё настройки (timeOut, recv_window и т.д.)
        )

    @classmethod
    def create(
        cls, 
        api_key: str, 
        api_secret: str, 
        logger: t.Optional[Logger] = None, 
        testnet: bool = False
    ) -> "BybitFuturesTrade":
        """
        Фабричный метод для создания экземпляра BybitFuturesTrade.

        :param api_key: API ключ для Bybit
        :param api_secret: Секретный ключ для Bybit
        :param logger: Опциональный логгер
        :param testnet: Флаг для работы c тестнетом (по умолчанию False)
        :return: Экземпляр BybitFuturesTrade
        """
        return cls(api_key, api_secret, logger, testnet)

    def close(self) -> None:
        """
        Закрывает HTTP-сессию, если нужно (в pybit обычно нет необходимости явно закрывать).
        """
        # В библиотеке pybit нет специальных методов для закрытия HTTP-сессии,
        # но если захотите, можно чисто логгировать факт "закрытия".
        if self.logger:
            self.logger.info("BybitFuturesTrade session closed")

    def get_account_info(self) -> dict:
        """
        Получает информацию об аккаунте из Bybit.
        Для unified account можно вызывать что-то вроде `GET_WALLET_BALANCE` или `GET_ACCOUNT_INFO`.
        """
        # Пример запроса баланса. Категорию указываем "CONTRACT" или "UNIFIED".
        # Подробнее см. в документации pybit.
        return self._session.get_account_info(accountType="CONTRACT")

    def get_futures_account_info(self) -> dict:
        """
        Получает расширенную информацию о фьючерсном счёте (например, состояние кошелька).
        """
        return self._session.get_wallet_balance(accountType="CONTRACT")

    def get_max_leverage_for_symbol(self, symbol: str) -> int:
        """
        Получает максимально возможное плечо для конкретного символа.
        Для Bybit придётся использовать другой эндпоинт (set_leverage / get_positions и т.д.).
        В pybit нет прямого "get max leverage", поэтому будем возвращать, скажем, 100.
        """
        # В Bybit нет явного эндпоинта для "get max leverage", 
        # поэтому для примера вернём какое-то типовое значение (100).
        # В реальности надо смотреть инфу по риск-лимитам.
        return 100

    def get_trading_symbols(self) -> t.List[dict]:
        """
        Получаем список торговых инструментов (фьючерсных).
        В Bybit это может быть get_instruments_info, указывая соответствующие категории.
        """
        resp = self._session.get_instruments_info(category="linear")
        # resp = {
        #   "retCode": 0,
        #   "retMsg": "OK",
        #   "result": {
        #       "category":"linear",
        #       "list": [...]
        #   },
        #   ...
        # }
        # Возвращаем список "list" или сам респонс как есть.
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            return resp["result"]["list"]
        return []

    def get_open_futures_positions(self) -> t.List[dict]:
        """
        Возвращает список открытых позиций.
        """
        # category="linear" для USDT Perpetual, "inverse" для Inverse и т.д.
        resp = self._session.get_positions(category="linear")
        # Ответ выглядит примерно так:
        # {
        #   "retCode":0,
        #   "retMsg":"OK",
        #   "result":{
        #       "list":[ ... ]
        #   }, ...
        # }
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            return resp["result"]["list"]
        return []

    def get_all_orders(self) -> t.List[dict]:
        """
        Возвращаем все (исторические) ордера. 
        В Bybit можно использовать get_order_history().
        """
        resp = self._session.get_order_history(category="linear")
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            return resp["result"]["list"]
        return []

    def get_open_orders(self) -> t.List[dict]:
        """
        Возвращаем активные ордера (открытые).
        """
        resp = self._session.get_open_orders(category="linear")
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            return resp["result"]["list"]
        return []

    def get_min_quantity(self, symbol_info: dict) -> float:
        """
        Получаем минимальный размер контракта на Bybit.
        (В реальности надо смотреть спецификацию на symbol_info)
        """
        # У Bybit для каждого символа будет специфическое поле. Для упрощения вернём 0.001.
        return 0.001

    def futures_change_leverage(self, symbol: str, leverage: int) -> dict:
        """
        Устанавливаем новое плечо для символа.
        """
        resp = self._session.set_leverage(
            category="linear",
            symbol=symbol,
            buyLeverage=str(leverage),
            sellLeverage=str(leverage),
        )
        return resp

    def calculate_quantity_from_usdt(
        self, 
        symbol: str, 
        usdt_amount: float, 
        leverage: int, 
        adjust_to_min_notional: bool = True, 
        take_profit_targets: t.Optional[t.List[float]] = None
    ) -> float:
        """
        Пример калькуляции количества: (usdt_amount * leverage) / current_price
        """
        price = self.get_current_price(symbol)
        if price <= 0:
            raise ValueError("Price is 0 or negative, cannot calculate quantity.")

        # Например, ( usdt_amount * leverage ) / price
        quantity = (usdt_amount * leverage) / price

        # Для упрощения — округлим quantity
        return float(self.round_more(quantity, 3))

    def round_more(self, number: float, digits: int) -> float:
        """
        Округляем число вверх (ceil) до digits знаков после запятой.
        """
        import math
        scale = 10 ** digits
        return math.ceil(number * scale) / scale

    def get_quantity_precision(self, symbol: str) -> int:
        """
        Возвращает точность (примерно) для ордера по symbol. 
        (В реальном коде нужно смотреть список фильтров).
        """
        return 3  # упрощение

    def get_price_precision(self, symbol: str) -> int:
        """
        Возвращает точность цены (примерно).
        """
        return 2  # упрощение

    def get_current_price(self, symbol: str) -> float:
        """
        Возвращаем текущую цену для symbol.
        """
        resp = self._session.get_tickers(category="linear", symbol=symbol)
        # Результат обычно:
        # {
        #   "retCode":0,
        #   "retMsg":"OK",
        #   "result":{
        #       "list":[
        #         {
        #           "symbol":"BTCUSDT",
        #           "lastPrice":"27213.00",
        #           ...
        #         }
        #       ]
        #   },
        # }
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            for item in resp["result"]["list"]:
                if item["symbol"] == symbol:
                    return float(item["lastPrice"])
        return 0.0

    def get_trading_mode(self) -> str:
        """
        Определяем режим торговли (ONE_WAY / HEDGE).
        В Bybit, если position mode = "MergedSingle", это условно one-way.
        Если "BothSide", тогда hedge.
        Для примера вернём "ONE_WAY".
        """
        # В pybit v5 можно смотреть switch_position_mode / get_positions и т.д.
        # Здесь делаем упрощённо:
        return "ONE_WAY"

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
        Создание ордера в Bybit (market или limit).
        """
        # Устанавливаем плечо
        self.futures_change_leverage(symbol, leverage)

        params = {
            "category": "linear",
            "symbol": symbol,
            "side": side.capitalize(),    # Bybit принимает "Buy" / "Sell"
            "orderType": order_type.capitalize(), # "Market" / "Limit"
            "qty": str(quantity),  # qty строкой
            # "timeInForce": "GTC", # можно указать, если Limit
        }

        if order_type.upper() == "LIMIT" and price is not None:
            params["price"] = str(price)
            # если нужно указать TIF
            params["timeInForce"] = "GoodTillCancel"

        # Отправляем
        resp = self._session.place_order(**params)
        return resp

    def create_stop_loss(
        self,
        symbol: str,
        side: str,
        stop_loss: t.Optional[float] = None,
        trading_mode: t.Optional[str] = None
    ) -> None:
        """
        Создаём стоп-лосс (если stop_loss указан). 
        По Bybit v5 можно делать set_trading_stop, 
        но здесь в демо-стиле "MARKET STOP" ордера нет в упрощённом API.
        """
        if stop_loss is None:
            return
        # Пример: используем set_trading_stop
        # "side": "Buy" -> SL для лонга
        # "stopLoss": price
        try:
            self._session.set_trading_stop(
                category="linear",
                symbol=symbol,
                stopLoss=str(stop_loss),
                # Можно задать позицию (side). 
                # Но Bybit v5 может быть tricky — нужно указывать positionIdx, если hedge.
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to create stop-loss: {e}")

    def bulk_create_take_profits(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_targets: t.Optional[t.List[float]] = None,
        trading_mode: t.Optional[str] = None
    ) -> None:
        """
        Упрощённый вариант создания тейк-профитов.
        В реальном Bybit (v5) обычно надо вызывать set_trading_stop (takeProfit=...),
        Либо несколько лимитных ордеров в противоположную сторону.
        """
        if not take_profit_targets:
            return

        # Для упрощения сделаем один tp — возьмём первый в списке
        tp_price = take_profit_targets[0]
        try:
            self._session.set_trading_stop(
                category="linear",
                symbol=symbol,
                takeProfit=str(tp_price),
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to set take-profit: {e}")

    def close_stop_loss_orders(self, symbol: str, position_side: str) -> None:
        """
        В Bybit v5 нет прямого "close_stop_loss_orders", 
        но можно отменять связанные ордера или обновлять через set_trading_stop.
        """
        pass  # Не реализовано для упрощения

    def close_take_profit_orders(self, symbol: str, position_side: str) -> None:
        """
        Аналогично закрываем TP-ордера — в Bybit можно отменять связанные conditional orders.
        """
        pass  # Не реализовано для упрощения

    def get_min_notional(self, symbol: str) -> float:
        """
        Возвращает минимальный номинал (для упрощения — 5 USDT).
        """
        return 5.0

    def close_order(self, symbol: str, order_id: int) -> dict:
        """
        Отменяет (закрывает) ордер по его ID.
        """
        # В Bybit v5 cancel_order(..., orderId="...")
        resp = self._session.cancel_order(
            category="linear",
            symbol=symbol,
            orderId=str(order_id)
        )
        return resp

    def get_futures_balance(self) -> float:
        """
        Возвращает общий баланс USDT (или другой валюты) для работы.
        """
        resp = self._session.get_wallet_balance(accountType="CONTRACT")
        # Обычно resp["result"]["list"] -> [{ "coin":"USDT", "walletBalance": ... }, ...]
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            for coin_info in resp["result"]["list"]:
                if coin_info["coin"] == "USDT":
                    return float(coin_info["walletBalance"])
        return 0.0

    def futures_create_order(self, **kwargs) -> dict:
        """
        В Bybit просто обёртка над place_order.
        """
        return self._session.place_order(**kwargs)

    def adjust_take_profits(self) -> None:
        """
        Механика переустановки TP. 
        Здесь просто пустая реализация.
        """
        pass

    def get_free_margin(self) -> float:
        """
        Возвращает "свободную" маржу (доступные средства). 
        В Bybit можно смотреть get_wallet_balance или get_account_info, 
        но точное поле "availableBalance" зависит от того, что вернёт API.
        """
        resp = self._session.get_wallet_balance(accountType="CONTRACT")
        if resp["retCode"] == 0 and "result" in resp and "list" in resp["result"]:
            for coin_info in resp["result"]["list"]:
                if coin_info["coin"] == "USDT":
                    # В unified margin может по-другому называться, 
                    # но для простоты возьмём 'availableToWithdraw'
                    if "availableBalance" in coin_info:
                        return float(coin_info["availableBalance"])
                    elif "availableToWithdraw" in coin_info:
                        return float(coin_info["availableToWithdraw"])
        return 0.0

