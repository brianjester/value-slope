# Value Slope

This script compares annualized stock-price change with return smoothness for the top 50 tickers over the filtered five-year period. It prints the metrics and displays an XY chart; lower mean squared changes in monthly log returns indicate smoother returns.

Install the required packages with:

```powershell
python -m pip install "kagglehub[pandas-datasets]" matplotlib numpy pandas
```

Run with `python value-slope.py`.

![Stock slope and smoothness chart](screenshot.png)

## Next Steps

Add P/E ratio with color green is low, red is high: [S&P 500 companies financials](https://datahub.io/core/s-and-p-500-companies-financials) > constituents-financial 
