# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col, lag
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("DownsideRiskTest1").getOrCreate()

# Initialize Spark session

# Calculate Downside Potential (MAR=0.01/252) in Pandas

MAR = 0.01 / 252

def downside_potential(returns, mar):

    downside = np.where(returns < mar, returns - mar, 0)
    return np.sqrt(np.mean(downside ** 2, axis=0))

# Convert pandas DataFrames to Spark DataFrames

# Calculate returns in Spark (discrete method)

    returns_from_r = None

    error_row = {'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

# Set variables from macro or environment

    DownsideRisk = spark.createDataFrame([error_row])

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r = spark.createDataFrame([error_row])

# Define a fuzz function (tolerance for difference)

fuzz_tolerance = 1e-6

# Count number of differences

keep = False if 'keep' not in locals() else keep

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST DOWNSIDE_RISK_TEST1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST DOWNSIDE_RISK_TEST1')

# If keep is False, drop intermediate tables (handled by Python's garbage collection)

dir_path = dir if 'dir' in locals() else os.getenv('dir', '.')

# Calculate discrete returns (Pandas)

# Read prices CSV as DataFrame (Pandas)

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

downside_potential_vals = downside_potential(returns_pd.values, MAR)

downside_risk_pd = pd.DataFrame([downside_potential_vals], columns=returns_pd.columns)

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

DownsideRisk = spark.createDataFrame(downside_risk_pd)

# Read prices into Spark DataFrame for further processing

prices = spark.read.csv(prices_path, header=True, inferSchema=True)

windowSpec = Window.orderBy('date')
for col_name in prices.columns:
    if col_name != 'date':

        prices = prices.withColumn(
            f'{col_name}_return',
            (col(col_name) - lag(col(col_name), 1).over(windowSpec)) / lag(col(col_name), 1).over(windowSpec)
        )

# Check if DownsideRisk and returns_from_r have 0 records, drop if so
if DownsideRisk.count() == 0:

    DownsideRisk = None
if returns_from_r.count() == 0:

# If DownsideRisk does not exist, create error row
if DownsideRisk is None:

# If returns_from_r does not exist, create error row
if returns_from_r is None:

# Compare returns_from_r and DownsideRisk for differences

diff = returns_from_r.join(
    DownsideRisk, on='date', how='inner', suffixes=('_r', '_d')
).withColumn(
    'IBM_diff', abs(col('IBM_r') - col('IBM_d'))
).withColumn(
    'GE_diff', abs(col('GE_r') - col('GE_d'))
).withColumn(
    'DOW_diff', abs(col('DOW_r') - col('DOW_d'))
).withColumn(
    'GOOGL_diff', abs(col('GOOGL_r') - col('GOOGL_d'))
).withColumn(
    'SPY_diff', abs(col('SPY_r') - col('SPY_d'))
)

diff_filtered = diff.filter(
    (col('IBM_diff') > fuzz_tolerance) |
    (col('GE_diff') > fuzz_tolerance) |
    (col('DOW_diff') > fuzz_tolerance) |
    (col('GOOGL_diff') > fuzz_tolerance) |
    (col('SPY_diff') > fuzz_tolerance)
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:
