import datetime
import pandas as pd
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis
from event_driven_backtest.strategy import Strategy
from event_driven_backtest.event import SignalEvent
from event_driven_backtest.backtest import Backtest
from event_driven_backtest.data import HistoricCSVDataHandler
from event_driven_backtest.execution import SimulatedExecutionHandler
from event_driven_backtest.portfolio import Portfolio
import numpy as np
import yfinance as yf

def create_lagged_series(symbol, start_date, end_date, lags=5):
    """
    This creates a Pandas DataFrame that stores the percentage returns of the
    adjusted closing value of a stock obtained from Yahoo Finance, along with a
    number of lagged returns from the prior trading days (lags defaults to 5 days).
    Trading volume, as well as the Direction from the previous day, are also included.
    """
    # Obtain stock information from Yahoo Finance
    ts = yf.download(symbol, start=start_date - datetime.timedelta(days=365), end=end_date)

    # Create the new lagged DataFrame
    tslag = pd.DataFrame(index=ts.index)
    tslag["Today"] = ts["Adj Close"]
    tslag["Volume"] = ts["Volume"]
    
    # Create the shifted lag series of prior trading period close values
    for i in range(0, lags):
        tslag[f"Lag{i + 1}"] = ts["Adj Close"].shift(i + 1)
    
    # Create the returns DataFrame
    tsret = pd.DataFrame(index=tslag.index)
    tsret["Volume"] = tslag["Volume"]
    tsret["Today"] = tslag["Today"].pct_change() * 100.0
    
    # If any of the values of percentage returns equal zero, set them to
    # a small number (stops issues with QDA model in Scikit-Learn)
    for i, x in enumerate(tsret["Today"]):
        if abs(x) < 0.0001:
            tsret["Today"].iloc[i] = 0.0001
    
    # Create the lagged percentage returns columns
    for i in range(0, lags):
        tsret[f"Lag{i + 1}"] = tslag[f"Lag{i + 1}"].pct_change() * 100.0
    
    # Create the "Direction" column (+1 or -1) indicating an up/down day
    tsret["Direction"] = np.sign(tsret["Today"])
    tsret = tsret[tsret.index >= start_date]
    
    return tsret

class SPYDailyForecastStrategy(Strategy):
    """
    S&P 500 forecast strategy. It uses a Quadratic Discriminant
    Analyser to predict the returns for a subsequent time period
    and then generates long/exit signals based on the prediction.
    """
    def __init__(self, bars, events):
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.datetime_now = datetime.datetime.utcnow()
        self.model_start_date = datetime.datetime(2001, 1, 10)
        self.model_end_date = datetime.datetime(2005, 12, 31)
        self.model_start_test_date = datetime.datetime(2005, 1, 1)
        self.long_market = False
        self.short_market = False
        self.bar_index = 0
        self.model = self.create_symbol_forecast_model()

    def create_symbol_forecast_model(self):
        # Create a lagged series of the S&P 500 US stock market index
        snpret = create_lagged_series(
            self.symbol_list[0], self.model_start_date,
            self.model_end_date, lags=5
        )
        
        # Use the prior two days of returns as predictor values,
        # with direction as the response
        X = snpret[["Lag1", "Lag2"]]
        y = snpret["Direction"]
        
        # Create training and test sets
        start_test = self.model_start_test_date
        X_train = X[X.index < start_test]
        X_test = X[X.index >= start_test]
        y_train = y[y.index < start_test]
        y_test = y[y.index >= start_test]
        
        # Initialize and fit the QDA model
        model = QuadraticDiscriminantAnalysis()
        model.fit(X_train, y_train)
        
        return model

    def calculate_signals(self, event):
        """
        Calculate the Signal Events based on market data.
        """
        sym = self.symbol_list[0]
        dt = self.datetime_now
        
        if event.type == 'MARKET':
            self.bar_index += 1
            if self.bar_index > 5:
                # Retrieve the last three returns; if "returns" does not exist, calculate it
                lags = self.bars.get_latest_bars_values(sym, "Adj Close", N=3)
                
                if lags is not None and len(lags) >= 3:
                    # Calculate percentage changes if "returns" aren't precomputed
                    returns = [(lags[i+1] - lags[i]) / lags[i] * 100.0 for i in range(2)]
                    pred_series = pd.Series(
                        {
                            'Lag1': returns[0],
                            'Lag2': returns[1]
                        }
                    )
                    
                    pred = self.model.predict(pred_series.values.reshape(1, -1))[0]
                    
                    if pred > 0 and not self.long_market:
                        self.long_market = True
                        signal = SignalEvent(1, sym, dt, 'LONG', 1.0)
                        self.events.put(signal)
                    
                    elif pred < 0 and self.long_market:
                        self.long_market = False
                        signal = SignalEvent(1, sym, dt, 'EXIT', 1.0)
                        self.events.put(signal)

if __name__ == "__main__":
    symbol_list = ['SPY']
    initial_capital = 100000.0
    heartbeat = 0.0
    start_date = datetime.datetime(2006, 1, 3, 0, 0, 0)
    end_date = datetime.datetime(2014, 10, 10, 0, 0, 0)
    
    backtest = Backtest(
        symbol_list, initial_capital, heartbeat,
        start_date, end_date, HistoricCSVDataHandler, SimulatedExecutionHandler,
        Portfolio, SPYDailyForecastStrategy
    )
    
    backtest.simulate_trading()
