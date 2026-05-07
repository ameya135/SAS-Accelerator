# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, row_number
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# ---------------------------
# Initialize Spark session
# ---------------------------

prices = spark.read.csv(os.path.join(dir, 'prices.csv'), header=True, inferSchema=True)

# ---------------------------
# Read prices.csv as Spark DataFrame
# ---------------------------

# ---------------------------
# Calculate discrete returns in Spark
# ---------------------------

window_spec = Window.orderBy('date')
for col_name in prices.columns:
    if col_name != 'date':

        prices = prices.withColumn(
            f'{col_name}_return',
            (col(col_name) - lag(col(col_name), 1).over(window_spec)) / lag(col(col_name), 1).over(window_spec)
        )

# Remove first row with null returns

first_date = prices.select('date').orderBy('date').first()['date']

agg_returns = prices.filter(col('date') != first_date)

# ---------------------------
# Handle empty DataFrames
# ---------------------------
if agg_returns.count() == 0:

    returns_from_r = None

# If agg_returns does not exist, create error-indicating DataFrame
if agg_returns is None:

    agg_returns = spark.createDataFrame([{
        'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999
    }])

    returns_from_r = spark.createDataFrame([{
        'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999
    }])

# ---------------------------
# Remove first row from agg_returns
# ---------------------------

window_rownum = Window.orderBy('date')

agg_returns = agg_returns.withColumn('row_num', row_number().over(window_rownum)).filter(col('row_num') > 1).drop('row_num')

# ---------------------------
# Macro variable equivalents (should be set externally or passed as arguments)
# Example usage:
# dir = '/path/to/dir'
# keep = False
# ---------------------------
# dir, keep = ...

def fuzz(col1, col2, tol=1e-6):
    return pyspark_abs(col1 - col2) < tol

# Join on all return columns

join_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# Compute fuzzy differences for each column
for c in join_cols:

    diff = diff.withColumn(f'{c}_diff', fuzz(col(f'r.{c}'), col(f'a.{c}')))

# Filter rows where any difference is above tolerance

# ---------------------------
# Count number of differences and set pass/notes
# ---------------------------

# ---------------------------
# Read prices.csv as pandas DataFrame for return calculations
# ---------------------------

    pass_ = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ACCUMULATE_TEST1')
else:

    pass_ = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ACCUMULATE_TEST1')

# ---------------------------
# Clean up temporary tables if keep is False
# ---------------------------
if not keep:
    for df_name in ['diff', 'prices', 'agg_returns', 'returns_from_r']:
        try:
            spark.catalog.dropTempView(df_name)
        except Exception:
            pass

prices_pd = pd.read_csv(os.path.join(dir, 'prices.csv'))
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

# Calculate discrete returns and cumulative returns (geometric) using pandas

returns_pd = prices_pd.pct_change().dropna()

returns_cum_pd = (1 + returns_pd).cumprod().reset_index()
returns_cum_pd.columns = ['date'] + list(returns_cum_pd.columns[1:])

returns_from_r = spark.createDataFrame(returns_cum_pd)

    agg_returns = None
if returns_from_r.count() == 0:

# If returns_from_r does not exist, create error-indicating DataFrame
if returns_from_r is None:

# ---------------------------
# Compare returns_from_r and agg_returns (excluding date column)
# ---------------------------

diff = returns_from_r.alias('r').join(agg_returns.alias('a'), on=join_cols, how='outer')

diff_filtered = diff.filter(~(
    col('IBM_diff') & col('GE_diff') & col('DOW_diff') & col('GOOGL_diff') & col('SPY_diff')
))

n = diff_filtered.count()

if n == 0:

# Convert pandas DataFrame to Spark DataFrame
