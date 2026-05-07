# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as ps_abs, col, lit
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

spark = SparkSession.builder.appName("ActivePremium_test3").getOrCreate()

# Initialize Spark session

active_premium_pd = active_premium_pd[['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]

# Convert pandas DataFrames to Spark DataFrames

    schema_ap = StructType([
        StructField('date', IntegerType(), True),
        StructField('IBM', DoubleType(), True),
        StructField('GE', DoubleType(), True),
        StructField('DOW', DoubleType(), True),
        StructField('GOOGL', DoubleType(), True),
        StructField('SPY', DoubleType(), True)
    ])

    schema_rr = StructType([
        StructField('date', IntegerType(), True),
        StructField('IBM', DoubleType(), True),
        StructField('GE', DoubleType(), True),
        StructField('DOW', DoubleType(), True),
        StructField('GOOGL', DoubleType(), True),
        StructField('SPY', DoubleType(), True)
    ])

    returns_from_r = spark.createDataFrame([(1, 999.0, 999.0, 999.0, 999.0, 999.0)], schema=schema_rr)

diff = diff.withColumn('_type_', lit('DIF')) \
    .withColumn('IBM_DIF', ps_abs(col('r.IBM') - col('a.IBM'))) \
    .withColumn('GE_DIF', ps_abs(col('r.GE') - col('a.GE'))) \
    .withColumn('DOW_DIF', ps_abs(col('r.DOW') - col('a.DOW'))) \
    .withColumn('GOOGL_DIF', ps_abs(col('r.GOOGL') - col('a.GOOGL')))

# Filter for differences above threshold

# Set variables from macro or environment

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST ActivePremium_test3')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST ActivePremium_test3')

    returns_from_r = None

    active_premium = None

keep = False  # Set from macro or parameter

# Clean up DataFrames if keep is False (optional, handled by Python GC)
if not keep:

    diff = None

data_dir = os.environ.get('dir', '/tmp')  # Set from macro or parameter

# Read prices.csv as pandas DataFrame

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

assets = returns_pd.iloc[:, 0:4]

benchmark = returns_pd.iloc[:, 4]

# ActivePremium calculation: (mean(asset) - mean(benchmark)) * scale
# Assume first 4 columns are assets, 5th is benchmark, scale=4

active_premium_pd = (assets.mean() - benchmark.mean()) * 4

active_premium_pd = active_premium_pd.to_frame().T
active_premium_pd['date'] = returns_pd.index[-1]
active_premium_pd['SPY'] = benchmark.mean() * 4

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

active_premium = spark.createDataFrame(active_premium_pd)

# Handle empty DataFrames by creating error DataFrames as in SAS
if active_premium.count() == 0:

    active_premium = spark.createDataFrame([(-1, -999.0, -999.0, -999.0, -999.0, -999.0)], schema=schema_ap)
if returns_from_r.count() == 0:

diff = returns_from_r.alias('r').join(
    active_premium.alias('a'),
    on='date',
    how='outer'
)

# Compare returns_from_r and active_premium DataFrames
# Join on 'date' and compare columns

diff_filtered = diff.filter(
    (ps_abs(col('IBM_DIF')) > 1e-5) |
    (ps_abs(col('GE_DIF')) > 1e-5) |
    (ps_abs(col('DOW_DIF')) > 1e-5) |
    (ps_abs(col('GOOGL_DIF')) > 1e-5)
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:

# Calculate log returns using pandas
