# Install dependencies as needed:
# pip install kagglehub[pandas-datasets] matplotlib
import kagglehub
from kagglehub import KaggleDatasetAdapter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Set the path to the file you'd like to load
file_path = "SnP_daily_update.csv"

# Load the latest version
df = kagglehub.dataset_load(
  KaggleDatasetAdapter.PANDAS,
  "yash16jr/s-and-p500-daily-update-dataset",
  file_path,
  pandas_kwargs={"header": [0, 1, 2]},
)

date_column = pd.to_datetime(df.iloc[:, 0], errors="coerce")
cutoff_date = pd.Timestamp.today().normalize() - pd.DateOffset(years=5)
date_filter = (date_column > cutoff_date) & (date_column.dt.day == 1)
filtered_df = df.loc[date_filter]
filtered_dates = date_column.loc[date_filter]
slopes = []

for column_index in range(1, filtered_df.shape[1]):
  if filtered_df.columns[column_index][0] != "Close":
    continue

  ticker = filtered_df.columns[column_index][1]
  prices = pd.to_numeric(
    filtered_df.iloc[:, column_index], errors="coerce"
  ).where(lambda values: values > 0)
  valid_prices = prices.dropna()
  if len(valid_prices) < 3:
    print(f"{ticker}: N/A (fewer than three positive prices)")
    continue

  price_dates = filtered_dates.loc[valid_prices.index]
  first_date = price_dates.iloc[0]
  last_date = price_dates.iloc[-1]
  elapsed_months = (
    (last_date.year - first_date.year) * 12
    + last_date.month
    - first_date.month
  )
  if elapsed_months <= 0:
    print(f"{ticker}: N/A (invalid starting price or date range)")
    continue

  annual_percentage_slope = (
    (valid_prices.iloc[-1] - valid_prices.iloc[0])
    / valid_prices.iloc[0]
    / (elapsed_months / 12)
    * 100
  )
  monthly_log_returns = np.log(prices / prices.shift(1))
  squared_return_changes = monthly_log_returns.diff().pow(2).dropna()
  if squared_return_changes.empty:
    print(f"{ticker}: N/A (not enough monthly returns for smoothness)")
    continue

  smoothness = squared_return_changes.mean()
  slopes.append((ticker, annual_percentage_slope, smoothness))

slopes_df = pd.DataFrame(
  slopes,
  columns=["Ticker", "AnnualPercentageSlope", "MeanSquaredReturnChange"],
)
# slopes_df = slopes_df.loc[slopes_df["Ticker"] != "SNDK"]
slopes_df = slopes_df.sort_values(
  "AnnualPercentageSlope", ascending=False
).reset_index(drop=True)
slopes_df = slopes_df.head(50)
print(f"Plotting {len(slopes_df)} tickers.")

for row in slopes_df.itertuples(index=False):
  print(
    f"{row.Ticker}: {row.AnnualPercentageSlope:.4f}% per year, "
    f"smoothness={row.MeanSquaredReturnChange:.8f}"
  )

ticker_data_url = (
  "https://raw.githubusercontent.com/browser-vm/us-stock-tickers/"
  "refs/heads/main/us_stock_tickers.csv"
)
ticker_data = pd.read_csv(ticker_data_url)
company_names = ticker_data.set_index("ticker_symbol")["company_name"]
slopes_df["CompanyName"] = slopes_df["Ticker"].map(company_names)
missing_names = slopes_df.loc[slopes_df["CompanyName"].isna(), "Ticker"]
if not missing_names.empty:
  print(f"Company names not found for: {', '.join(missing_names)}")
slopes_df["ChartLabel"] = slopes_df.apply(
  lambda row: (
    f"{row['Ticker']} - {row['CompanyName']}"
    if pd.notna(row["CompanyName"])
    else row["Ticker"]
  ),
  axis=1,
)

fig, ax = plt.subplots(figsize=(12, 8), dpi=100)
colors = [
  "seagreen" if slope >= 0 else "indianred"
  for slope in slopes_df["AnnualPercentageSlope"]
]
ax.scatter(
  slopes_df["MeanSquaredReturnChange"],
  slopes_df["AnnualPercentageSlope"],
  color=colors,
  alpha=0.75,
)
for row in slopes_df.itertuples(index=False):
  ax.annotate(
    row.ChartLabel,
    (row.MeanSquaredReturnChange, row.AnnualPercentageSlope),
    xytext=(4, 3),
    textcoords="offset points",
    fontsize=6,
  )
ax.set_xlabel("Smoothness: mean squared change in monthly log returns (lower is smoother)")
ax.set_ylabel("Average annual price change (% of starting price)")
ax.set_xscale("log")
ax.set_yscale("log")
ax.set_title(f"Top {len(slopes_df)} tickers: annual slope vs. smoothness")
average_slope = slopes_df["AnnualPercentageSlope"].mean()
average_smoothness = slopes_df["MeanSquaredReturnChange"].mean()
ax.text(
  0.02,
  0.98,
  f"Average slope: {average_slope:.0f}% per year\n"
  f"Average smoothness: {average_smoothness:.4f}",
  transform=ax.transAxes,
  va="top",
  bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
)
ax.grid(linestyle="--", alpha=0.4)
fig.tight_layout(rect=[0, 0, 0.78, 1])
table_ax = fig.add_axes([0.81, 0.04, 0.17, 0.92])
table_ax.axis("off")
table_ax.set_title("Top 20 by slope", pad=4)
top_table = table_ax.table(
  cellText=[
    [row.Ticker, f"{row.AnnualPercentageSlope:.2f}%"]
    for row in slopes_df.head(20).itertuples(index=False)
  ],
  colLabels=["Ticker", "Slope (%/year)"],
  cellLoc="center",
  loc="upper center",
)
top_table.scale(1, 0.9)
plt.show()

# Next Steps: add P/E ratio with color green is low, red is high: https://datahub.io/core/s-and-p-500-companies-financials > contituents-financial (My Downloads)