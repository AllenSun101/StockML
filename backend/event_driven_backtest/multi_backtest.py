import datetime
import pprint
import queue
import time

class MultiBacktest(object):
    """
    Enscapsulates the settings and components for carrying out an event-driven backtest.
    """

    def __init__(
    self, symbol_list, initial_capital,
    heartbeat, start_date, end_date, data_handler,
    execution_handler, portfolio, strategy, strat_params_list
):
        """
        Initialises the backtest.
        Parameters:
        symbol_list - The list of symbol strings.
        initial_capital - The starting capital for the portfolio.
        heartbeat - Backtest "heartbeat" in seconds.
        start_date - The start date/time of the strategy.
        data_handler - (Class) Handles the market data feed.
        execution_handler - (Class) Handles the orders/fills for trades.
        portfolio - (Class) Keeps track of portfolio current and prior positions.
        strategy - (Class) Generates signals based on market data.
        """
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start_date = start_date
        self.end_date = end_date
        
        self.data_handler_cls = data_handler
        self.execution_handler_cls = execution_handler
        self.portfolio_cls = portfolio
        self.strategy_cls = strategy
        
        self.events = queue.Queue()
        
        self.signals = 0
        self.orders = 0
        self.fills = 0
        self.num_strats = 1

        self.strat_params_list = strat_params_list
        
        self._generate_trading_instances(self.strat_params_list)

    def _generate_trading_instances(self, strategy_params_dict):
        """
        Generates the trading instance objects from their class types.
        """
        print("Creating DataHandler, Strategy, Portfolio, and ExecutionHandler for")
        print("strategy parameter list: %s..." % strategy_params_dict)

        # Create DataHandler instance
        self.data_handler = self.data_handler_cls(
            self.events, self.symbol_list, self.start_date, self.end_date
        )

        # Create Strategy instance
        self.strategy = self.strategy_cls(
            self.data_handler, self.events
        )

        # Create Portfolio instance
        self.portfolio = self.portfolio_cls(
            self.data_handler, self.events, self.start_date,
            self.initial_capital
        )

        # Create ExecutionHandler instance
        self.execution_handler = self.execution_handler_cls(self.events)

    def _run_backtest(self):
        """
        Executes the backtest.
        """
        i=0
        while True:
            i += 1
            # print(i)
            # Update the market bars
            if self.data_handler.continue_backtest == True:
                self.data_handler.update_bars()
            else:
                break
            
            # Handle the events
            while True:
                try:
                    event = self.events.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:
                        if event.type == 'MARKET':
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_timeindex(event)
                        elif event.type=='SIGNAL':
                            self.signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == 'ORDER':
                            self.orders+=1
                            self.execution_handler.execute_order(event)
                        elif event.type == 'FILL':
                            self.fills+=1
                            self.portfolio.update_fill(event)
                            
            time.sleep(self.heartbeat)

    def _output_performance(self):
        """
        Outputs the strategy performance from the backtest.
        """

        self.portfolio.create_equity_curve_dataframe()

        print("Creating summary stats...")
        stats = self.portfolio.output_summary_stats()
        
        print("Creating equity curve...")
        print(self.portfolio.equity_curve.tail(10))
        pprint.pprint(stats)

        print("Signals:%s" % self.signals)
        print("Orders:%s" % self.orders)
        print("Fills:%s" % self.fills)

        return stats

    def simulate_trading(self):
        """
        Simulates the backtest and outputs portfolio performance.
        """
        out = open("output.csv", "w")
        spl = len(self.strat_params_list)
        
        for i, sp in enumerate(self.strat_params_list):
            print("Strategy %s out of %s..." % (i + 1, spl))
            
            # Generate trading instances
            self._generate_trading_instances(sp)
            
            # Run backtest
            self._run_backtest()
            
            # Get performance stats
            stats = self._output_performance()
            pprint.pprint(stats)
            

            # Extract performance metrics
            tot_ret = float(stats[0][1].replace("%", ""))
            sharpe = float(stats[1][1])
            max_dd = float(stats[2][1].replace("%", ""))
            dd_dur = int(stats[3][1])
            
            # Write the results to the output file
            out.write(
                "%s,%s,%s,%s,%s,%s,%s\n" % (
                    sp["ols_window"], sp["zscore_high"], sp["zscore_low"],
                    tot_ret, sharpe, max_dd, dd_dur
                )
            )
        
        out.close()
