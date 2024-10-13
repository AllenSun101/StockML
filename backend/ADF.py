from __future__ import print_function
# Import the Time Series library
import statsmodels.tsa.stattools as ts

# Import Datetime and the Pandas DataReader
from datetime import datetime
import pandas_datareader.data as web
import yfinance as yf

# Download the Amazon OHLCV data from 1/1/2000 to 1/1/2015
amzn = yf.download("AMZN", start="2000-01-01", end="2015-01-01")

# Output the results of the Augmented Dickey-Fuller test for Amazon
# with a lag order value of 1
result = ts.adfuller(amzn['Adj Close'], 1)

# First value is test statistic, second value is p-value, fourth is number of data points
# Fifth value dictionary contains critical values of test statistic at 1, 5, and 10 percent respectively
print("ADF Statistic:", result[0])
print("p-value:", result[1])
print("Data Points :", result[3])
print("Critical Values:", result[4])