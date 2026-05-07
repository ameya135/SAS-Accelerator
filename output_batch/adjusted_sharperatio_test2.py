# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.functions import col, lag, lit, month, row_number, year, when
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# --- Initialize Spark session ---

rf = 0.01 / 12

# --- Set date column name ---

    prices = prices.withColumn(
        f'{col_name}_monthly_cum',
        F.expr(f'aggregate(collect_list({col_name}_ret) over (partition by year, month order by {date_column} rows between unbounded preceding and current row), 1D, (acc, x) -> acc * (1 + x)) - 1')
    )

# --- Set first row of each numeric column to null ---
for col_name in num_cols:

# --- Adjusted Sharpe Ratio calculation (Pandas) ---

# --- Define file path for prices CSV ---
# Assumes 'dir' variable is defined elsewhere in your environment

prices_csv_path = os.path.join(dir, 'prices.csv')

# --- Pandas: Read prices and calculate monthly cumulative returns ---

prices_pd = pd.read_csv(prices_csv_path, parse_dates=True, index_col=0)

returns_pd = prices_pd.pct_change().dropna()

monthly_returns_pd = returns_pd.resample('M').apply(lambda x: (1 + x).prod() - 1)

excess_returns = monthly_returns_pd * 100 - rf * 100

mean_return = excess_returns.mean()

std_return = excess_returns.std()

skewness = excess_returns.skew()

kurtosis = excess_returns.kurtosis()

adj_sharpe = mean_return / std_return * (
    1 + (skewness / 6) * (mean_return / std_return) - ((kurtosis - 3) / 24) * (mean_return / std_return) ** 2
)

# --- Prepare returns DataFrame for Spark ---

returns_pd_out = monthly_returns_pd.copy()
returns_pd_out['date'] = monthly_returns_pd.index
returns_pd_out.reset_index(drop=True, inplace=True)

returns = spark.createDataFrame(returns_pd_out)

# --- Read prices into Spark DataFrame ---

prices = spark.read.csv(prices_csv_path, header=True, inferSchema=True)

date_column = prices.columns[0]  # Assumes first column is date

# --- Calculate discrete returns in Spark ---

num_cols = [c for c in prices.columns if c != date_column]

window_spec = Window.orderBy(date_column)
for col_name in num_cols:

    prices = prices.withColumn(
        f'{col_name}_ret',
        (col(col_name) - lag(col(col_name), 1).over(window_spec)) / lag(col(col_name), 1).over(window_spec)
    )

# --- Calculate monthly cumulative returns in Spark ---

prices = prices.withColumn('year', year(col(date_column))).withColumn('month', month(col(date_column)))

window_month = Window.partitionBy('year', 'month').orderBy(date_column).rowsBetween(Window.unboundedPreceding, Window.currentRow)
for col_name in num_cols:

    prices = prices.withColumn(
        col_name,
        when(row_number().over(window_spec) == 1, None).otherwise(col(col_name))
    )
