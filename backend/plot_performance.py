import os.path
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pytz

if __name__ == "__main__":
    # Load the data from CSV file
    data = pd.read_csv(
        "equity.csv", header=0,
        parse_dates=True, index_col=0
    )

    data.index = pd.to_datetime(data.index, utc=True)

    # Sort the data by the index (timestamp)
    data = data.sort_index()

    # Create a figure for plotting
    fig = plt.figure()

    # Set the outer background color to white
    fig.patch.set_facecolor('white')

    # Plot the equity curve
    ax1 = fig.add_subplot(311, ylabel='Portfolio value, %')
    data['equity_curve'].plot(ax=ax1, color="blue", lw=2)
    ax1.grid(True)

    # Plot the period returns
    ax2 = fig.add_subplot(312, ylabel='Period returns, %')
    data['returns'].plot(ax=ax2, color="black", lw=2)
    ax2.grid(True)

    # Plot the drawdowns
    ax3 = fig.add_subplot(313, ylabel='Drawdowns, %')
    data['drawdown'].plot(ax=ax3, color="red", lw=2)
    ax3.grid(True)

    # Show the plots
    plt.tight_layout()  # Adjust subplots to fit nicely
    plt.show()
