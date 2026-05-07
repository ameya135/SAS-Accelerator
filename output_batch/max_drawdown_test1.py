# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

def max_drawdown(series):

    cumulative = (1 + series).cumprod()

    highwater = cumulative.cummax()

    drawdown = cumulative / highwater - 1
    return drawdown.min()

max_dd_pd = pd.DataFrame([max_dd_dict])

# Convert pandas DataFrames to Spark DataFrames

max_dd = spark.createDataFrame(max_dd_pd)

# Handle empty DataFrames by replacing with error rows
if max_dd.count() == 0:

    error_row = {'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    max_dd = spark.createDataFrame([error_row])

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r = spark.createDataFrame([error_row])

# Compare DataFrames by date and columns, output differences where fuzziness applies

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST MAX_DRAWDOWN_TEST1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST MAX_DRAWDOWN_TEST1')

# Clean up temporary tables if keep is False
if not keep:

    diff = None

    max_dd = None

    returns_from_r = None

# Read prices CSV as DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

# Calculate discrete returns using pandas

returns_pd = prices_pd.pct_change().dropna()

max_dd_dict = {col: max_drawdown(returns_pd[col]) for col in returns_pd.columns}

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

if returns_from_r.count() == 0:

joined = returns_from_r.alias('base').join(max_dd.alias('compare'), how='inner')

diff = joined.filter(
    (pyspark_abs(col('base.IBM') - col('compare.IBM')) > 1e-8) |
    (pyspark_abs(col('base.GE') - col('compare.GE')) > 1e-8) |
    (pyspark_abs(col('base.DOW') - col('compare.DOW')) > 1e-8) |
    (pyspark_abs(col('base.GOOGL') - col('compare.GOOGL')) > 1e-8) |
    (pyspark_abs(col('base.SPY') - col('compare.SPY')) > 1e-8)
)

n = diff.count()

# Set up variables from dependencies (assume these are provided elsewhere)
# n, dir, nv, keep are assumed to be set in the environment or passed in

# Set pass/fail and notes based on differences
if n == 0:

# Calculate max drawdown for each column
