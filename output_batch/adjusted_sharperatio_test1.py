# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col, row_number
from pyspark.sql.window import Window

spark = SparkSession.builder.appName('AdjustedSharpeRatioTest').getOrCreate()

# Initialize Spark session

def adjusted_sharpe_ratio(returns, rf=0.01/252, scale=252):

    mean_ret = returns.mean() * scale

    std_ret = returns.std(ddof=0) * np.sqrt(scale)

    sharpe = (mean_ret - rf * scale) / std_ret

    skew = returns.skew()

    kurt = returns.kurtosis()

    adj_sharpe = sharpe * (1 + (skew/6)*sharpe - ((kurt-3)/24)*sharpe**2)
    return adj_sharpe

# Compute Adjusted Sharpe Ratio for each column

# Convert pandas DataFrames to Spark DataFrames

    error_data = [(-1, -999, -999, -999, -999, -999)]

# Macro variable equivalents (should be set externally or passed as function args)
# Example assignments (replace with actual values as needed):
# dir = '/path/to/dir'
# keep = False

    columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    error_data = [(1, 999, 999, 999, 999, 999)]

    columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    returns_from_r = spark.createDataFrame(error_data, columns)

# Keep only the last row in adjusted_SharpeRatio

window_spec = Window.orderBy(col('date').desc())

adjusted_SharpeRatio = adjusted_SharpeRatio.withColumn('rn', row_number().over(window_spec)).filter(col('rn') == 1).drop('rn')

compare_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# Read prices.csv as pandas DataFrame

    diff = diff.withColumn(f'diff_{c}', spark_abs(col(f'r.{c}') - col(f'a.{c}')))

# Filter where any difference is above tolerance

tolerance = 1e-6

# Count differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Adjusted_SharpeRatio_test1')
else:

prices_path = os.path.join(dir, 'prices.csv')

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Adjusted_SharpeRatio_test1')

# If keep is False, drop intermediate DataFrames
if not keep:

    adjusted_SharpeRatio = None

    returns_from_r = None

    diff_filtered = None

prices_pdf = pd.read_csv(prices_path, parse_dates=['date'])
prices_pdf.set_index('date', inplace=True)

# Calculate discrete returns using pandas

returns_pdf = prices_pdf.pct_change().dropna()

adj_sharpe_dict = {col_name: adjusted_sharpe_ratio(returns_pdf[col_name]) for col_name in returns_pdf.columns}

adj_sharpe_df = pd.DataFrame([adj_sharpe_dict])
adj_sharpe_df['date'] = returns_pdf.index.max()

adj_sharpe_df = adj_sharpe_df[['date'] + list(adj_sharpe_dict.keys())]

returns_from_r_df = returns_pdf.copy() * 100
returns_from_r_df['date'] = returns_from_r_df.index

returns_from_r_df = returns_from_r_df[['date'] + list(returns_pdf.columns)]

adjusted_SharpeRatio = spark.createDataFrame(adj_sharpe_df)

# Prepare adjusted_SharpeRatio DataFrame

returns_from_r = spark.createDataFrame(returns_from_r_df)

# Prepare returns_from_r DataFrame (mimicking R output structure)

# Handle empty DataFrames by creating error DataFrames as in SAS
if adjusted_SharpeRatio.count() == 0:

    adjusted_SharpeRatio = spark.createDataFrame(error_data, columns)
if returns_from_r.count() == 0:

# Compare returns_from_r and adjusted_SharpeRatio (fuzzy match on columns)

diff = returns_from_r.alias('r').join(adjusted_SharpeRatio.alias('a'), on='date', how='inner')
for c in compare_cols:

diff_filtered = diff.filter(
    ' or '.join([f'diff_{c} > {tolerance}' for c in compare_cols])
)

n_diff = diff_filtered.count()

# Set pass/notes variables
if n_diff == 0:

# Adjusted Sharpe Ratio calculation (custom implementation)
