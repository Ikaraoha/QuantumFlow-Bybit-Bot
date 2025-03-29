"""
QuantumFlow Elite Bybit v1.0
Time: 2025-03-29 07:44:10 UTC
User: Ikaraoha
Status: Production Ready
"""

import os
import time
import logging
import math
import pandas as pd
import numpy as np
import talib
from datetime import datetime
from typing import Dict, Optional
from pybit.unified_trading import HTTP
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import PAIRS, SETTINGS

class QuantumFlowBybit:
    def __init__(self):
        self.timestamp = "2025-03-29 07:44:10"
        self.user = "Ikaraoha"
        self.logger = self.setup_logging()
        self.settings = SETTINGS
        self.pairs = PAIRS
        self.trades_today = {pair: 0 for pair in PAIRS}
        
        # Initialize Bybit client
        self.client = HTTP(
            testnet=False,
            api_key=os.getenv('BYBIT_API_KEY'),
            api_secret=os.getenv('BYBIT_API_SECRET')
        )
        
        # Initialize Telegram bot
        self.telegram_bot = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.setup_telegram_commands()
        
        self.initial_balance = self.get_account_balance()
        self.logger.info(f"Starting balance: ${self.initial_balance:.2f}")
        self.send_telegram_message(f"🚀 Bot Started\nInitial Balance: ${self.initial_balance:.2f}")

    def setup_logging(self) -> logging.Logger:
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            filename=f'logs/quantum_flow_{datetime.now().strftime("%Y%m%d")}.log',
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] - %(message)s'
        )
        return logging.getLogger("QuantumFlow")

    def setup_telegram_commands(self):
        self.telegram_bot.add_handler(CommandHandler("status", self.cmd_status))
        self.telegram_bot.add_handler(CommandHandler("balance", self.cmd_balance))
        self.telegram_bot.add_handler(CommandHandler("positions", self.cmd_positions))
        self.telegram_bot.add_handler(CommandHandler("stop", self.cmd_stop))
        self.telegram_bot.add_handler(CommandHandler("start", self.cmd_start))
        self.telegram_bot.add_handler(CommandHandler("trades", self.cmd_trades))
        self.telegram_bot.add_handler(CommandHandler("settings", self.cmd_settings))

    async def send_telegram_message(self, message: str):
        try:
            await self.telegram_bot.bot.send_message(
                chat_id=self.telegram_chat_id,
                text=message,
                parse_mode='HTML'
            )
        except Exception as e:
            self.logger.error(f"Telegram message error: {str(e)}")

    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        balance = self.get_account_balance()
        positions = self.get_positions()
        
        status_msg = (
            "📊 <b>Bot Status Report</b>\n"
            f"Balance: ${balance:.2f}\n"
            f"Active Positions: {len(positions)}\n"
            f"Trades Today: {sum(self.trades_today.values())}\n"
            f"Running since: {self.timestamp}"
        )
        await update.message.reply_html(status_msg)

    async def cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        balance = self.get_account_balance()
        await update.message.reply_html(f"💰 Current Balance: ${balance:.2f}")

    async def cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        positions = self.get_positions()
        if not positions:
            await update.message.reply_text("No open positions")
            return
            
        positions_msg = "📈 <b>Open Positions</b>\n"
        for pos in positions:
            positions_msg += (
                f"Symbol: {pos['symbol']}\n"
                f"Side: {pos['side']}\n"
                f"Size: {pos['size']}\n"
                f"Entry: {pos['entry_price']:.5f}\n"
                f"Current: {pos['current_price']:.5f}\n"
                f"PnL: {pos['unrealised_pnl']:.2f}\n"
                "---------------\n"
            )
        await update.message.reply_html(positions_msg)

    async def cmd_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        trades_msg = "🔄 <b>Today's Trades</b>\n"
        for pair, count in self.trades_today.items():
            trades_msg += f"{pair}: {count}/{self.pairs[pair]['risk_settings']['max_daily_trades']}\n"
        await update.message.reply_html(trades_msg)

    async def cmd_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        settings_msg = (
            "⚙️ <b>Current Settings</b>\n"
            f"Base Lot: {self.settings['base_lot']}\n"
            f"Risk Per Trade: {self.settings['risk_per_trade']*100}%\n"
            f"Max Drawdown: {self.settings['max_drawdown']}%\n"
            "\n<b>Trading Pairs:</b>\n"
        )
        for pair, settings in self.pairs.items():
            settings_msg += (
                f"\n{pair}:\n"
                f"Max Daily Trades: {settings['risk_settings']['max_daily_trades']}\n"
                f"SL ATR: {settings['risk_settings']['stop_loss_atr']}\n"
                f"TP ATR: {settings['risk_settings']['take_profit_atr']}\n"
            )
        await update.message.reply_html(settings_msg)

    def get_account_balance(self) -> float:
        try:
            wallet_balance = self.client.get_wallet_balance(
                accountType="UNIFIED",
                coin="USDT"
            )
            return float(wallet_balance['result']['list'][0]['totalWalletBalance'])
        except Exception as e:
            self.logger.error(f"Balance check error: {str(e)}")
            return 0.0

    def get_positions(self) -> list:
        try:
            positions = self.client.get_positions(
                category="linear",
                settleCoin="USDT"
            )
            return [p for p in positions['result']['list'] if float(p['size']) > 0]
        except Exception as e:
            self.logger.error(f"Position check error: {str(e)}")
            return []

    def calculate_optimal_lot(self, symbol: str) -> float:
        try:
            current_balance = self.get_account_balance()
            
            # Calculate growth-based lot size
            growth_factor = current_balance / self.initial_balance
            optimal_lot = self.settings['base_lot'] * min(
                math.floor(growth_factor * self.settings['lot_growth_factor']), 
                10
            )
            
            # Apply risk management
            risk_per_trade = current_balance * self.settings['risk_per_trade']
            symbol_info = self.client.get_instruments_info(
                category="linear",
                symbol=symbol
            )['result']['list'][0]
            
            tick_size = float(symbol_info['priceFilter']['tickSize'])
            min_trading_qty = float(symbol_info['lotSizeFilter']['minOrderQty'])
            
            # Adjust lot size based on risk
            max_position_size = risk_per_trade / tick_size
            optimal_lot = min(optimal_lot, max_position_size)
            optimal_lot = max(optimal_lot, min_trading_qty)
            
            return round(optimal_lot, 3)
            
        except Exception as e:
            self.logger.error(f"Lot calculation error: {str(e)}")
            return self.settings['base_lot']

    def analyze_market_conditions(self, symbol: str) -> Dict:
        try:
            # Get kline data
            klines = self.client.get_kline(
                category="linear",
                symbol=symbol,
                interval=5,
                limit=100
            )['result']['list']
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'turnover'])
            df = df.astype(float)
            
            # Calculate indicators
            df['ema_8'] = talib.EMA(df['close'], timeperiod=8)
            df['ema_21'] = talib.EMA(df['close'], timeperiod=21)
            df['rsi'] = talib.RSI(df['close'], timeperiod=14)
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            return {
                "tradeable": True,
                "trend": "up" if df['ema_8'].iloc[-1] > df['ema_21'].iloc[-1] else "down",
                "rsi": df['rsi'].iloc[-1],
                "atr": df['atr'].iloc[-1],
                "momentum": self.calculate_momentum(df)
            }
        except Exception as e:
            self.logger.error(f"Analysis error: {str(e)}")
            return {"tradeable": False}

    def calculate_momentum(self, df: pd.DataFrame) -> float:
        try:
            close = df['close'].values
            rsi = talib.RSI(close, timeperiod=14)
            return min(100, abs(rsi[-1] - 50) / 50 * 100)
        except Exception:
            return 0.0

    def execute_trade(self, symbol: str, direction: str):
        try:
            if not self.validate_entry(symbol):
                return

            lot_size = self.calculate_optimal_lot(symbol)
            conditions = self.analyze_market_conditions(symbol)
            
            # Get current price
            ticker = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )['result']['list'][0]
            
            current_price = float(ticker['lastPrice'])
            
            # Calculate SL/TP levels
            atr = conditions["atr"]
            sl_multiplier = self.pairs[symbol]["risk_settings"]["stop_loss_atr"]
            tp_multiplier = self.pairs[symbol]["risk_settings"]["take_profit_atr"]
            
            if direction == "buy":
                stop_loss = current_price - (atr * sl_multiplier)
                take_profit = current_price + (atr * tp_multiplier)
            else:
                stop_loss = current_price + (atr * sl_multiplier)
                take_profit = current_price - (atr * tp_multiplier)
            
            # Place the order
            order = self.client.place_order(
                category="linear",
                symbol=symbol,
                side="Buy" if direction == "buy" else "Sell",
                orderType="Market",
                qty=str(lot_size),
                stopLoss=str(round(stop_loss, 5)),
                takeProfit=str(round(take_profit, 5)),
                timeInForce="GoodTillCancel",
                positionIdx=0  # One-Way Mode
            )
            
            if order['retCode'] == 0:
                self.trades_today[symbol] += 1
                self.logger.info(f"Trade executed: {symbol} {direction} {lot_size}")
                self.send_telegram_message(
                    f"✅ New Trade\n"
                    f"Symbol: {symbol}\n"
                    f"Direction: {direction.upper()}\n"
                    f"Size: {lot_size}\n"
                    f"Entry: {current_price:.5f}\n"
                    f"SL: {stop_loss:.5f}\n"
                    f"TP: {take_profit:.5f}"
                )
            else:
                self.logger.error(f"Trade failed: {order['retMsg']}")
                
        except Exception as e:
            self.logger.error(f"Trade error: {str(e)}")

    def validate_entry(self, symbol: str) -> bool:
        try:
            conditions = self.analyze_market_conditions(symbol)
            if not conditions["tradeable"]:
                return False

            current_hour = datetime.utcnow().hour
            
            # Get current spread
            ticker = self.client.get_tickers(
                category="linear",
                symbol=symbol
            )['result']['list'][0]
            
            spread = (float(ticker['askPrice']) - float(ticker['bidPrice'])) * 10000

            return all([
                current_hour in self.pairs[symbol]["optimal_hours"],
                spread <= self.pairs[symbol]["max_spread"],
                self.trades_today[symbol] < self.pairs[symbol]["risk_settings"]["max_daily_trades"],
                35 <= conditions["rsi"] <= 65,
                conditions["momentum"] > 60
            ])
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False

    def monitor_positions(self):
        try:
            positions = self.get_positions()
            if positions:
                for position in positions:
                    symbol = position['symbol']
                    ticker = self.client.get_tickers(
                        category="linear",
                        symbol=symbol
                    )['result']['list'][0]
                    
                    current_price = float(ticker['lastPrice'])
                    trailing_settings = self.pairs[symbol]["risk_settings"]
                    
                    if position['side'] == "Buy":
                        potential_profit = current_price - float(position['entry_price'])
                        if potential_profit > float(position['stop_loss']) * trailing_settings["trailing_start"]:
                            new_sl = current_price - (potential_profit * trailing_settings["trailing_step"])
                            if new_sl > float(position['stop_loss']):
                                self.modify_position_sl(position['id'], new_sl)
                    else:
                        potential_profit = float(position['entry_price']) - current_price
                        if potential_profit > float(position['stop_loss']) * trailing_settings["trailing_start"]:
                            new_sl = current_price + (potential_profit * trailing_settings["trailing_step"])
                            if new_sl < float(position['stop_loss']):
                                self.modify_position_sl(position['id'], new_sl)
                                
        except Exception as e:
            self.logger.error(f"Monitor error: {str(e)}")

    def modify_position_sl(self, position_id: str, new_sl: float):
        try:
            self.client.set_trading_stop(
                category="linear",
                symbol=position_id,
                stopLoss=str(round(new_sl, 5))
            )
        except Exception as e:
            self.logger.error(f"Modify SL error: {str(e)}")

    def run(self):
        try:
            self.logger.info(f"Bot started - Balance: ${self.get_account_balance():.2f}")
            
            # Start Telegram bot
            self.telegram_bot.run_polling(allowed_updates=Update.ALL_TYPES)
            
            while True:
                current_time = datetime.utcnow()
                
                # Reset daily trade counters at midnight UTC
                if current_time.hour == 0 and current_time.minute == 0:
                    self.trades_today = {pair: 0 for pair in self.pairs}
                
                for symbol in self.pairs:
                    conditions = self.analyze_market_conditions(symbol)
                    if conditions["tradeable"]:
                        direction = "buy" if conditions["trend"] == "up" else "sell"
                        self.execute_trade(symbol, direction)
                
                # Monitor positions
                self.monitor_positions()
                
                # Sleep to avoid API rate limits
                time.sleep(5)
                
        except KeyboardInterrupt:
            self.logger.info(f"Bot stopped - Final Balance: ${self.get_account_balance():.2f}")
            self.send_telegram_message("🛑 Bot stopped manually")

if __name__ == "__main__":
    bot = QuantumFlowBybit()
    bot.run()
