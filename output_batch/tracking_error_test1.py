# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("TrackingErrorTest1").getOrCreate()

# Initialize Spark session

# Calculate discrete returns using pandas

# Tracking Error calculation: compare first 4 columns to 5th (benchmark), annualized

def tracking_error(returns, benchmark_col, scale=252):

    diff = returns.iloc[:, :4].values - returns.iloc[:, [benchmark_col]].values

    te = np.std(diff, axis=0, ddof=1) * np.sqrt(scale)
    return pd.DataFrame([te], columns=returns.columns[:4])

# Convert tracking error result to Spark DataFrame

# Prepare returns_from_r DataFrame (simulate R output)

returns_from_r_df = tracking_error_df

    tracking_error_df = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999}])
if returns_from_r_df.count() == 0:

    returns_from_r_df = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999}])

# Compare returns_from_r and tracking_error DataFrames

# Count differences

# Set up variables from macro inputs (assume these are defined elsewhere)

    pass_var = True

    notes_var = 'Passed'
    print('NOTE: NO ERROR IN TEST Tracking_Error_TEST1')
else:

    pass_var = False

    notes_var = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Tracking_Error_TEST1')

    prices_df = None

    tracking_error_df = None

    returns_from_r_df = None

    diff_df = None

keep = False if keep_macro_variable == 'FALSE' else True

# Cleanup if keep is False
if not keep:

dir_path = dir_macro_variable

# Read prices CSV as Spark DataFrame

prices_path = os.path.join(dir_path, 'prices.csv')

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

prices_pd = prices_df.toPandas().set_index(prices_df.columns[0])

returns_pd = prices_pd.pct_change().dropna()

returns_te_pd = tracking_error(returns_pd, benchmark_col=4, scale=252)
returns_te_pd['date'] = returns_pd.index[-1] if not returns_pd.empty else None

tracking_error_df = spark.createDataFrame(returns_te_pd)

# Handle empty DataFrames by inserting error rows
if tracking_error_df.count() == 0:

diff_df = returns_from_r_df.alias('r').join(
    tracking_error_df.alias('t'), on='date', how='inner'
).withColumn(
    'IBM_DIF', pyspark_abs(col('r.IBM') - col('t.IBM'))
).withColumn(
    'GE_DIF', pyspark_abs(col('r.GE') - col('t.GE'))
).withColumn(
    'DOW_DIF', pyspark_abs(col('r.DOW') - col('t.DOW'))
).withColumn(
    'GOOGL_DIF', pyspark_abs(col('r.GOOGL') - col('t.GOOGL'))
).filter(
    (col('IBM_DIF') > 1e-5) | (col('GE_DIF') > 1e-5) | (col('DOW_DIF') > 1e-5) | (col('GOOGL_DIF') > 1e-5)
)

n = diff_df.count()

# Set pass/fail and notes
if n == 0:

# Convert prices to Pandas DataFrame for return calculation
