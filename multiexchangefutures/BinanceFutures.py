import math
import typing as t
from logging import Logger
from .basefutures import BaseFuturesTrade
from binance import Client

class BinanceFuturesTrade(BaseFuturesTrade):
    """
    Класс для торговли фьючерсами на Binance, наследуется от BaseFuturesTrade.
    но сохраняет интерфейс, определённый в BaseFuturesTrade.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        logger: t.Optional[Logger] = None,
        requests_params: t.Optional[t.Dict[str, t.Any]] = None,
        testnet: bool = False,
    ):
        """
        Создаём экземпляр BinanceFuturesTrade.

        :param api_key: Ваш API ключ.
        :param secret_key: Ваш Secret ключ.
        :param logger: Опциональный logger для логирования.
        :param requests_params: Параметры для requests.Session (прокси, тайм-ауты, etc.).
        :param testnet: Если True - будет использоваться тестовая среда Binance Futures.
        """
        super().__init__()
        self.logger = logger
        self.api_key = api_key
        self.secret_key = secret_key
        self.testnet = testnet
        self.client = Client(
            api_key=self.api_key,
            api_secret=self.secret_key,
            requests_params=requests_params,
            testnet=self.testnet,
            # При необходимости указывайте другие аргументы (tld, ping=False, etc.)
        )

    @classmethod
    def create(
        cls,
        api_key: str,
        secret_key: str,
        logger: t.Optional[Logger] = None,
        requests_params: t.Optional[t.Dict[str, t.Any]] = None,
        testnet: bool = False,
    ):
        """
        Фабричный метод, создающий экземпляр BinanceFuturesTrade.

        :param api_key: Ваш API ключ.
        :param secret_key: Ваш Secret ключ.
        :param logger: Опциональный logger для логирования.
        :param requests_params: Параметры для requests.Session (прокси, тайм-ауты, etc.).
        :param testnet: Если True - будет использоваться тестовая среда Binance Futures.
        :return: Экземпляр BinanceFuturesTrade.
        """
        return cls(api_key, secret_key, logger=logger, requests_params=requests_params, testnet=testnet)

    def close(self):
        """
        Закрывает соединение (сессию) с сервером Binance, если нужно.
        """
        if self.client:
            self.client.close_connection()

    def get_account_info(self) -> dict:
        """
        Получает информацию об аккаунте ( SPOT / Margin, не путать с futures_account ).
        Для USDS-M Futures обычно нужен futures_account вместо этого. 
        Но раз в BaseFuturesTrade есть такой метод – реализуем.

        :return: dict с информацией об аккаунте.
        """
        return self.client.get_account()

    def get_futures_account_info(self) -> dict:
        """
        Получает информацию о фьючерсном аккаунте: балансы, маржу, позиции и т.д.

        :return: dict с информацией о фьючерсном аккаунте.
        """
        return self.client.futures_account()

    def get_max_leverage_for_symbol(self, symbol: str) -> int:
        """
        Возвращает максимально возможное плечо для указанного символа фьючерсов.

        :param symbol: Название торговой пары (например, 'BTCUSDT').
        :return: Максимальное плечо (int).
        """
        brackets = self.client.futures_leverage_bracket()
        max_leverage = -1
        for bracket_obj in brackets:
            if bracket_obj.get('symbol') == symbol:
                # Ищем максимальное плечо среди 'brackets'
                bracket_list = bracket_obj.get('brackets', [])
                possible = max(b['initialLeverage'] for b in bracket_list)
                max_leverage = max(max_leverage, possible)
        if max_leverage < 1:
            raise ValueError(f'Не найдено информации о плече для {symbol}')
        return max_leverage

    def get_trading_symbols(self) -> t.List[dict]:
        """
        Возвращает список доступных фьючерсных символов/инструментов.

        :return: список dict, описывающих символы.
        """
        info = self.client.futures_exchange_info()
        return info.get('symbols', [])

    def get_open_futures_positions(self) -> t.List[dict]:
        """
        Возвращает список текущих открытых позиций на фьючерсном аккаунте.

        :return: список dict (каждый dict = одна позиция).
        """
        positions = self.client.futures_position_information()
        # Отфильтруем только те, где positionAmt != 0
        return [p for p in positions if float(p.get('positionAmt', '0')) != 0.0]

    def get_all_orders(self) -> t.List[dict]:
        """
        Возвращает список всех ордеров (активных и исполненных) на фьючерсном аккаунте.

        :return: список dict.
        """
        return self.client.futures_get_all_orders()

    def get_open_orders(self) -> t.List[dict]:
        """
        Возвращает список активных (неисполненных/неотменённых) ордеров на фьючерсном аккаунте.

        :return: список dict.
        """
        return self.client.futures_get_open_orders()

    def get_min_quantity(self, symbol_info: dict) -> float:
        """
        Возвращает минимальное кол-во (minQty) для указанного symbol_info.

        :param symbol_info: Словарь из get_trading_symbols(), описывающий символ.
        :return: float, минимальное кол-во.
        """
        for flt in symbol_info.get('filters', []):
            if flt.get('filterType') == 'LOT_SIZE':
                return float(flt['minQty'])
        return 0.0

    def futures_change_leverage(self, symbol: str, leverage: int) -> dict:
        """
        Меняет плечо на фьючерсном аккаунте для symbol.

        :param symbol: Торговая пара.
        :param leverage: Новое значение плеча.
        :return: dict с деталями изменения плеча.
        """
        return self.client.futures_change_leverage(symbol=symbol, leverage=leverage)

    def calculate_quantity_from_usdt(
        self,
        symbol: str,
        usdt_amount: float,
        leverage: int,
        adjust_to_min_notional: bool = True,
        take_profit_targets: t.Optional[t.List[float]] = None,
    ) -> float:
        """
        Примерная реализация калькуляции кол-ва на основе usdt_amount * leverage / current_price.
        Параметр adjust_to_min_notional определяет, нужно ли автоматически дотягивать
        до минимального номинала.

        :param symbol: Символ (BTCUSDT, ETHUSDT, и т.п.).
        :param usdt_amount: Сколько USDT хотим закинуть (без учёта плеча).
        :param leverage: Плечо.
        :param adjust_to_min_notional: нужно ли дотянуть до минимального номинала.
        :param take_profit_targets: список целей (могут влиять на min_notional).
        :return: float, итоговое кол-во.
        """
        # current price
        current_price_obj = self.client.futures_symbol_ticker(symbol=symbol)
        current_price = float(current_price_obj['price'])

        # Пример логики: (usdt_amount * leverage) / current_price
        notional = usdt_amount * leverage
        quantity = notional / current_price

        # При необходимости подтягиваем до min_notional
        # Для упрощения берём фильтр MIN_NOTIONAL
        # И round_more() если нужно.

        # 1) узнаём minNotional из get_trading_symbols()
        symbols_info = self.get_trading_symbols()
        symbol_item = next((s for s in symbols_info if s.get('symbol') == symbol), None)
        if not symbol_item:
            raise ValueError(f"Symbol {symbol} не найден в get_trading_symbols()")

        # minNotional
        min_notional = 0.0
        for f in symbol_item.get('filters', []):
            if f.get('filterType') == 'MIN_NOTIONAL':
                min_notional = float(f['notional'])

        # NOTE: В фьючерсах 'min_notional' может отличаться (но условно используем).
        # Немного поправим if take_profit_targets, как в вашем коде:
        if take_profit_targets and len(take_profit_targets) > 0:
            # Пример: если у нас 3 цели, иногда увеличивают min_notional * 3
            min_notional *= len(take_profit_targets)

        # Проверяем
        actual_notional = quantity * current_price
        if actual_notional < min_notional:
            if adjust_to_min_notional:
                quantity = min_notional / current_price
            else:
                # выбросим Exception
                raise ValueError("Calculated quantity is below the minimum notional value")

        # И округлим вверх, используя round_more()
        qty_precision = self.get_quantity_precision(symbol)
        quantity = self.round_more(quantity, qty_precision)

        return quantity

    def round_more(self, number: float, digits: int) -> float:
        """
        Округляет число вверх (ceil) до заданного кол-ва знаков после запятой.
        """
        if not isinstance(number, float):
            number = float(number)
        scale = 10 ** digits
        return math.ceil(number * scale) / scale

    def get_quantity_precision(self, symbol: str) -> int:
        """
        Возвращает точность (LOT_SIZE) для количества.

        :param symbol: e.g. 'BTCUSDT'.
        :return: int (кол-во знаков после запятой).
        """
        symbols = self.get_trading_symbols()
        s = next((x for x in symbols if x.get('symbol') == symbol), None)
        if not s:
            raise ValueError(f"Не найден symbol {symbol} в биржевой информации")

        for flt in s.get('filters', []):
            if flt.get('filterType') == 'LOT_SIZE':
                stepSize = flt.get('stepSize', '1')
                # Кол-во знаков = длина того, что после десятичной, кроме нулей
                return max(len(stepSize.rstrip('0')) - 2, 0)
        return 0

    def get_price_precision(self, symbol: str) -> int:
        """
        Возвращает точность цены (PRICE_FILTER).

        :param symbol: e.g. 'BTCUSDT'.
        :return: int (кол-во знаков после запятой).
        """
        symbols = self.get_trading_symbols()
        s = next((x for x in symbols if x.get('symbol') == symbol), None)
        if not s:
            raise ValueError(f"Не найден symbol {symbol} в биржевой информации")

        for flt in s.get('filters', []):
            if flt.get('filterType') == 'PRICE_FILTER':
                tick = flt.get('tickSize', '1')
                return max(len(tick.rstrip('0')) - 2, 0)
        return 0

    def get_current_price(self, symbol: str) -> float:
        """
        Возвращает текущую цену (futures_symbol_ticker).
        """
        data = self.client.futures_symbol_ticker(symbol=symbol)
        return float(data['price'])

    def get_trading_mode(self) -> str:
        """
        Возвращает 'ONE_WAY' или 'HEDGE' на основе инфы об аккаунте (futures_account).
        Упрощённая логика: если есть позиции LONG/SHORT, считаем Hedge.

        :return: str.
        """
        futures_info = self.client.futures_account()
        positions = futures_info.get('positions', [])
        # Если найдём 'positionSide' == LONG или SHORT – Hedge
        for p in positions:
            if p.get('positionSide') in ['LONG', 'SHORT']:
                return 'HEDGE'
        return 'ONE_WAY'

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
        Создание ордера (MARKET / LIMIT) с потенциальным стоп-лоссом и ТП.

        :param symbol: Торговая пара.
        :param side: BUY / SELL.
        :param order_type: LIMIT / MARKET.
        :param quantity: Кол-во.
        :param price: Цена (для LIMIT).
        :param stop_loss: SL, если нужен.
        :param take_profit_targets: список целей ТП.
        :param leverage: Плечо.
        :return: dict с инфой об ордере.
        """
        # Для единообразия с вашим кодом:
        # Меняем плечо
        self.futures_change_leverage(symbol, leverage)

        # Если аккаунт в hedge – position_side = LONG/SHORT, иначе BOTH
        position_side = 'BOTH'
        if self.get_trading_mode() == 'HEDGE':
            position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'

        order_params = dict(
            symbol=symbol,
            side=side.upper(),
            type=order_type.upper(),
            quantity=quantity,
            positionSide=position_side,
        )
        if order_type.upper() == 'LIMIT' and price is not None:
            order_params['price'] = str(price)
            order_params['timeInForce'] = 'GTC'

        # Отправляем ордер
        new_order = self.client.futures_create_order(**order_params)

        # При необходимости создаём SL и TP
        if stop_loss:
            self.create_stop_loss(symbol, side, stop_loss, trading_mode=None)

        if take_profit_targets:
            self.bulk_create_take_profits(symbol, side, quantity, take_profit_targets, trading_mode=None)

        return new_order

    def create_stop_loss(
        self,
        symbol: str,
        side: str,
        stop_loss: t.Optional[float] = None,
        trading_mode: t.Optional[str] = None
    ) -> None:
        """
        Создаём стоп-лосс (STOP_MARKET).
        """
        if stop_loss is None:
            return  # нечего создавать
        if not trading_mode:
            trading_mode = self.get_trading_mode()
        position_side = 'BOTH'
        if trading_mode == 'HEDGE':
            position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'

        # Закроем старые SL:
        self.close_stop_loss_orders(symbol, position_side)

        params = dict(
            symbol=symbol,
            side=('SELL' if side.upper() == 'BUY' else 'BUY'),
            type='STOP_MARKET',
            stopPrice=stop_loss,
            closePosition=True,
            positionSide=position_side
        )
        self.client.futures_create_order(**params)

    def bulk_create_take_profits(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_targets: t.Optional[t.List[float]] = None,
        trading_mode: t.Optional[str] = None
    ) -> None:
        """
        Создаёт несколько TP (TAKE_PROFIT_MARKET).
        """
        if not take_profit_targets:
            return
        if trading_mode is None:
            trading_mode = self.get_trading_mode()
        position_side = 'BOTH'
        if trading_mode == 'HEDGE':
            position_side = 'LONG' if side.upper() == 'BUY' else 'SHORT'

        # Удалим старые TP
        self.close_take_profit_orders(symbol, position_side)

        # Допустим делим количество поровну
        chunk = quantity / len(take_profit_targets)
        qty_prec = self.get_quantity_precision(symbol)
        from math import ceil
        chunk = self.round_more(chunk, qty_prec)

        # В зависимости от side сортируем TPs
        sorted_targets = sorted(take_profit_targets, reverse=(side.upper() == 'SELL'))
        for i, tp in enumerate(sorted_targets):
            # если последний – на всё оставшееся
            if i == len(sorted_targets) - 1:
                use_qty = None  # признак closePosition
            else:
                use_qty = chunk

            if use_qty is None:
                # создаём TakeProfit в режиме closePosition
                self.client.futures_create_order(
                    symbol=symbol,
                    side=('SELL' if side.upper() == 'BUY' else 'BUY'),
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=tp,
                    positionSide=position_side,
                    closePosition=True
                )
            else:
                self.client.futures_create_order(
                    symbol=symbol,
                    side=('SELL' if side.upper() == 'BUY' else 'BUY'),
                    type='TAKE_PROFIT_MARKET',
                    stopPrice=tp,
                    quantity=use_qty,
                    positionSide=position_side
                )

    def close_stop_loss_orders(self, symbol: str, position_side: str) -> None:
        """
        Закрывает все STOP_MARKET ордера (стоп-лоссы) для указанного символа и position_side.
        """
        open_orders = self.get_open_orders()
        for ord_obj in open_orders:
            if (ord_obj.get('symbol') == symbol and
                ord_obj.get('type') == 'STOP_MARKET' and
                ord_obj.get('positionSide') == position_side):
                oid = ord_obj.get('orderId')
                self.close_order(symbol, oid)

    def close_take_profit_orders(self, symbol: str, position_side: str) -> None:
        """
        Закрывает все TAKE_PROFIT_MARKET ордера (тейк-профиты) для указанного symbol & position_side.
        """
        open_orders = self.get_open_orders()
        for ord_obj in open_orders:
            if (ord_obj.get('symbol') == symbol and
                ord_obj.get('type') == 'TAKE_PROFIT_MARKET' and
                ord_obj.get('positionSide') == position_side):
                oid = ord_obj.get('orderId')
                self.close_order(symbol, oid)

    def get_min_notional(self, symbol: str) -> float:
        """
        Возвращает минимальный номинал (MIN_NOTIONAL) для символа.
        """
        syms = self.get_trading_symbols()
        s = next((x for x in syms if x.get('symbol') == symbol), None)
        if not s:
            raise ValueError(f"Symbol {symbol} не найден.")
        for f in s.get('filters', []):
            if f.get('filterType') == 'MIN_NOTIONAL':
                return float(f.get('notional', 0))
        return 0.0

    def close_order(self, symbol: str, order_id: int) -> dict:
        """
        Отменяет (закрывает) указанный ордер (по order_id).
        """
        return self.client.futures_cancel_order(symbol=symbol, orderId=order_id)

    def get_futures_balance(self) -> float:
        """
        Возвращает доступный баланс USDT на фьючерсном аккаунте.

        :return: float (баланс USDT).
        """
        balances = self.client.futures_account_balance()
        for item in balances:
            if item['asset'] == 'USDT':
                return float(item['balance'])
        raise RuntimeError("USDT не найден в futures_account_balance")

    def futures_create_order(self, **kwargs) -> dict:
        """
        Низкоуровневый метод для создания ордера (фактически проксирует client.futures_create_order).
        """
        return self.client.futures_create_order(**kwargs)

    def adjust_take_profits(self) -> None:
        """
        Логика по переустановке/корректировке TP.
        К примеру, реализуем упрощённо: пока не делаем ничего.
        """
        # Здесь любая желаемая логика.
        pass

    def get_free_margin(self) -> float:
        """
        Возвращает доступную маржу для торговли (в USDT) на фьючерсном аккаунте.
        """
        # Самый простой путь – посмотреть в self.client.futures_account_balance() => availableBalance
        balances = self.client.futures_account_balance()
        for item in balances:
            if item['asset'] == 'USDT':
                # availableBalance или что-то подобное
                return float(item.get('withdrawAvailable', item.get('availableBalance', 0)))
        return 0.0
