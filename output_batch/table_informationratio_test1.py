# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as ps_abs, col
import os

spark = SparkSession.builder.appName("table_InformationRatio_test1").getOrCreate()

# Initialize Spark session

# --- Calculate Returns ---

assets = returns_pd[asset_cols]

benchmark = returns_pd[benchmark_col]

# --- Calculate Information Ratio ---
# Assume first 4 columns are assets, 5th is benchmark (SPY)

excess_returns = assets.subtract(benchmark, axis=0)

info_ratio = excess_returns.mean() / excess_returns.std(ddof=0)

info_ratio = info_ratio.round(8)

# Prepare output DataFrame

table_InformationRatio_pd = table_InformationRatio_pd.round(8)

# --- Prepare Returns DataFrame for Comparison ---

# Set up variables (replace with actual values or pass as arguments)

# --- Compare DataFrames: Absolute Differences ---

for col_name in join_cols:

    diff_sdf = diff_sdf.withColumn(f"{col_name}_DIF", ps_abs(col(col_name) - col(col_name)))

# Apply custom thresholds for filtering

keep = False  # Set to True to keep intermediate DataFrames

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_InformationRatio_TEST1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_InformationRatio_TEST1')

# --- Optional Cleanup ---
if not keep:
    # Optionally clean up intermediate DataFrames if needed
    pass

data_dir = '/path/to/data'  # Replace with actual directory path

# --- Read and Prepare Data ---
# Read prices.csv as pandas DataFrame

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
prices_pd.index = pd.to_datetime(prices_pd.iloc[:, 0])

prices_sdf = spark.createDataFrame(prices_pd.reset_index())

returns_pd = prices_pd.pct_change().dropna()

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

asset_cols = returns_pd.columns[:4]

benchmark_col = returns_pd.columns[4]

table_InformationRatio_pd = pd.DataFrame([info_ratio], columns=asset_cols)
table_InformationRatio_pd[benchmark_col] = benchmark.mean() / benchmark.std(ddof=0)

table_InformationRatio_sdf = spark.createDataFrame(table_InformationRatio_pd)

returns_from_r_sdf = returns_sdf.select(*asset_cols, benchmark_col)

# --- Handle Empty DataFrames ---
if table_InformationRatio_sdf.count() == 0:

    error_dict = {col: [-999.0] for col in list(asset_cols) + [benchmark_col]}

    table_InformationRatio_sdf = spark.createDataFrame(pd.DataFrame(error_dict))
if returns_from_r_sdf.count() == 0:

    error_dict = {col: [999.0] for col in list(asset_cols) + [benchmark_col]}

    returns_from_r_sdf = spark.createDataFrame(pd.DataFrame(error_dict))

join_cols = list(asset_cols) + [benchmark_col]

diff_sdf = returns_from_r_sdf.join(table_InformationRatio_sdf, on=join_cols, how='outer')

diff_filtered = diff_sdf.filter(
    (col('IBM_DIF') > 1e-4) |
    (col('GE_DIF') > 1e-3) |
    (col('DOW_DIF') > 1e-4) |
    (col('GOOGL_DIF') > 1e-3)
)

n = diff_filtered.count()

# --- Set Pass/Fail and Notes ---
if n == 0:

prices_pd = prices_pd.iloc[:, 1:]

# Convert prices to Spark DataFrame
