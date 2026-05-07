# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, lit, log, stddev_samp
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("StandardDeviationTest1").getOrCreate()

# Initialize Spark session

window_spec = Window.orderBy('date')

tickers = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    returns = returns.withColumn(f'{ticker}_lag', lag(col(ticker)).over(window_spec))

    returns = returns.withColumn(f'{ticker}_ret', log(col(ticker) / col(f'{ticker}_lag')))

# Select only return columns and date, drop rows with nulls

return_cols = ['date'] + [f'{ticker}_ret' for ticker in tickers]

# Calculate annualized standard deviation (assuming 252 trading days)

annualized_stddev = annualized_stddev.withColumn('date', lit(-1))

annualized_stddev = annualized_stddev.select('date', *tickers)

    returns_from_r = spark.createDataFrame(
        [{'date': 1, 'IBM_ret': 999, 'GE_ret': 999, 'DOW_ret': 999, 'GOOGL_ret': 999, 'SPY_ret': 999}]
    )

    returns_from_r_last = returns_from_r_last.withColumnRenamed(f'{ticker}_ret', ticker)

# Fuzzy comparison function

# Set variables from dependencies (simulate macro variables)

def fuzz(col1, col2, tol=1e-6):
    return pyspark_abs(col1 - col2) < tol

# Join and compare the two DataFrames

    diff = diff.withColumn(f'{ticker}_diff', ~fuzz(col(ticker), col(ticker)))

diff = diff.filter(
    col('IBM_diff') | col('GE_diff') | col('DOW_diff') | col('GOOGL_diff') | col('SPY_diff')
)

# Count differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Standard_Deviation_test1')
else:

dir_path = os.environ.get('DIR', '/path/to/dir')

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Standard_Deviation_test1')

keep = os.environ.get('KEEP', 'FALSE').upper() == 'TRUE'

# Cleanup if keep is False (no explicit deletion needed in PySpark)

# Load prices data

prices_path = os.path.join(dir_path, 'prices.csv')

prices = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Calculate log returns for each ticker

returns = prices
for ticker in tickers:

returns_from_r = returns.select(*return_cols).na.drop()

annualized_stddev = returns_from_r.agg(
    *[(stddev_samp(col(f'{ticker}_ret')) * (252 ** 0.5)).alias(ticker) for ticker in tickers]
)

# Handle empty DataFrames by inserting default rows
if annualized_stddev.count() == 0:

    annualized_stddev = spark.createDataFrame(
        [{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}]
    )
if returns_from_r.count() == 0:

# Reduce annualized_stddev and returns_from_r to last row

annualized_stddev_last = annualized_stddev.orderBy('date', ascending=False).limit(1)

returns_from_r_last = returns_from_r.orderBy('date', ascending=False).limit(1)
for ticker in tickers:

diff = returns_from_r_last.join(annualized_stddev_last, on='date', how='inner')
for ticker in tickers:

n = diff.count()

# Set pass/fail and notes
if n == 0:
