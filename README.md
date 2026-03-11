# VaR_GreenHill_Capital

A Python script to calculate the 1-day historical Value at Risk (VaR) and Conditional Value at Risk (CVaR / Expected Shortfall) for an investment club's multi-asset portfolio.


🚀 Features

    Historical VaR & CVaR Calculation: Computes the 1-day risk metrics based on historical price data fetched via Yahoo Finance.

    Dynamic Portfolio Weighting: Automatically adjusts and recalculates weights if certain stock data is unavailable, ensuring accurate risk representation.

    VaR Validity Checks (New):

        Subadditivity (Coherence): Verifies that the portfolio VaR is less than or equal to the sum of individual asset VaRs, confirming the diversification benefit.

        Basic Backtesting: Compares the empirical failure rate (m/n) against the target confidence level (1−c) to validate the model's accuracy.

🛠️ Installation & Setup

The script is ready-to-run. You just need the latest version of Python and a few standard libraries.

    Clone or download this repository.

    Install the required packages by running the following command in your terminal:

Bash

python -m pip install yfinance numpy pandas

📈 Usage

Simply execute the script in your terminal or IDE:
Bash

python your_script_name.py

The console will output the total portfolio value, the downloaded data status, the calculated 1-day VaR and CVaR, and the results of the validity checks.
