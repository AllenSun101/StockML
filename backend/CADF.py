import datetime
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import yfinance as yf
import pprint
import statsmodels.tsa.stattools as ts
import statsmodels.api as sm

# inspect whether cointegration may be likely 
def plot_price_series(df, ts1, ts2):
    months = mdates.MonthLocator() # every month
    fig, ax = plt.subplots()
    ax.plot(df.index, df[ts1], label=ts1)
    ax.plot(df.index, df[ts2], label=ts2)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim(datetime.datetime(2012, 1, 1), datetime.datetime(2013, 1, 1))
    ax.grid(True)
    fig.autofmt_xdate()
    plt.xlabel('Month/Year')
    plt.ylabel('Price ($)')
    plt.title('%s and %s Daily Prices' % (ts1, ts2))
    plt.legend()
    plt.show()

# inspect whether linear relationship exists between two series
# whether good candidate for OLS procedure and ADF test
def plot_scatter_series(df, ts1, ts2):
    plt.xlabel('%s Price ($)' % ts1)
    plt.ylabel('%s Price ($)' % ts2)
    plt.title('%s and %s Price Scatterplot' % (ts1, ts2))
    plt.scatter(df[ts1], df[ts2])
    plt.show()

# residual prices
def plot_residuals(df):
    months = mdates.MonthLocator() # every month
    fig, ax = plt.subplots()
    ax.plot(df.index, df["res"], label="Residuals")
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.set_xlim(datetime.datetime(2012, 1, 1), datetime.datetime(2013, 1, 1))
    ax.grid(True)
    fig.autofmt_xdate()
    plt.xlabel('Month/Year')
    plt.ylabel('Price ($)')
    plt.title('Residual Plot')
    plt.legend()
    plt.plot(df["res"])
    plt.show()

if __name__ == "__main__":
    start = datetime.datetime(2012, 1, 1)
    end = datetime.datetime(2013, 1, 1)
    stock1 = yf.download("AAPL", start=start, end=end)
    stock2 = yf.download("GOOG", start=start, end=end)

    df = pd.DataFrame(index=stock1.index)
    df["stock1"] = stock1["Adj Close"]
    df["stock2"] = stock2["Adj Close"]

    # Plot the two time series
    plot_price_series(df, "stock1", "stock2")
    # Display a scatter plot of the two time series
    plot_scatter_series(df, "stock1", "stock2")

    # Define the dependent variable (y) and independent variable (X)
    y = df['stock2']
    X = df['stock1']

    # Add a constant to the independent variable (X)
    X = sm.add_constant(X)  # Adds a constant term to the predictor

    # Calculate optimal hedge ratio "beta"
    res = sm.OLS(y, X).fit()
    beta_hr = res.params.stock1

    # Calculate the residuals of the linear combination
    df["res"] = df["stock2"] - beta_hr*df["stock1"]

    # Plot the residuals
    plot_residuals(df)

    # Calculate and output the CADF test on the residuals
    cadf = ts.adfuller(df["res"])
    pprint.pprint(cadf)
