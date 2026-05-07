# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from functools import reduce
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("Sterling_Ratio_Test1").getOrCreate()

# Initialize Spark session

# Define Sterling Ratio calculation (scale=4 as in SAS/R)

def sterling_ratio(returns_series, scale=4):

    downside = returns_series[returns_series < 0].fillna(0)

    downside_deviation = np.sqrt((downside ** 2).mean()) * np.sqrt(scale)

    avg_return = returns_series.mean() * scale

    sr = avg_return / downside_deviation if downside_deviation != 0 else np.nan
    return sr

# Calculate Sterling Ratio for each column except 'date'

    error_data = {'date': [-1], 'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    SterlingRatio = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'date': [1], 'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_from_r = spark.createDataFrame(pd.DataFrame(error_data))

join_cols = ['date']

compare_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# Filter rows where any difference exists

diff = diff.withColumn('any_diff', reduce(lambda a, b: a | b, [col(f'diff_{c}') for c in compare_cols]))

diff = diff.filter(col('any_diff'))

# Count number of differences

# Read prices CSV as Spark DataFrame

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST STERLING_RATIO_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST STERLING_RATIO_TEST1')

# Optionally drop intermediate tables if keep is False
if not keep:

    prices_df = None

    SterlingRatio = None

    returns_from_r = None

prices_path = os.path.join(dir, 'prices.csv')

    diff = None

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Convert prices_df to Pandas for return calculation

prices_pd = prices_df.toPandas()

returns_pd = prices_pd.set_index('date').pct_change().dropna().reset_index()

sterling_ratios = {}
for col_name in returns_pd.columns:
    if col_name != 'date':
        sterling_ratios[col_name] = sterling_ratio(returns_pd[col_name])

sterling_ratio_data = {'date': [returns_pd['date'].iloc[-1]]}
for k, v in sterling_ratios.items():
    sterling_ratio_data[k] = [v]

SterlingRatio_pd = pd.DataFrame(sterling_ratio_data)

SterlingRatio = spark.createDataFrame(SterlingRatio_pd)

# Prepare SterlingRatio DataFrame

returns_from_r_pd = returns_pd.copy()

returns_from_r = spark.createDataFrame(returns_from_r_pd)

# Prepare returns_from_r DataFrame

# Handle empty DataFrames by creating error rows if needed
if SterlingRatio.count() == 0:

if returns_from_r.count() == 0:

# Compare returns_from_r and SterlingRatio by date and columns, output differences

diff = returns_from_r.alias('r').join(SterlingRatio.alias('s'), on=join_cols, how='inner') \
    .select([col('r.date')] + [
        (pyspark_abs(col(f'r.{c}') - col(f's.{c}')) > 1e-8).alias(f'diff_{c}') for c in compare_cols
    ])

n = diff.count()

# Set variables from dependencies (assume these are provided in the environment)
# n, dir, nv, keep are assumed to be set externally

# Set pass/notes variables based on comparison
if n == 0:

# Calculate discrete returns using pandas
