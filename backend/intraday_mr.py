import datetime
import numpy as np
import pandas as pd
import statsmodels.api as sm
from event_driven_backtest.strategy import Strategy
from event_driven_backtest.event import SignalEvent
from event_driven_backtest.backtest import Backtest
from event_driven_backtest.hft_data import HistoricCSVDataHandlerHFT
from event_driven_backtest.hft_portfolio import PortfolioHFT
from event_driven_backtest.execution import SimulatedExecutionHandler

class IntradayOLSMRStrategy(Strategy):
    """
    Uses ordinary least squares (OLS) to perform a rolling linear
    regression to determine the hedge ratio between a pair of equities.
    The z-score of the residuals time series is then calculated in a
    rolling fashion. If it exceeds an interval of thresholds
    (defaulting to [0.5, 3.0]), then a long/short signal pair is generated
    (for the high threshold) or an exit signal pair is generated (for the
    low threshold).
    """
    def __init__(self, bars, events, ols_window=100, zscore_low=0.5, zscore_high=3.0):
        """
        Initializes the stat arb strategy.

        Parameters:
        - bars: The DataHandler object that provides bar information
        - events: The EventQueue object
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.ols_window = ols_window
        self.zscore_low = zscore_low
        self.zscore_high = zscore_high
        self.pair = ('AAPL', 'GOOG')
        self.datetime = datetime.datetime.utcnow()
        self.long_market = False
        self.short_market = False

    def calculate_xy_signals(self, zscore_last):
        """
        Calculates the actual x, y signal pairings
        to be sent to the signal generator.

        Parameters:
        - zscore_last: The current z-score to test against
        """
        y_signal = None
        x_signal = None
        p0 = self.pair[0]
        p1 = self.pair[1]
        dt = self.datetime
        hr = abs(self.hedge_ratio)
        
        # If we're long the market and below the negative of the high z-score threshold
        if zscore_last <= -self.zscore_high and not self.long_market:
            self.long_market = True
            y_signal = SignalEvent(1, p0, dt, 'LONG', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'SHORT', hr)
        
        # If we're long the market and between the absolute value of the low z-score threshold
        if abs(zscore_last) <= self.zscore_low and self.long_market:
            self.long_market = False
            y_signal = SignalEvent(1, p0, dt, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'EXIT', 1.0)
        
        # If we're short the market and above the high z-score threshold
        if zscore_last >= self.zscore_high and not self.short_market:
            self.short_market = True
            y_signal = SignalEvent(1, p0, dt, 'SHORT', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'LONG', hr)
        
        # If we're short the market and between the absolute value of the low z-score threshold
        if abs(zscore_last) <= self.zscore_low and self.short_market:
            self.short_market = False
            y_signal = SignalEvent(1, p0, dt, 'EXIT', 1.0)
            x_signal = SignalEvent(1, p1, dt, 'EXIT', 1.0)
        
        return y_signal, x_signal

    def calculate_signals_for_pairs(self):
        """
        Generates a new set of signals based on the mean reversion strategy.
        Calculates the hedge ratio between the pair of tickers. 
        We use OLS for this, although ideally, we should use CADF.
        """
        # Obtain the latest window of values for each component of the pair of tickers
        y = self.bars.get_latest_bars_values(self.pair[0], "Adj Close", N=self.ols_window)
        x = self.bars.get_latest_bars_values(self.pair[1], "Adj Close", N=self.ols_window)
        
        if y is not None and x is not None:
            # Check that all window periods are available
            if len(y) >= self.ols_window and len(x) >= self.ols_window:
                # Calculate the current hedge ratio using OLS
                self.hedge_ratio = sm.OLS(y, x).fit().params[0]
                
                # Calculate the current z-score of the residuals
                spread = y - self.hedge_ratio * x
                zscore_last = (spread - spread.mean()) / spread.std()
                zscore_last = zscore_last[-1]
                
                # Calculate signals and add them to the events queue
                y_signal, x_signal = self.calculate_xy_signals(zscore_last)
                if y_signal is not None and x_signal is not None:
                    self.events.put(y_signal)
                    self.events.put(x_signal)

    def calculate_signals(self, event):
        """
        Calculate the Signal Events based on market data.
        """
        if event.type == 'MARKET':
            self.calculate_signals_for_pairs()
    
if __name__ == "__main__":
    symbol_list = ['AAPL', 'GOOG']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2024, 10, 8, 10, 41, 0)
    end_date = datetime.datetime(2024, 10, 12, 10, 41, 0)

    backtest = Backtest(
        symbol_list, initial_capital, heartbeat,
        start_date, end_date, HistoricCSVDataHandlerHFT, SimulatedExecutionHandler,
        PortfolioHFT, IntradayOLSMRStrategy
    )
    
    backtest.simulate_trading()

