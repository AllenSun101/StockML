import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
from event_driven_backtest.strategy import Strategy
from event_driven_backtest.event import SignalEvent
from event_driven_backtest.backtest import Backtest
from event_driven_backtest.data import HistoricCSVDataHandler
from event_driven_backtest.execution import SimulatedExecutionHandler
from event_driven_backtest.portfolio import Portfolio

class MovingAverageCrossStrategy(Strategy):
    """
    Carries out a basic Moving Average Crossover strategy with a
    short/long simple weighted moving average. Default short/long
    windows are 100/400 periods respectively.
    """
    
    def __init__(self, bars, events, short_window=100, long_window=400):
        """
        Initialises the MovingAverageCrossStrategy.

        Parameters:
        bars - The DataHandler object that provides bar information.
        events - The EventQueue object.
        short_window - The short moving average lookback.
        long_window - The long moving average lookback.
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

        #Set to True if a symbol is in the market
        self.bought = self._calculate_initial_bought()

    def _calculate_initial_bought(self):
        """
        Adds keys to the bought dictionary for all symbols
        and sets them to 'OUT'.
        """
        bought = {}
        for s in self.symbol_list:
            bought[s] = 'OUT'
        return bought
    
    def calculate_signals(self, event):
        """
        Generates a new set of signals based on the MAC SMA with the short
        window crossing the long window, meaning a long entry and vice versa
        for a short entry.

        Parameters:
        event - A MarketEvent object.
        """
        if event.type == 'MARKET':
            for s in self.symbol_list:
                bars = self.bars.get_latest_bars_values(
                    s, "Adj Close", N=self.long_window
                )
                bar_date = self.bars.get_latest_bar_datetime(s)
                
                if bars is not None and len(bars) > 0:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])
                    symbol = s
                    dt = datetime.datetime.now(datetime.timezone.utc)
                    sig_dir = ""
                    
                    if short_sma > long_sma and self.bought[s] == "OUT":
                        print("LONG: %s" % bar_date)
                        sig_dir = 'LONG'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'LONG'
                    elif short_sma < long_sma and self.bought[s] == "LONG":
                        print("SHORT: %s" % bar_date)
                        sig_dir = 'EXIT'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[s] = 'OUT'


if __name__ == "__main__":
    symbol_list = ['AAPL']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(1990, 1, 1, 0, 0, 0)
    end_date = datetime.datetime(2001, 12, 31, 0, 0, 0)

    backtest = Backtest(
        symbol_list, initial_capital, heartbeat,
        start_date, end_date, HistoricCSVDataHandler, SimulatedExecutionHandler,
        Portfolio, MovingAverageCrossStrategy
    )
    backtest.simulate_trading()