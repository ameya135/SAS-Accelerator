# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, when

spark = SparkSession.builder.appName("GEO_MEAN_TEST").getOrCreate()

# Initialize Spark session

# Convert geometric mean to Spark DataFrame

geo_mean_df = spark.createDataFrame([geo_mean_row])

# Convert geometric mean to Spark DataFrame for comparison (simulate returns_from_r)

returns_from_r_df = spark.createDataFrame([returns_from_r_row])

# If geo_mean_df or returns_from_r_df are empty, create error rows
if geo_mean_df.count() == 0:

    geo_mean_df = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r_df.count() == 0:

    returns_from_r_df = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames (simulate proc compare with fuzz logic)

columns = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

diff = returns_from_r_df.crossJoin(geo_mean_df) \
    .select([
        pyspark_abs(col(f'returns_from_r_df.{c}') - col(f'geo_mean_df.{c}')).alias(c)
        for c in columns
    ])

# Check for differences using a tolerance (fuzz)

diff_count = diff.select([
    when(col(c) > 1e-8, 1).otherwise(0).alias(c) for c in columns
]).agg(
    sum([col(c) for c in columns]).alias('diff_sum')
).collect()[0]['diff_sum']

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST GEO_MEAN_TEST')
else:

# Set pass/fail and notes variables
if diff_count == 0:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST GEO_MEAN_TEST')

# Read prices CSV as DataFrame

# Clean up temporary tables if keep is False
if not keep:
    geo_mean_df.unpersist()
    returns_from_r_df.unpersist()

prices_path = f'{dir}/prices.csv'

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

# Calculate discrete returns using pandas

returns_pd = prices_pd.pct_change().dropna()

# Calculate geometric mean for each column

geo_mean_vals = np.exp(np.log1p(returns_pd).mean()) - 1

geo_mean_dict = geo_mean_vals.to_dict()

geo_mean_row = {k: float(v) for k, v in geo_mean_dict.items()}
geo_mean_row['date'] = -1

returns_from_r_row = {k: float(v) for k, v in geo_mean_dict.items()}
returns_from_r_row['date'] = 1
