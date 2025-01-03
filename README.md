# MultiExchangeFutures – Универсальная библиотека для торговли фьючерсами на разных биржах (by Vladislav Tislenko aka keklick1337)

**MultiExchangeFutures** – это набор Python-классов, который предоставляет единый интерфейс для торговли фьючерсными инструментами на различных криптобиржах.  
В основу библиотеки положен абстрактный класс [BaseFuturesTrade](./multiexchangefutures/base_futures_trade.py), в котором определён общий интерфейс (методы) для фьючерсной торговли. Для каждой биржи (Binance, Bybit, BitGet, OKX и т.д.) создаются **реальные** классы, наследующиеся от базового, и реализующие необходимые методы под специфику конкретной биржи.

## Содержание
1. [Основные возможности](#Основные-возможности)
2. [Структура проекта](#Структура-проекта)
3. [Установка](#Установка)
4. [Использование](#Использование)
5. [Примеры кода](#Примеры-кода)
   - [Binance](#Пример-использования-с-binancefuturestrade)
   - [BitGet](#Пример-использования-с-bitgetfuturestrade)
   - [Bybit](#Пример-использования-с-bybitfuturestrade)
   - [OKX](#Пример-использования-с-okxfuturestrade)
6. [Расширение и добавление новых бирж](#Расширение-и-добавление-новых-бирж)
7. [Лицензия](#Лицензия)
8. [Отказ от ответственности](#Отказ-от-ответственности)

---

## Основные возможности
- Унифицированный **базовый класс** с методами для:
  - Получения балансов и позиций,
  - Создания, отмены и управления ордерами,
  - Управления плечом (leverage),
  - Расчёта количества контрактов, округления и т.д.
- **Конкретные реализации** для популярных бирж (Binance, Bybit, BitGet, OKX) – каждая из них наследует общий интерфейс `BaseFuturesTrade`.
- Простое переключение между биржами, не меняя бизнес-логику работы с классом.
- Поддержка фьючерсных инструментов (USDT-маржинальные фьючерсы, perpetual swaps и т.п.).

## Структура проекта

```
.
└── multiexchangefutures
    ├── __init__.py               # Инициализационный файл модуля
    ├── base_futures_trade.py     # Базовый (абстрактный) класс BaseFuturesTrade
    ├── BinanceFutures.py         # Реализация торговли на Binance Futures
    ├── BitGetFutures.py          # Реализация торговли на BitGet Futures
    ├── ByBitFutures.py           # Реализация торговли на Bybit Futures
    ├── OKXFutures.py             # Реализация торговли на OKX (Swap/Futures)
    └── ... (другие файлы, зависимости, тесты и т.д.)
```

- **`base_futures_trade.py`**  
  Содержит абстрактный класс `BaseFuturesTrade` с методами, которые нужно переопределять в реальных классах. Все методы помечены как `NotImplementedError`.  

- **`BinanceFutures.py`**  
  Класс `BinanceFuturesTrade`, унаследованный от `BaseFuturesTrade`, и реализующий логику работы с Binance Futures через официальный `binance` Python SDK.  

- **`BitGetFutures.py`**  
  Класс `BitGetFuturesTrade`, реализующий работу с BitGet (USDT-маржинальными контрактами). Использует библиотеку pybitget.  

- **`ByBitFutures.py`**  
  Класс `BybitFuturesTrade`, в котором применяется библиотека pybit.  

- **`OKXFutures.py`**  
  Класс `OkxFuturesTrade`, построенный на базе официальной библиотеки okx.  

## Установка

### 1. Клонировать репозиторий (или добавить файлы к себе в проект)
```bash
git clone https://github.com/keklick1337/multiexchangefutures.git
```

### 2. Установить необходимые зависимости
```bash
pip install -r requirements.txt
```
> **Примечание**: В зависимости от используемых классов могут понадобиться разные библиотеки (binance, pybit, okx, pybitget и т.д.). Убедитесь, что все нужные пакеты доступны в среде.

## Использование

Все классы работают по одному и тому же интерфейсу, определённому в `BaseFuturesTrade`.  
Например, вы можете:

```python
from multiexchangefutures.BinanceFutures import BinanceFuturesTrade
from multiexchangefutures.BitGetFutures import BitGetFuturesTrade

# Создать экземпляр для Binance (фьючерсы):
binance_trader = BinanceFuturesTrade.create(api_key="...", secret_key="...")

# Создать экземпляр для BitGet (фьючерсы):
bitget_trader = BitGetFuturesTrade.create(api_key="...", secret_key="...")

# Получить список символов
binance_symbols = binance_trader.get_trading_symbols()
bitget_symbols = bitget_trader.get_trading_symbols()

# Открыть позицию на Binance
binance_order = binance_trader.create_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="MARKET",
    quantity=0.001,
    leverage=10
)
```

## Примеры кода

Ниже – упрощённые примеры, демонстрирующие, как вызывать методы. Более полно – см. комментарии внутри соответствующих файлов.

### Пример использования с `BinanceFuturesTrade`

```python
from multiexchangefutures.BinanceFutures import BinanceFuturesTrade

# Инициализируем
binance = BinanceFuturesTrade.create(
    api_key="YOUR_BINANCE_API_KEY",
    secret_key="YOUR_BINANCE_SECRET_KEY",
    testnet=True  # Можно включить тестовую сеть
)

# Узнаём тек. баланс USDT:
balance = binance.get_futures_balance()
print("Futures Balance (USDT):", balance)

# Рассчитываем количество на 50 USDT при плече 10:
qty = binance.calculate_quantity_from_usdt(symbol="BTCUSDT", usdt_amount=50.0, leverage=10)
print("Quantity for 50 USDT with 10x leverage:", qty)

# Открываем маркет-ордер:
order_resp = binance.create_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="MARKET",
    quantity=qty,
    leverage=10
)
print("Order response:", order_resp)

# Закрываем соединение (по желанию)
binance.close()
```

### Пример использования с `BitGetFuturesTrade`

```python
from multiexchangefutures.BitGetFutures import BitGetFuturesTrade

bitget = BitGetFuturesTrade.create(api_key="...", secret_key="...")
acc_info = bitget.get_futures_account_info()
print("BitGet Futures Account Info:", acc_info)

# Проверяем максимальное плечо по символу BTCUSDT_UMCBL:
max_lev = bitget.get_max_leverage_for_symbol("BTCUSDT_UMCBL")
print("Max leverage for BTCUSDT_UMCBL:", max_lev)

# Создаём лимитный ордер на покупку 0.001 BTCUSDT по цене 20000:
resp = bitget.create_order(
    symbol="BTCUSDT_UMCBL",
    side="BUY",
    order_type="LIMIT",
    quantity=0.001,
    price=20000.0,
    leverage=5
)
print(resp)
bitget.close()
```

### Пример использования с `BybitFuturesTrade`

```python
from multiexchangefutures.ByBitFutures import BybitFuturesTrade

bybit = BybitFuturesTrade.create(api_key="...", api_secret="...", testnet=True)

# Получаем список инструментов (USDT Perpetual):
instruments = bybit.get_trading_symbols()
print("Bybit instruments:", instruments)

# Ставим новое плечо:
bybit.futures_change_leverage("BTCUSDT", 20)

# Создаем рыночный ордер:
bybit.create_order(
    symbol="BTCUSDT",
    side="Buy",
    order_type="Market",
    quantity=0.001,
    leverage=20
)

bybit.close()
```

### Пример использования с `OkxFuturesTrade`

```python
from multiexchangefutures.OKXFutures import OkxFuturesTrade

okx = OkxFuturesTrade.create(
    api_key="...",
    secret_key="...",
    passphrase="..."
)

# Баланс
acc = okx.get_account_info()
print("OKX Account:", acc)

# Открытые позиции
positions = okx.get_open_futures_positions()
print("Open positions:", positions)

# Создаём MARKET ордер на покупку
res = okx.create_order(
    symbol="BTC-USDT-SWAP",
    side="BUY",
    order_type="MARKET",
    quantity=1,
    leverage=10
)
print("Order result:", res)
okx.close()
```

## Расширение и добавление новых бирж

1. Создайте новый файл, например `MyExchangeFutures.py` в папке `multiexchangefutures`.
2. Импортируйте `BaseFuturesTrade`.
3. Наследуйтесь от класса `BaseFuturesTrade`.
4. Переопределите все необходимые методы (либо используйте заглушки, если ваша биржа не поддерживает какой-то функционал).
5. Вне при желании – добавьте импорт в `__init__.py`, чтобы можно было проще импортировать.

Пример структуры:

```python
# MyExchangeFutures.py
from .base_futures_trade import BaseFuturesTrade

class MyExchangeFuturesTrade(BaseFuturesTrade):
    def __init__(self, api_key, secret_key, ...):
        # ...
        pass
    
    @classmethod
    def create(cls, api_key, secret_key, ...):
        # ...
        return cls(api_key, secret_key, ...)
    
    def get_account_info(self) -> dict:
        # ...
        return {}
    
    # ... и т.д. для остальных методов
```

## Лицензия

Этот проект распространяется по лицензии MIT. Смотрите файл [LICENSE](LICENSE).

## Отказ от ответственности

1. Код предоставлен «как есть», без каких-либо гарантий.  
2. Использование торговых ботов, торговых библиотек и API на реальных счётах – это всегда **риск** потери средств.  
3. Автор и сообщество не несут ответственности за любые убытки, возникающие в результате использования данного ПО.  
4. Убедитесь, что вы понимаете риск маржинальной торговли и **тестируйте** на демо-средах или небольших объёмах, прежде чем использовать реальный капитал.  
