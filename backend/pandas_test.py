import datetime
import yfinance as yf
import pandas_datareader.data as web

if __name__ == "__main__":
    # Use yfinance as the data source
    yf.pdr_override()

    spy = web.get_data_yahoo(
        "SPY", 
        start=datetime.datetime(2007, 1, 1), 
        end=datetime.datetime(2015, 6, 15)
    )

    print(spy.tail())
