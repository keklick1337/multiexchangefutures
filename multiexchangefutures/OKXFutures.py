import typing as t
from logging import Logger

from .base_futures_trade import BaseFuturesTrade

from okx.Account import AccountAPI
from okx.Trade import TradeAPI
from okx.PublicData import PublicAPI
from okx.MarketData import MarketAPI
from okx.exceptions import OkxAPIException

class OkxFuturesTrade(BaseFuturesTrade):
    """
    Пример синхронного класса, реализующего методы BaseFuturesTrade для OKX-фьючерсов.
    """

    def __init__(self, 
                 api_key: str,
                 secret_key: str,
                 passphrase: str,
                 logger: t.Optional[Logger] = None,
                 use_server_time: bool = False,
                 flag: str = '1',
                 domain: str = 'https://www.okx.com',
                 debug: bool = False,
                 proxy: t.Optional[str] = None
                ):
        """
        В конструкторе инициализируем нужные клиенты из библиотеки okx.
        """
        super().__init__()
        self.logger = logger
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.use_server_time = use_server_time
        self.flag = flag
        self.domain = domain
        self.debug = debug
        self.proxy = proxy

        # Создаем нужные API-клиенты
        self.account_api = AccountAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            use_server_time=self.use_server_time,
            flag=self.flag,
            domain=self.domain,
            debug=self.debug,
            proxy=self.proxy
        )
        self.trade_api = TradeAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            use_server_time=self.use_server_time,
            flag=self.flag,
            domain=self.domain,
            debug=self.debug,
            proxy=self.proxy
        )
        self.public_api = PublicAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            use_server_time=self.use_server_time,
            flag=self.flag,
            domain=self.domain,
            debug=self.debug,
            proxy=self.proxy
        )
        self.market_api = MarketAPI(
            api_key=self.api_key,
            api_secret_key=self.secret_key,
            passphrase=self.passphrase,
            use_server_time=self.use_server_time,
            flag=self.flag,
            domain=self.domain,
            debug=self.debug,
            proxy=self.proxy
        )

    @classmethod
    def create(cls, 
               api_key: str,
               secret_key: str,
               passphrase: str,
               logger: t.Optional[Logger] = None,
               use_server_time: bool = False,
               flag: str = '1',
               domain: str = 'https://www.okx.com',
               debug: bool = False,
               proxy: t.Optional[str] = None
              ) -> "OkxFuturesTrade":
        """
        Фабричный метод для создания экземпляра.
        """
        return cls(
            api_key=api_key,
            secret_key=secret_key,
            passphrase=passphrase,
            logger=logger,
            use_server_time=use_server_time,
            flag=flag,
            domain=domain,
            debug=debug,
            proxy=proxy
        )

    def close(self):
        """
        Закрываем все HTTP-соединения, если нужно.
        """
        try:
            # Отключение клиентов, если нужно.
            self.account_api.close()
            self.trade_api.close()
            self.public_api.close()
            self.market_api.close()
        except Exception as e:
            if self.logger:
                self.logger.exception(f"[OKX] Error on close: {e}")

    # =========================================================================
    # Ниже — реализация методов базового класса BaseFuturesTrade
    # =========================================================================

    def get_account_info(self) -> dict:
        """
        Получает информацию об аккаунте (спот + фьючерсы).
        На OKX нет отдельного "аккаунт-фьючерс" эндпоинта, 
        поэтому возвращаем общий баланс из /api/v5/account/balance.
        """
        try:
            resp = self.account_api.get_account_balance()
            return resp
        except OkxAPIException as ex:
            raise ex

    def get_futures_account_info(self) -> dict:
        """
        На OKX нет отдельного метода для “futures account info”.
        Можно, к примеру, вернуть список позиций и баланс счета в cross/isolated.
        """
        try:
            # Возьмём общий risk + позиции:
            positions_info = self.account_api.get_position_risk(instType='SWAP')  
            # Если нужно, можете комбинировать ещё и balances
            return positions_info
        except OkxAPIException as ex:
            raise ex

    def get_max_leverage_for_symbol(self, symbol: str) -> int:
        """
        На OKX жестко “максимальное плечо” не возвращается одним запросом, 
        но можно использовать /api/v5/account/leverage-info (GET_LEVERAGE).
        """
        try:
            # symbol -> instId, допустим "BTC-USDT-SWAP" для perpetual
            resp = self.account_api.get_leverage(mgnMode='cross', instId=symbol)
            # resp - список, берем максимальный lever, если вдруг несколько
            # Пример ответа: [{"instId":"BTC-USDT-SWAP","lever":"75","mgnMode":"cross"}]
            if resp and 'data' in resp and len(resp['data']) > 0:
                lever = resp['data'][0].get('lever', '1')
                return int(float(lever))
            return 1
        except OkxAPIException as ex:
            raise ex

    def get_trading_symbols(self) -> t.List[dict]:
        """
        Возвращает список фьючерсных инструментов (SWAP + FUTURES).
        """
        try:
            # Пример: хотим взять /api/v5/public/instruments?instType=SWAP
            # Можно также FUTURES
            swaps = self.public_api.get_instruments(instType='SWAP')
            futures = self.public_api.get_instruments(instType='FUTURES')
            data_swaps = swaps.get('data', [])
            data_futures = futures.get('data', [])
            return data_swaps + data_futures
        except OkxAPIException as ex:
            raise ex

    def get_open_futures_positions(self) -> t.List[dict]:
        """
        Возвращает открытые позиции. 
        На OKX: /api/v5/account/positions?instType=SWAP
        """
        try:
            resp = self.account_api.get_positions(instType='SWAP')
            data = resp.get('data', [])
            return data
        except OkxAPIException as ex:
            raise ex

    def get_all_orders(self) -> t.List[dict]:
        """
        Список всех ордеров (в т.ч. завершённых) обычно берут через history + archive. 
        Здесь, для примера, возьмём последние 7 дней:
        """
        try:
            # instType='SWAP' - фьючерсы/perpetual
            resp = self.trade_api.get_orders_history(instType='SWAP')
            return resp.get('data', [])
        except OkxAPIException as ex:
            raise ex

    def get_open_orders(self) -> t.List[dict]:
        """
        Открытые (активные) ордера: /api/v5/trade/orders-pending
        """
        try:
            resp = self.trade_api.get_order_list(instType='SWAP')
            return resp.get('data', [])
        except OkxAPIException as ex:
            raise ex

    def get_min_quantity(self, symbol_info: dict) -> float:
        """
        На OKX нет прямого LOT_SIZE, как на Binance. 
        Однако можно посмотреть на minSz, stepSz в /public/instruments
        символ - это элемент из get_trading_symbols().
        """
        # Допустим, из symbol_info['minSz']:
        return float(symbol_info.get("minSz", 0.0))

    def futures_change_leverage(self, symbol: str, leverage: int) -> dict:
        """
        Меняем плечо через /api/v5/account/set-leverage
        """
        try:
            resp = self.account_api.set_leverage(
                lever=str(leverage),
                mgnMode='cross',   # или isolated
                instId=symbol
            )
            return resp
        except OkxAPIException as ex:
            raise ex

    def calculate_quantity_from_usdt(
        self, 
        symbol: str, 
        usdt_amount: float, 
        leverage: int, 
        adjust_to_min_notional: bool = True,
        take_profit_targets: t.Optional[t.List[float]] = None
    ) -> float:
        """
        Примерный расчёт кол-ва. 
        Возьмём текущую цену * usdt_amount * leverage -> quantity.
        """
        price = self.get_current_price(symbol)
        if price <= 0:
            raise ValueError(f"Bad price for {symbol}")
        
        # Примерная формула: (usdt_amount * leverage) / price
        raw_qty = (usdt_amount * leverage) / price
        # Проверим минимально допустимый lotSize:
        min_sz = 0.0
        # Попробуем найти инструменты
        inst_info = self.public_api.get_instruments(instType='SWAP', instId=symbol)
        if inst_info and 'data' in inst_info and len(inst_info['data']) > 0:
            min_sz = float(inst_info['data'][0].get('minSz', '0.0'))

        if raw_qty < min_sz and adjust_to_min_notional:
            raw_qty = min_sz
        
        return raw_qty

    def round_more(self, number: float, digits: int) -> float:
        """
        Просто ceil с нужным количеством знаков после запятой.
        """
        import math
        if digits <= 0:
            return math.ceil(number)
        scale = 10 ** digits
        return math.ceil(number * scale) / scale

    def get_quantity_precision(self, symbol: str) -> int:
        """
        На OKX в /public/instruments для каждого символа есть параметр stepSz (минимальный шаг).
        Можно на основе него вычислить precision.
        """
        try:
            info = self.public_api.get_instruments(instType='SWAP', instId=symbol)
            if info and 'data' in info and len(info['data']) > 0:
                stepSz_str = info['data'][0].get('stepSz', '0.0001')
                # допустим, если stepSz=0.001 -> precision=3
                return self._calc_precision(stepSz_str)
            return 0
        except OkxAPIException as ex:
            raise ex

    def get_price_precision(self, symbol: str) -> int:
        """
        Аналогично, на OKX есть tickSz для цены.
        """
        try:
            info = self.public_api.get_instruments(instType='SWAP', instId=symbol)
            if info and 'data' in info and len(info['data']) > 0:
                tickSz_str = info['data'][0].get('tickSz', '0.0001')
                return self._calc_precision(tickSz_str)
            return 0
        except OkxAPIException as ex:
            raise ex

    def _calc_precision(self, step_str: str) -> int:
        """
        Вспомогательная функция, которая считает кол-во знаков после запятой, 
        исходя из строки типа '0.001'.
        """
        if '.' not in step_str:
            return 0
        splitted = step_str.split('.')
        return len(splitted[1].rstrip('0'))

    def get_current_price(self, symbol: str) -> float:
        """
        Текущая рыночная цена: /api/v5/market/ticker?instId=...
        """
        try:
            resp = self.market_api.get_ticker(symbol)
            if resp and 'data' in resp and len(resp['data']) > 0:
                return float(resp['data'][0].get('last', '0'))
            return 0.0
        except OkxAPIException as ex:
            raise ex

    def get_trading_mode(self) -> str:
        """
        На OKX режим 'ONE_WAY' или 'HEDGE' называется posMode="long_short_mode"/"net_mode".
        """
        try:
            conf = self.account_api.get_account_config()
            # Например, resp['data'][0]['posMode']: "net_mode" или "long_short_mode"
            if not conf or 'data' not in conf or len(conf['data']) == 0:
                return 'ONE_WAY'
            pmode = conf['data'][0].get('posMode')
            if pmode == 'long_short_mode':
                return 'HEDGE'
            return 'ONE_WAY'
        except OkxAPIException:
            # По умолчанию
            return 'ONE_WAY'

    def create_order(self, 
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
        Пример создания ордера на OKX:
        - trade_api.place_order
        Параметр side: 'BUY' / 'SELL' -> в OKX side='buy' или 'sell'
        Параметр order_type: 'MARKET' / 'LIMIT' -> в OKX ordType='market' / 'limit'
        """
        # Установка плеча:
        self.futures_change_leverage(symbol, leverage)

        # Определяем tdMode (cross/isolated). Для простоты пусть cross:
        tdMode = 'cross'
        # Позиционный режим:
        position_side = self.get_trading_mode()
        posSide = 'long' if side.upper() == 'BUY' else 'short'
        if position_side == 'ONE_WAY':
            posSide = ''  # OKX требует posSide='', если net_mode

        # Формируем параметры
        okx_side = side.lower()
        okx_ord_type = order_type.lower()  # 'limit' или 'market'

        params = {
            "instId": symbol,
            "tdMode": tdMode,
            "side": okx_side,
            "ordType": okx_ord_type,
            "sz": str(quantity),   # строка
            "posSide": posSide,    # '' или 'long'/'short'
        }
        if okx_ord_type == 'limit' and price is not None:
            params["px"] = str(price)

        try:
            result = self.trade_api.place_order(**params)
            # Если нужно, создаём стоп-лосс/тейк-профит - 
            # на OKX они делаются через algo-ордер или tp/sl.
            # Для простоты — опустим (или сделайте сами).
            return result
        except OkxAPIException as ex:
            raise ex

    def create_stop_loss(self, 
                         symbol: str, 
                         side: str, 
                         stop_loss: t.Optional[float] = None, 
                         trading_mode: t.Optional[str] = None
                        ) -> None:
        """
        На OKX стоп-лосс обычно делается через "attachAlgoOrds" при place_order,
        либо отдельным вызовом /api/v5/trade/order-algo с ordType='stop'.
        Для упрощения ничего не делаем или делаем заготовку.
        """
        if stop_loss is None:
            return
        # Заглушка:
        pass

    def bulk_create_take_profits(self, 
                                 symbol: str, 
                                 side: str, 
                                 quantity: float, 
                                 take_profit_targets: t.Optional[t.List[float]] = None, 
                                 trading_mode: t.Optional[str] = None
                                ) -> None:
        """
        Аналогично create_stop_loss — на OKX это algo-ордера. 
        Здесь оставим заглушку.
        """
        if not take_profit_targets:
            return
        # Заглушка:
        pass

    def close_stop_loss_orders(self, symbol: str, position_side: str) -> None:
        """
        Закрывает все стоп-лоссы. 
        На OKX нужно отменять algo-ордера через cancel_algo_order().
        Здесь — заглушка.
        """
        pass

    def close_take_profit_orders(self, symbol: str, position_side: str) -> None:
        """
        Закрывает все ТП-ордера. 
        """
        pass

    def get_min_notional(self, symbol: str) -> float:
        """
        На OKX нет MIN_NOTIONAL как на Binance, 
        можно пытаться оценивать minSz * price. Возвращаем 0.
        """
        return 0.0

    def close_order(self, symbol: str, order_id: int) -> dict:
        """
        Отмена ордера. 
        На OKX: trade_api.cancel_order(instId, ordId=..., ...)
        """
        try:
            resp = self.trade_api.cancel_order(
                instId=symbol, 
                ordId=str(order_id)
            )
            return resp
        except OkxAPIException as ex:
            raise ex

    def get_futures_balance(self) -> float:
        """
        Возвращаем кол-во USDT (либо доступный кросс-марджин) 
        Для примера: ищем "USDT" в account balance
        """
        try:
            resp = self.account_api.get_account_balance(ccy='USDT')
            data_list = resp.get('data', [])
            if len(data_list) > 0:
                details = data_list[0].get('details', [])
                for item in details:
                    if item.get('ccy') == 'USDT':
                        return float(item.get('cashBal', 0.0))
            return 0.0
        except OkxAPIException as ex:
            raise ex

    def futures_create_order(self, **kwargs) -> dict:
        """
        Вспомогательный метод для непосредственного создания ордера. 
        Можно переиспользовать create_order, но оставим пример:
        """
        return self.create_order(
            symbol=kwargs.get('symbol'),
            side=kwargs.get('side'),
            order_type=kwargs.get('type'),
            quantity=float(kwargs.get('quantity', 0)),
            price=kwargs.get('price'),
            stop_loss=kwargs.get('stop_loss'),
            take_profit_targets=kwargs.get('take_profit_targets', None),
            leverage=int(kwargs.get('leverage', 1))
        ) or {}

    def adjust_take_profits(self) -> None:
        """
        Пример вспомогательной логики.
        В OKX нет метода “автоматом отредактировать все TPs”, 
        нужно вручную читать открытые ордера + позиции и редактировать.
        """
        pass

    def get_free_margin(self) -> float:
        """
        Возвращаем доступную маржу (free) в USDT. На OKX можно смотреть cashBal - 
        или смотреть через API get_account_balance.
        """
        return self.get_futures_balance()
