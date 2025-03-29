# QuantumFlow Elite Bybit Configuration
# Time: 2025-03-29 07:44:10 UTC
# User: Ikaraoha

SETTINGS = {
    'base_lot': 0.01,
    'lot_growth_factor': 1.5,
    'margin_safety': 0.8,
    'risk_per_trade': 0.02,  # 2% risk per trade
    'max_drawdown': 20,  # 20% max drawdown
    'magic_number': 123456
}

PAIRS = {
    'BTCUSDT': {
        'optimal_hours': range(0, 24),  # 24/7 trading
        'max_spread': 5.0,
        'risk_settings': {
            'max_daily_trades': 5,
            'stop_loss_atr': 2.0,
            'take_profit_atr': 3.0,
            'trailing_start': 1.5,
            'trailing_step': 0.5
        }
    },
    'ETHUSDT': {
        'optimal_hours': range(0, 24),
        'max_spread': 5.0,
        'risk_settings': {
            'max_daily_trades': 5,
            'stop_loss_atr': 2.0,
            'take_profit_atr': 3.0,
            'trailing_start': 1.5,
            'trailing_step': 0.5
        }
    }
}
