# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, lag, lit, log, monotonically_increasing_id, quarter, sum as spark_sum, year
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Convert to Spark DataFrame

# --- Spark Section: Calculate Quarterly Log Returns ---

prices = prices.withColumn('date', col('date').cast('date'))

window_spec = Window.orderBy('date')

tickers = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']
for ticker in tickers:

    prices = prices.withColumn(f'{ticker}_log_return', log(col(ticker)) - log(lag(col(ticker), 1).over(window_spec)))

# Add year and quarter columns

prices = prices.withColumn('quarter', quarter('date')).withColumn('year', year('date'))

agg_returns_all = None
for ticker in tickers:

        agg_returns_all = agg
    else:

        agg_returns_all = agg_returns_all.join(agg, ['year', 'quarter'], 'inner')

# Add a unique row id for ordering and simulate firstobs=2 by removing first row

agg_returns = agg_returns_all.withColumn('row_id', monotonically_increasing_id())

agg_returns = agg_returns.orderBy('row_id').filter(col('row_id') != 0)

# Macro variable simulation (replace with actual values or parameterize as needed)

# --- Handle Empty Tables ---
if agg_returns.count() == 0:

    returns_from_r = spark.createDataFrame([(1, 999, 999, 999, 999, 999)], ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

# --- Compare Results and Report Differences ---

def fuzz(x, y, tol=1e-8):
    return abs(x - y) < tol

agg_returns_pd = agg_returns.select(['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']).toPandas()

keep = False  # Set to True to keep intermediate tables

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ACCUMULATE_TEST4')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ACCUMULATE_TEST4')

# --- Clean up if not keeping intermediate tables ---
if not keep:
    # Variables will be cleaned up by Python's garbage collector
    pass

dir_path = dir_macro_variable  # assign actual directory path

prices = spark.read.csv(os.path.join(dir_path, 'prices.csv'), header=True, inferSchema=True)

    agg = prices.groupBy('year', 'quarter').agg(spark_sum(f'{ticker}_log_return').alias(ticker))
    if agg_returns_all is None:

# --- Pandas Section: Calculate Quarterly Log Returns (R-like) ---

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns = np.log(prices_pd / prices_pd.shift(1)).dropna()

returns_quarterly = returns.resample('Q').sum()
returns_quarterly.reset_index(inplace=True)

returns_from_r = spark.createDataFrame(returns_quarterly)

# Calculate log returns for each ticker

# Aggregate quarterly log returns for each ticker

    agg_returns = spark.createDataFrame([(-1, -999, -999, -999, -999, -999)], ['row_id', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])
if returns_from_r.count() == 0:

returns_from_r_pd = returns_from_r.select(['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']).toPandas()

diff_rows = []
for idx, row in returns_from_r_pd.iterrows():
    if idx >= len(agg_returns_pd):
        continue

    diffs = {}
    for ticker in tickers:
        if not fuzz(row[ticker], agg_returns_pd.iloc[idx][ticker]):
            diffs[ticker] = (row[ticker], agg_returns_pd.iloc[idx][ticker])
    if diffs:
        diff_rows.append({'_type_': 'DIF', **diffs})

diff = pd.DataFrame(diff_rows)

n = len(diff)

# --- Set Pass/Fail Notes ---
if n == 0:

# Calculate log returns and accumulate quarterly (non-geometric)
