"""
QuantumFlow Elite Bybit - Micro Account Edition
Last Updated: 2025-03-29 08:50:23 UTC
User: Ikaraoha
Version: 2.1.0
"""

# Dynamic trade limits based on balance
TRADE_LIMIT_TIERS = {
    10: 4,    # $10-$24: 4 trades per pair
    25: 6,    # $25-$49: 6 trades per pair
    50: 8,    # $50-$99: 8 trades per pair
    100: 10,  # $100-$249: 10 trades per pair
    250: 12,  # $250-$499: 12 trades per pair
    500: 15,  # $500-$999: 15 trades per pair
    1000: 20  # $1000+: 20 trades per pair
}

SETTINGS = {
    'base_lot': 0.001,  # Micro lot base size
    'lot_growth_factor': 1.15,  # Conservative growth
    'margin_safety': 0.95,  # High safety margin
    'risk_per_trade': 0.015,  # 1.5% risk per trade
    'max_drawdown': 10,  # Maximum 10% drawdown
    'max_daily_loss': 5,  # Maximum 5% daily loss
    'magic_number': 20250329,  # Based on deployment date
    'recovery_mode': True,  # Enable recovery after losses
    'compound_profits': True  # Enable profit compounding
}

# Optimized pairs for micro accounts
PAIRS = {
    'EURUSD': {
        'optimal_hours': range(6, 16),  # London + NY overlap
        'max_spread': 1.5,  # Tight spread requirement
        'min_volume': 100,  # Minimum volume requirement
        'risk_settings': {
            'base_daily_trades': 4,  # Base number, scales with balance
            'stop_loss_atr': 1.2,  # Tight stop loss
            'take_profit_atr': 2.4,  # 1:2 risk-reward
            'trailing_start': 1.0,
            'trailing_step': 0.2,
            'max_position_size': 0.05  # 5% max position
        }
    },
    'GBPUSD': {
        'optimal_hours': range(7, 15),  # London session focus
        'max_spread': 1.8,
        'min_volume': 80,
        'risk_settings': {
            'base_daily_trades': 3,  # Base number, scales with balance
            'stop_loss_atr': 1.3,
            'take_profit_atr': 2.6,
            'trailing_start': 1.1,
            'trailing_step': 0.25,
            'max_position_size': 0.04
        }
    },
    'USDJPY': {
        'optimal_hours': range(0, 7),  # Asian session focus
        'max_spread': 1.6,
        'min_volume': 90,
        'risk_settings': {
            'base_daily_trades': 3,  # Base number, scales with balance
            'stop_loss_atr': 1.25,
            'take_profit_atr': 2.5,
            'trailing_start': 1.05,
            'trailing_step': 0.22,
            'max_position_size': 0.04
        }
    }
}

# Recovery settings
RECOVERY_SETTINGS = {
    'enabled': True,
    'max_consecutive_losses': 3,
    'lot_reduction': 0.5,  # Reduce lot size by 50% after losses
    'min_recovery_balance': 8.0,  # Minimum balance to continue trading
    'cool_off_period': 4  # Hours to wait after max losses
}

# Advanced compounding settings
COMPOUND_SETTINGS = {
    'base_increment': 0.1,  # 10% increase per level
    'profit_threshold': 5.0,  # $5 profit to increase level
    'max_level': 5,  # Maximum compounding level
    'reset_on_loss': True  # Reset level on significant loss
}