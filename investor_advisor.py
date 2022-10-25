# coding: utf-8
import warnings
warnings.filterwarnings('ignore')
import yfinance as yf
import os
import questionary
import pandas as pd
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
from alpaca_trade_api.common import URL
from MCForecastTools import MCSimulation
from datetime import datetime, timedelta


# Load the environment variables from the .env file
#by calling the load_dotenv function
load_dotenv(".\\SAMPLE.env")

# Using the YFinance library, make an API call to access the historical prices of Bitcoin over the last three years
btc = yf.Ticker("BTC-USD")
btc_hist = btc.history(period="1m")

# Collect the Bitcoin data into DataFrame 
btc_price_df = pd.DataFrame(btc_hist["Close"])
btc_price_df.dropna().copy()
btc_price_df["Close"] = btc_price_df["Close"].astype("float")

# Using the YFinance library, make an API call to access the historical prices of S&P 500 ETF over the last three years
spy = yf.Ticker("SPY")
spy_hist = spy.history(period="1m")

# Collect the S&P 500 ETF data into DataFrame 
spy_price_df = pd.DataFrame(spy_hist["Close"])
spy_price_df.dropna().copy()
spy_price_df["Close"] = spy_price_df["Close"].astype("float")

# Collect the initial investment 
monthly_investment = questionary.text("How much money would you like to invest monthly (50/50 split)?").ask()
monthly_investment = float(monthly_investment)

# Calculate the Bitcoin initial investment 
btc_investment = monthly_investment / 2
print(f"Monthly BTC Investment: ${btc_investment:.2f}")

# Calculate the daily number of Bitcoin coins based on the Bitcoin initial investment
btc_coins_list = []
for price in btc_price_df['Close']:
    btc_coins = btc_investment / price
    btc_coins_list.append(btc_coins)

# Calculate the total current Bitcoin coins based on recurring monthly investment and collect into DataFrame    
btc_price_df['Coins'] = btc_coins_list
btc_coins_df = pd.DataFrame(btc_price_df["Coins"])
btc_coins_df.reset_index(inplace=True)
btc_coins_df = btc_coins_df.rename(columns = {'index':'Date'})
btc_period = btc_coins_df.Date.dt.to_period("M")
avg_btc_coins_df = btc_coins_df.groupby(btc_period)['Coins'].mean()
total_btc_coins = avg_btc_coins_df.sum()
print(f"Total Current Bitcoin Coins: {total_btc_coins:.5f}")

# Calculate the total current Bitcoin wallet in USD using current Bitcoin price
btc_current_price = btc_price_df["Close"].iloc[-1]
print(f"Current Bitcoin Price: ${btc_current_price:.2f}") 
btc_usd_wallet = total_btc_coins * btc_current_price
print(f"Total Current Bitcoin Wallet (USD): ${btc_usd_wallet:.2f}")

# Calculate the S&p 500 ETF initial investment 
spy_investment = monthly_investment / 2
print(f"Monthly SPY Investment: ${spy_investment:.2f}")

# Calculate the daily number of S&P 500 ETF shares based on the S&P 500 ETF initial investment
spy_shares_list = []
for price in spy_price_df['Close']:
    spy_shares = spy_investment / price
    spy_shares_list.append(spy_shares)

# Calculate the total current S&P 500 ETF shares based on recurring monthly investment and collect into DataFrame
spy_price_df['Shares'] = spy_shares_list
spy_shares_df = pd.DataFrame(spy_price_df["Shares"])
spy_shares_df.reset_index(inplace=True)
spy_shares_df = spy_shares_df.rename(columns = {'index':'Date'})
spy_period = spy_shares_df.Date.dt.to_period("M")
avg_spy_shares_df = spy_shares_df.groupby(spy_period)['Shares'].mean()
total_spy_shares = avg_spy_shares_df.sum()
print(f"Total Current S&P 500 ETF Shares: {total_spy_shares:.5f}")

# Calculate the total current S&P 500 ETF wallet in USD using current S&P 500 ETF price
spy_current_price = spy_price_df["Close"].iloc[-1]
print(f"Current S&P 500 ETF Price: ${spy_current_price:.2f}")  
spy_usd_wallet = total_spy_shares * spy_current_price
print(f"Total Current S&P 500 ETF Wallet (USD): ${spy_usd_wallet:.2f}")

# Calculate the total value of portfolio in USD
total_portfolio = btc_usd_wallet + spy_usd_wallet
print(f"Total Value of Portfolio (USD): ${total_portfolio:.2f}")

# Create a savings DataFrame including the Bitcoin and S&P 500 ETF wallets
savings_df = pd.DataFrame(data=[btc_usd_wallet, spy_usd_wallet], columns=['Amount'], index=['Bitcoin', 'S&P 500 ETF'])

# Plot the total value of the member's portfolio (Bitcoin and S&P 500 ETF) in a pie chart
savings_df.plot.pie(y='Amount',figsize=(5, 5),title="Total Value of Portfolio (USD)",
                    autopct='%1.1f%%', shadow=True, startangle=0)

# Set the variables for the Alpaca API and secret keys
alpaca_api_key = os.getenv("ALPACA_API_KEY")
alpaca_secret_key = os.getenv("ALPACA_SECRET_KEY")

# Create the Alpaca tradeapi.REST object
api = tradeapi.REST(
    alpaca_api_key,
    alpaca_secret_key,
    URL('https://paper-api.alpaca.markets'),
    api_version = "v2"
)

# Set timeframe to 1Day
timeframe = "1Day"

# Set start and end dates of 3 years back from yesterday's date
today = datetime.today()
yesterday = today - timedelta(days=1)
one_month = today - timedelta(days=30)
#three_years = today - timedelta(days=756)
sDateStr = three_years.strftime("%Y-%m-%d")
eDateStr = yesterday.strftime("%Y-%m-%d")
start_date = pd.Timestamp(sDateStr, tz="America/New_York").isoformat()
end_date = pd.Timestamp(eDateStr, tz="America/New_York").isoformat()

# Use the Alpaca get_bars function to get current closing prices of S&P 500 ETF
spy_data = api.get_bars(
    ["SPY"],
    timeframe,
    start_date,
    end_date
).df

# Reorganize the S&P 500 ETF DataFrame
spy_data.index = spy_data.index.strftime('%Y-%m-%d')
SPY = spy_data[spy_data['symbol']=='SPY'].drop('symbol', axis=1)

# Use the Alpaca get_crypto_bars function to get current closing prices of Bitcoin
bitcoin_data = api.get_crypto_bars(
     ["BTCUSD"], 
     timeframe,
     start_date,
     end_date
).df

# Reorganize the Bitcoin DataFrame
bitcoin_data.index = bitcoin_data.index.strftime('%Y-%m-%d')
BTC = bitcoin_data[bitcoin_data['exchange']=='CBSE'].drop(['exchange','symbol'], axis=1)

# Combine Bitcoin and S&P 500 ETF DataFrames into one DataFrame and remove any null values
prices_df = pd.concat([BTC,SPY],axis=1, keys=['BTC','SPY'])
prices_df = prices_df.dropna().copy()

# Configure the Monte Carlo simulation to forecast 10 years cumulative returns
# The weights should be split 80% to BTC and 20% to SPY.
# Run 500 samples.
MC_tenyear_aggressive = MCSimulation(
    portfolio_data=prices_df,
    weights=[0.80, 0.20],
    num_simulation=500,
    num_trading_days=252*10,
)

# Run the Monte Carlo simulation to forecast 10 years cumulative returns
#MC_tenyear_aggressive.calc_cumulative_return()

# Visualize the 10-year Monte Carlo simulation by creating an
# overlay line plot
#MC_tenyear_aggressive.plot_simulation()

# Visualize the probability distribution of the 10-year Monte Carlo simulation 
#MC_tenyear_aggressive.plot_distribution()

# Generate summary statistics from the 10-year Monte Carlo simulation results
# Save the results as a variable
MC_tenyear_statistics = MC_tenyear_aggressive.summarize_cumulative_return()

# Use the lower and upper `95%` confidence intervals to calculate the range of the possible outcomes for the current crypt/stock portfolio
ci_lower_ten_cumulative_return = round(MC_tenyear_statistics[8]*monthly_investment,2)
ci_upper_ten_cumulative_return = round(MC_tenyear_statistics[9]*monthly_investment,2)

# Print the result of your calculations
print(f"There is a 95% chance that an initial investment of"
      f" ${monthly_investment:.2f} in the portfolio"
      f" over the next 10 years will end within the range of"
      f" ${ci_lower_ten_cumulative_return} and ${ci_upper_ten_cumulative_return}.")