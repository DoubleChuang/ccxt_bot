from typing import Union

import ccxt

from ccxt_bot.trade.base import StrategyResult, Suggestion
from ccxt_bot.core.logger import logger


class Trader():
    def __init__(self, exchange: ccxt.binance, symbol: str, sandbox: bool = True):
        self._exchange = exchange
        self._symbol = symbol
        self._sandbox = sandbox
    
    def fetch_balance(self) -> tuple:
        balance = self._exchange.fetch_balance(
            params={'type':'margin', 'isIsolated': 'TRUE'}
        )

        currency1, currency2 = self._symbol.split("/")
        
        return (currency1, currency2), (balance[currency1], balance[currency2])
    
    def calc_amount(self):
        """獲取目前可以交易的金額
   
   
        ETH Balance: {'free': 0.0002, 'used': 0.0, 'total': 0.0002, 'debt': 0.05}
        USDT Balance: {'free': 559.9662597, 'used': 0.0, 'total': 559.9662597, 'debt': 0.0}

        ETH: {'free': 0.7, 'used': 0.0, 'total': 0.7, 'debt': 0}
        USDT: {'free': 464.1267597, 'used': 0.0, 'total': 464.1267597, 'debt': 900}
        """
        _, currency_balance = self.fetch_balance()
        ticker = self._exchange.fetch_ticker(self._symbol)
        # logger.debug(f"ticker :{ticker['close']}"
        
        bal_total_0 = currency_balance[0]["total"] - currency_balance[0]["debt"]
        bal_total_1 = currency_balance[1]["total"] - currency_balance[1]["debt"]
        
        return bal_total_1/ticker["close"] + bal_total_0
        
    def create_order(self, result: StrategyResult, percent_of_equity: int = 30):
        """ create_order
        
        做多: 還款 獲取目前總體餘額 並使用其30%買入
        做空: 還款 獲取目前總體餘額 並使用其30%買入
        做多平倉(TP or SL): 將目前ETH/USDT的ETH total變成0，也就是賣出所有可以用的餘額
        做空平倉(TP or SL): 

        Args:
            suggestion (Suggestion): _description_
        """
        if result.suggestion == Suggestion.DoNothing:
            logger.debug(f'suggest do nothing 💎')
            return
        
        (currency1, currency2), currency_balance = self.fetch_balance()
        amount = self._exchange.amount_to_precision(
            self._symbol,
            self.calc_amount() * percent_of_equity/100
        )
        
        if result.suggestion == Suggestion.Long:
            # 將獲取總額 並計算3成的錢
            # 買入訂單 並設定OCO或停損單

            logger.info(
                f"""
                [{result.suggestion.name}] (sandbox mode {"🟢"if self._sandbox else "🔴"}):
                    amount:      {amount}
                    Stop Loss:   {result.stop_price}
                    Take profit: {result.tp_price}
                """
            )
            
            # 如果是沙盒模式 則跳過購買
            if self._sandbox: return
            
            # 市價買入
            order = self._exchange.create_order(
                symbol=self._symbol, 
                type='market',
                side='buy',
                amount=amount,
                price=None,
                params={
                    # 'clientOrderId': 'ccxt_bot',
                    'type':'margin',
                }
            )
            logger.info(f"[Buy]: {order}")
            # 如果有停損價 市價買入
            if result.stop_price is not None and result.tp_price is not None:
                # https://github.com/ccxt/ccxt/issues/8241
                # https://github.com/ccxt/ccxt/blob/7b9badf71d85bf67f8d8799d3f17fdc1516718be/python/ccxt/abstract/binance.py#L199
                order = self._exchange.sapi_post_margin_order_oco({
                        'symbol': self._exchange.market(self._symbol)['id'],
                        'side': 'SELL',  # SELL, BUY
                        'quantity': amount,
                        'price': self._exchange.price_to_precision(self._symbol, result.tp_price),
                        'stopPrice': self._exchange.price_to_precision(self._symbol, result.stop_price),
                        'stopLimitPrice': self._exchange.price_to_precision(self._symbol, result.stop_price),  # If provided, stopLimitTimeInForce is required
                        'stopLimitTimeInForce': 'GTC',  # GTC, FOK, IOC
                        # 'listClientOrderId': exchange.uuid(),  # A unique Id for the entire orderList
                        # 'limitClientOrderId': exchange.uuid(),  # A unique Id for the limit order
                        # 'limitIcebergQty': exchangea.amount_to_precision(symbol, limit_iceberg_quantity),
                        # 'stopClientOrderId': exchange.uuid()  # A unique Id for the stop loss/stop loss limit leg
                        # 'stopIcebergQty': exchange.amount_to_precision(symbol, stop_iceberg_quantity),
                        # 'newOrderRespType': 'ACK',  # ACK, RESULT, FULL
                })
                logger.info(f"[Buy] OCO: {order}")
            elif result.stop_price is not None:
                stop_price = self._exchange.price_to_precision(self._symbol, result.stop_price)
                
                order = self._exchange.create_order(
                    symbol=self._symbol,
                    type='stop_loss_limit',
                    side='sell',
                    amount=amount,
                    price=stop_price, 
                    params={
                        # 'clientOrderId': 'ccxt_bot',
                        'type':'margin',
                        'stopPrice': stop_price
                    }
                )
            
                logger.info(f"[Buy] SL: {order}")
        elif result.suggestion == Suggestion.Short:
            # 將獲取總額 並計算3成的錢
            # 借款賣出訂單 並設定OCO或停損單
            
            logger.info(
                f"""
                [{result.suggestion.name}] (sandbox mode {"🟢"if self._sandbox else "🔴"}):
                    amount:      {amount}
                    Stop Loss:   {result.stop_price}
                    Take profit: {result.tp_price}
                """
            )
            
            # 如果是沙盒模式 則跳過購買
            if self._sandbox: return
            
            # 借款
            self._exchange.borrowMargin (
                currency1, # ETH
                amount,
                symbol=self._symbol,
                params={
                    # 'clientOrderId': 'ccxt_bot',
                    'type':'margin',
                    'isIsolated': 'FALSE'
                }
            )
            # 市價賣出
            order = self._exchange.create_order(
                symbol=self._symbol, 
                type='market',
                side='sell',
                amount=amount,
                price=None,
                params={
                    # 'clientOrderId': 'ccxt_bot',
                    'type':'margin',
                }
            )
            logger.info(f"[Sell]: {order}")
            # 如果有停損價 市價買入
            if result.stop_price is not None and result.tp_price is not None:
                # https://github.com/ccxt/ccxt/issues/8241
                # https://github.com/ccxt/ccxt/blob/7b9badf71d85bf67f8d8799d3f17fdc1516718be/python/ccxt/abstract/binance.py#L199
                order = self._exchange.sapi_post_margin_order_oco({
                        'symbol': self._exchange.market(self._symbol)['id'],
                        'side': 'BUY',  # SELL, BUY
                        'quantity': amount,
                        'price': self._exchange.price_to_precision(self._symbol, result.tp_price),
                        'stopPrice': self._exchange.price_to_precision(self._symbol, result.stop_price),
                        'stopLimitPrice': self._exchange.price_to_precision(self._symbol, result.stop_price),  # If provided, stopLimitTimeInForce is required
                        'stopLimitTimeInForce': 'GTC',  # GTC, FOK, IOC
                        # 'listClientOrderId': exchange.uuid(),  # A unique Id for the entire orderList
                        # 'limitClientOrderId': exchange.uuid(),  # A unique Id for the limit order
                        # 'limitIcebergQty': exchangea.amount_to_precision(symbol, limit_iceberg_quantity),
                        # 'stopClientOrderId': exchange.uuid()  # A unique Id for the stop loss/stop loss limit leg
                        # 'stopIcebergQty': exchange.amount_to_precision(symbol, stop_iceberg_quantity),
                        # 'newOrderRespType': 'ACK',  # ACK, RESULT, FULL
                })
                logger.info(f"[Sell] OCO: {order}")
            elif result.stop_price is not None:
                stop_price = self._exchange.price_to_precision(self._symbol, result.stop_price)
                
                order = self._exchange.create_order(
                    symbol=self._symbol,
                    type='stop_loss_limit',
                    side='buy',
                    amount=amount,
                    price=stop_price, 
                    params={
                        # 'clientOrderId': 'ccxt_bot',
                        'type':'margin',
                        'stopPrice': stop_price
                    }
                )
            
                logger.info(f"[Sell] SL: {order}")
        elif result.suggestion == Suggestion.Long_SL or result.suggestion == Suggestion.Long_TP:
            logger.info(
                f"""
                [{result.suggestion.name}] (sandbox mode {"🟢"if self._sandbox else "🔴"}):
                    amount:      {amount}
                    Stop Loss:   {result.stop_price}
                    Take profit: {result.tp_price}
                """
            )
            
            # 如果是沙盒模式 則跳過購買
            if self._sandbox: return
            
            # 獲取委託單
            open_orders = self._exchange.fetch_open_orders(
                symbol=self._symbol, 
                params={
                    'type':'margin',
                }
            )
            
            # 取消 委託賣出單
            for order in open_orders:
                if order['info']['symbol'] == self._exchange.market(self._symbol)['id'] and \
                    order['info']['side'] == 'SELL':
                    self._exchange.cancel_order(order['info']['orderId'])
            
            _, currency_balance = self.fetch_balance()
            amount = self._exchange.amount_to_precision(
                self._symbol,
                currency_balance[0]['free']
            )
            
            order = self._exchange.create_order(
                    symbol=self._symbol,
                    type='market',
                    side='sell',
                    amount=amount,
                    price=None, 
                    params={
                        # 'clientOrderId': 'ccxt_bot',
                        'type':'margin',
                    }
                )
            
        elif result.suggestion == Suggestion.Short_SL or result.suggestion == Suggestion.Short_TP:
            logger.info(
                f"""
                [{result.suggestion.name}] (sandbox mode {"🟢"if self._sandbox else "🔴"}):
                    amount:      {amount}
                    Stop Loss:   {result.stop_price}
                    Take profit: {result.tp_price}
                """
            )
            
            # 如果是沙盒模式 則跳過購買
            if self._sandbox: return
            
            # 獲取委託單
            open_orders = self._exchange.fetch_open_orders(
                symbol=self._symbol, 
                params={
                    'type':'margin',
                }
            )
            # 取消 委託買入單
            for order in open_orders:
                if order['info']['symbol'] == self._exchange.market(self._symbol)['id'] and \
                    order['info']['side'] == 'BUY':
                    self._exchange.cancel_order(order['info']['orderId'])
            
            (currency1, currency2), currency_balance = self.fetch_balance()
            
            if currency_balance[0]['debt'] > 0:
                amount = self._exchange.amount_to_precision(
                    self._symbol,
                    currency_balance[0]['debt']
                )
                
                # 買回做空的幣
                order = self._exchange.create_order(
                        symbol=self._symbol,
                        type='market',
                        side='buy',
                        amount=amount,
                        price=None, 
                        params={
                            # 'clientOrderId': 'ccxt_bot',
                            'type':'margin',
                        }
                    )
        
                # 還款 
                # #https://docs.ccxt.com/#/?id=borrow-and-repay-margin
                self._exchange.repayMargin(
                    code=currency1,
                    amount=amount,
                    symbol=self._symbol,
                    params={
                        'type':'margin',
                        'isIsolated': 'FALSE'
                    }
                )
        else:
            logger.error(f'Unknown Suggestion: {result.suggestion}')
            return