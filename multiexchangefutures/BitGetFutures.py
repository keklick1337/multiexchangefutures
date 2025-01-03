import math
import typing as t
from logging import Logger
from .base_futures_trade import BaseFuturesTrade
from pybitget import Client

# Заглушка: Укажите реальные константы/эндпоинты/переменные, если нужно
BITGET_PRODUCT_TYPE = "umcbl"  # USDT-маржинальные фьючерсы
BITGET_MARGIN_COIN = "USDT"    # USDT как маржинальная монета

class BitGetFuturesTrade(BaseFuturesTrade):
    """
    Пример реализации торговли фьючерсами на BitGet на основе базового класса BaseFuturesTrade.
    Для упрощения используется productType="umcbl" (USDT margined futures) и marginCoin="USDT".
    """

    def __init__(
        self, 
        api_key: str, 
        api_secret: str, 
        passphrase: str, 
        logger: t.Optional[Logger] = None,
        use_server_time: bool = True,
        verbose: bool = False
    ):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.passphrase = passphrase
        self.logger = logger
        self.use_server_time = use_server_time
        self.verbose = verbose

        # Инициализируем клиент BitGet
        # self.client = Client(api_key, api_secret, passphrase, use_server_time=use_server_time, verbose=verbose)
        # Поскольку вы скинули класс Client напрямую, 
        # предположим, что вы сможете проинициализировать его сами:
        self.client = Client(
            api_key=self.api_key,
            api_secret_key=self.api_secret,
            passphrase=self.passphrase,
            use_server_time=self.use_server_time,
            verbose=self.verbose
        )

    @classmethod
    def create(cls, api_key: str, secret_key: str, logger: t.Optional[Logger] = None):
        """
        Создаёт экземпляр BitGetFuturesTrade.
        Пассфразу (passphrase) на BitGet надо указывать при создании API-ключа.
        Для примера берем пустую строку. 
        Если у вас есть реальная passphrase - подставьте её.
        """
        passphrase = ""  # <-- Замените на реальную passphrase, если нужна
        return cls(api_key, secret_key, passphrase, logger=logger, use_server_time=True)

    def close(self):
        """
        Завершает работу с клиентом. В BitGet Client нет отдельного метода закрытия,
        поэтому оставляем пустым.
        """
        pass

    # ========== Примеры переопределения методов BaseFuturesTrade ==========

    def get_account_info(self) -> dict:
        """
        Получает аккаунты пользователя по фьючерсам (умолч. USDT margined).
        Возвращаемый результат — словарь с полями, как есть в BitGet.
        """
        resp = self.client.mix_get_accounts(BITGET_PRODUCT_TYPE)
        # resp обычно содержит что-то вроде {"code":"00000","msg":"success","requestTime":1690000000000,"data":[...]}
        return resp

    def get_futures_account_info(self) -> dict:
        """
        Аналогично get_account_info — в BitGet нет чёткого разделения, 
        но можно, например, запросить список аккаунтов + позиций, и вернуть комбинированную инфу.
        """
        accounts = self.client.mix_get_accounts(BITGET_PRODUCT_TYPE)
        # Можете дополнительно подтянуть позиции
        positions = self.client.mix_get_all_positions(productType=BITGET_PRODUCT_TYPE)
        return {
            "accounts": accounts,
            "positions": positions
        }

    def get_max_leverage_for_symbol(self, symbol: str) -> int:
        """
        BitGet-метод для получения текущего плеча. 
        Реального "максимума" они не всегда возвращают напрямую, 
        но есть метод mix_get_leverage(symbol).
        """
        resp = self.client.mix_get_leverage(symbol)
        # В resp["data"] обычно лежит список или dict с leverage, minLeverage, maxLeverage и т.д.
        # Пример: {"code":"00000","msg":"success","data":{"symbol":"BTCUSDT_UMCBL","maxLeverage":"125","minLeverage":"1"}}
        # Парсим maxLeverage:
        try:
            max_leverage = int(resp["data"]["maxLeverage"])
        except:
            max_leverage = 50  # Наугад, если вдруг нет данных
        return max_leverage

    def get_trading_symbols(self) -> t.List[dict]:
        """
        Возвращает список доступных контрактов для USDT-маржинальных фьючерсов (umcbl).
        """
        resp = self.client.mix_get_symbols_info(BITGET_PRODUCT_TYPE)
        # resp["data"] — это список символов
        if "data" in resp:
            return resp["data"]
        return []

    def get_open_futures_positions(self) -> t.List[dict]:
        """
        Возвращает все открытые позиции для текущего productType="umcbl".
        """
        resp = self.client.mix_get_all_positions(BITGET_PRODUCT_TYPE, marginCoin=BITGET_MARGIN_COIN)
        if "data" in resp:
            # Возможно, resp["data"] — это список позиций
            return resp["data"]
        return []

    def get_all_orders(self) -> t.List[dict]:
        """
        Возвращает исторические ордера (для примера).
        Можно использовать mix_get_productType_history_orders или mix_get_history_orders.
        """
        # Здесь нужно startTime, endTime и прочие параметры, 
        # для демонстрации вызываем без них, просто вернём пустой список или заглушку
        return []

    def get_open_orders(self) -> t.List[dict]:
        """
        Возвращает открытые ордера.
        """
        resp = self.client.mix_get_all_open_orders(BITGET_PRODUCT_TYPE, BITGET_MARGIN_COIN)
        if "data" in resp:
            return resp["data"]
        return []

    def get_min_quantity(self, symbol_info: dict) -> float:
        """
        BitGet не всегда явно возвращает minQty, 
        но в contracts (mix_get_symbols_info) может быть поле minTradeNum или что-то вроде того.
        """
        # Пример: symbol_info.get("minTradeNum"), symbol_info.get("minTradeAmount") и т.п.
        return 0.0

    def futures_change_leverage(self, symbol: str, leverage: int) -> dict:
        """
        Меняет плечо. 
        Здесь нужно вызывать mix_adjust_leverage(symbol, marginCoin, leverage).
        """
        resp = self.client.mix_adjust_leverage(
            symbol=symbol,
            marginCoin=BITGET_MARGIN_COIN,
            leverage=leverage
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
        Простейшая формула: кол-во = (usdt_amount * leverage) / текущую_цену.
        """
        current_price = self.get_current_price(symbol)
        if current_price <= 0:
            raise ValueError("Current price is 0 or invalid")
        quantity = (usdt_amount * leverage) / current_price
        # Здесь можно добавить проверку minNotional и т.д.
        return quantity

    def round_more(self, number: float, digits: int) -> float:
        """
        Округляет число вверх (ceil) до digits знаков после запятой.
        """
        scale = 10 ** digits
        return math.ceil(number * scale) / scale

    def get_quantity_precision(self, symbol: str) -> int:
        """
        Вы можете посмотреть в символ-инфо (mix_get_symbols_info) поле stepSize.
        Здесь заглушка 3.
        """
        return 3

    def get_price_precision(self, symbol: str) -> int:
        """
        Аналогично get_quantity_precision, только для цены.
        """
        return 2

    def get_current_price(self, symbol: str) -> float:
        """
        Через mix_get_single_symbol_ticker(symbol) получаем текущую цену (last, close и т.п.)
        """
        resp = self.client.mix_get_single_symbol_ticker(symbol)
        # Пример: {"code":"00000","data":{"symbol":"BTCUSDT_UMCBL","last":"29100","high24h":...}, ...}
        try:
            return float(resp["data"]["last"])
        except:
            return 0.0

    def get_trading_mode(self) -> str:
        """
        На BitGet есть holdMode: cross или isolated, а также 'single_hold_mode' или 'double_hold_mode'.
        Для ONE_WAY / HEDGE можно ориентироваться на mix_get_accounts => "holdMode".
        """
        acc_data = self.client.mix_get_accounts(BITGET_PRODUCT_TYPE)
        if "data" in acc_data and len(acc_data["data"]) > 0:
            # Предположим, что holdMode = "double_hold_mode" => HEDGE, иначе ONE_WAY
            hold_mode = acc_data["data"][0].get("holdMode")
            if hold_mode == "double_hold_mode":
                return "HEDGE"
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
        Создаёт рыночный или лимитный ордер на BitGet (mix_place_order).
        side — здесь важно правильно маппить на BitGet:
         - BUY => open_long
         - SELL => open_short
         - (при закрытии - close_long / close_short)
        order_type => 'limit' или 'market'.
        """
        # Устанавливаем плечо
        self.futures_change_leverage(symbol, leverage)

        # Маппинг side (очень упрощённо, без учёта закрытия позиции)
        if side.upper() == "BUY":
            bitget_side = "open_long"
        else:
            bitget_side = "open_short"

        # Для закрытия позиций у вас должна быть своя логика, например:
        # if order_type == "CLOSE_LONG": bitget_side = "close_long" etc.

        # Если order_type = "LIMIT" => orderType='limit', price обязателен
        # Если order_type = "MARKET" => orderType='market'
        bitget_order_type = order_type.lower()  # "limit" или "market"

        str_price = str(price) if price else "0"

        resp = self.client.mix_place_order(
            symbol=symbol,
            marginCoin=BITGET_MARGIN_COIN,
            size=str(quantity),
            side=bitget_side,
            orderType=bitget_order_type,
            price=str_price,
            # Некоторые поля можно выставить по умолчанию:
            timeInForceValue="normal",
            reduceOnly=False,
            presetTakeProfitPrice="",  # Если нужно
            presetStopLossPrice=""     # Если нужно
        )
        return resp

    def create_stop_loss(self, symbol: str, side: str, stop_loss: t.Optional[float] = None, trading_mode: t.Optional[str] = None) -> None:
        """
        Пример: на BitGet можно вызывать mix_place_stop_order или mix_place_plan_order (TPSL).
        """
        if stop_loss is None:
            return
        # Простейший вызов (full close):
        # planType="loss_plan" для стоп-лосса, holdSide="long"/"short"
        # Если side=BUY => holdSide="long", side=SELL => holdSide="short"
        hold_side = "long" if side.upper() == "BUY" else "short"
        self.client.mix_place_stop_order(
            symbol=symbol,
            marginCoin=BITGET_MARGIN_COIN,
            planType="loss_plan",
            holdSide=hold_side,
            triggerPrice=str(stop_loss),
            triggerType="fill_price"   # или "market_price"
        )

    def bulk_create_take_profits(self, symbol: str, side: str, quantity: float, take_profit_targets: t.Optional[t.List[float]] = None, trading_mode: t.Optional[str] = None) -> None:
        """
        Тейк-профиты можно делать тоже через mix_place_stop_order (planType="profit_plan") или mix_place_plan_order.
        Если нужно несколько целей — BitGet позволяет делать несколько план-ордеров.
        """
        if not take_profit_targets:
            return
        hold_side = "long" if side.upper() == "BUY" else "short"
        for tp in take_profit_targets:
            self.client.mix_place_stop_order(
                symbol=symbol,
                marginCoin=BITGET_MARGIN_COIN,
                planType="profit_plan",
                holdSide=hold_side,
                triggerPrice=str(tp),
                triggerType="fill_price"
            )

    def close_stop_loss_orders(self, symbol: str, position_side: str) -> None:
        """
        Можно отменить все стопы (planType="loss_plan") через mix_cancel_plan_order.
        Но BitGet требует orderId. Значит, нужно сначала получить список текущих план-ордеров, отфильтровать.
        """
        current_plans = self.client.mix_get_plan_order_tpsl(symbol=symbol, isPlan="profit_loss")  # возможно, isPlan="profit_loss"
        # Далее отменяем все, где planType="loss_plan" и holdSide = position_side
        if "data" in current_plans and current_plans["data"]:
            for plan in current_plans["data"]:
                # тут проверяем planType == "loss_plan"?
                # для отмены надо plan["orderId"] и plan["planType"]
                if plan.get("planType") == "loss_plan":
                    oid = plan["orderId"]
                    self.client.mix_cancel_plan_order(
                        symbol=symbol,
                        marginCoin=BITGET_MARGIN_COIN,
                        orderId=oid,
                        planType="loss_plan"
                    )

    def close_take_profit_orders(self, symbol: str, position_side: str) -> None:
        """
        Аналогично close_stop_loss_orders, только planType="profit_plan".
        """
        current_plans = self.client.mix_get_plan_order_tpsl(symbol=symbol, isPlan="profit_loss")
        if "data" in current_plans and current_plans["data"]:
            for plan in current_plans["data"]:
                if plan.get("planType") == "profit_plan":
                    oid = plan["orderId"]
                    self.client.mix_cancel_plan_order(
                        symbol=symbol,
                        marginCoin=BITGET_MARGIN_COIN,
                        orderId=oid,
                        planType="profit_plan"
                    )

    def get_min_notional(self, symbol: str) -> float:
        """
        На BitGet нет точного поля 'minNotional' в простом виде. 
        Можно смотреть minTradeNum из /contracts. 
        Возвращаем заглушку.
        """
        return 5.0

    def close_order(self, symbol: str, order_id: int) -> dict:
        """
        Отменяет ордер по его ID.
        """
        resp = self.client.mix_cancel_order(symbol, BITGET_MARGIN_COIN, orderId=str(order_id))
        return resp if resp else {}

    def get_futures_balance(self) -> float:
        """
        Возвращает баланс (доступные средства) по marginCoin=USDT для umcbl.
        Посмотрим mix_get_accounts => ищем coin="USDT".
        """
        acc = self.client.mix_get_accounts(BITGET_PRODUCT_TYPE)
        # Пример: acc["data"] = [ { "marginCoin":"USDT", "available":"1234.56", ...}, ... ]
        if "data" in acc:
            for item in acc["data"]:
                if item.get("marginCoin") == BITGET_MARGIN_COIN:
                    # Возьмём поле "available"
                    return float(item.get("available", 0.0))
        return 0.0

    def futures_create_order(self, **kwargs) -> dict:
        """
        В BitGet уже есть метод mix_place_order. Можно вызвать напрямую. 
        Можно повторить логику из create_order. 
        """
        # В kwargs ожидаем такие поля: symbol, quantity, side, price и т.д.
        # Для упрощения — вызываем create_order (оно уже делает mix_place_order).
        symbol = kwargs.get("symbol")
        side = kwargs.get("side", "BUY")
        order_type = kwargs.get("type", "MARKET").lower()
        quantity = kwargs.get("quantity", 0.0)
        price = kwargs.get("price")
        resp = self.create_order(symbol, side, order_type, quantity, price=price)
        return resp if resp else {}

    def adjust_take_profits(self) -> None:
        """
        Примерно повторяет логику "автокоррекции" TP, как в вашем Binance-классе.
        Здесь оставляем заглушку или пишем собственный код, если нужно.
        """
        # Заглушка:
        pass

    def get_free_margin(self) -> float:
        """
        Аналогично get_futures_balance, но иногда нужно разницу между total и used.
        Здесь возвращаем просто available (как "free margin").
        """
        return self.get_futures_balance()
