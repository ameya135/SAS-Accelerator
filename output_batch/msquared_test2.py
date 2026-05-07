# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F, types as T, Window

spark = SparkSession.builder.appName("MSquared_test2").getOrCreate()

# Initialize Spark session

        Rf_adj = (1 + Rf) ** scale - 1
    else:

        Rf_adj = Rf * scale

# Convert pandas DataFrames to Spark DataFrames

# Calculate discrete returns in Spark
for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    prices_spark = prices_spark.withColumn(
        f'{col}_ret',
        (F.col(col) - F.lag(col).over(Window.orderBy('date'))) / F.lag(col).over(Window.orderBy('date'))
    )

prices_spark = prices_spark.dropna()

# Set directory and file path
# dir should be defined externally or set here
# dir = '/path/to/data'  # Uncomment and set if needed

# Collect to pandas and apply tM2

Ra_msq = msquared_pd[['IBM_ret', 'GE_ret', 'DOW_ret', 'GOOGL_ret']]

Rb_msq = msquared_pd['SPY_ret']

msquared_result = tM2(Ra_msq, Rb_msq, Rf=0.01, scale=1, geometric=True)

MSquared_pd = pd.DataFrame(msquared_result).T
MSquared_pd.columns = ['IBM', 'GE', 'DOW', 'GOOGL']
MSquared_pd['SPY'] = Rb_msq.std() * np.sqrt(1)
MSquared_pd['date'] = msquared_pd['date'].iloc[-1]

MSquared = spark.createDataFrame(MSquared_pd)

# Prepare DataFrame for MSquared calculation

    returns_from_r = None

prices_path = os.path.join(dir, 'prices.csv')

# If MSquared does not exist, create error row
if MSquared is None:

    MSquared_pd = pd.DataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])

    MSquared = spark.createDataFrame(MSquared_pd)

    returns_from_r_pd = pd.DataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames and output differences

def fuzz(x, y):
    return abs(x - y) > 1e-8

diff = diff.withColumn('IBM_diff', F.when(F.abs(F.col('IBM_r') - F.col('IBM_m')) > 1e-8, 1).otherwise(0)) \
           .withColumn('GE_diff', F.when(F.abs(F.col('GE_r') - F.col('GE_m')) > 1e-8, 1).otherwise(0)) \
           .withColumn('DOW_diff', F.when(F.abs(F.col('DOW_r') - F.col('DOW_m')) > 1e-8, 1).otherwise(0)) \
           .withColumn('GOOGL_diff', F.when(F.abs(F.col('GOOGL_r') - F.col('GOOGL_m')) > 1e-8, 1).otherwise(0))

# Read prices.csv as pandas DataFrame

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST MSQUARED_TEST2')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST MSQUARED_TEST2')

    keep = False

# Clean up temporary tables if keep is False
if not 'keep' in locals():

if not keep:
    for df_name in ['diff', 'prices_spark', 'returns_from_r', 'MSquared']:
        try:
            eval(df_name).unpersist()
        except Exception:
            pass

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

prices_spark = spark.createDataFrame(prices_pd.reset_index())

msquared = prices_spark.select(
    [F.col('date')] + [F.col(f'{col}_ret') for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]
)

msquared_pd = msquared.toPandas()

# Calculate discrete returns (drop NA)

returns_pd = prices_pd.pct_change().dropna()

Ra = returns_pd.iloc[:, 0:4]

        SR = (Ra.mean() - Rf) / Ra.std() * np.sqrt(scale)
    else:

        SR = (Ra.mean() - Rf) / Ra.std() * scale

# Apply tM2 to first 4 columns as Ra, 5th as Rb

Rb = returns_pd.iloc[:, 4]

def tM2(Ra, Rb, Rf=0, scale=1, geometric=True):
    if geometric:

    sb = Rb.std() * np.sqrt(scale) if geometric else Rb.std() * scale
    if geometric:

    result = SR * sb + Rf_adj
    return result

tM2_result = tM2(Ra, Rb, Rf=0.01, scale=1, geometric=True)

returns_from_r_pd = pd.DataFrame(tM2_result).T
returns_from_r_pd.columns = Ra.columns

returns_from_r = spark.createDataFrame(returns_from_r_pd.reset_index(drop=True))

# Check if MSquared and returns_from_r have 0 records, drop if so
if MSquared.count() == 0:
    MSquared.unpersist()

    MSquared = None
if returns_from_r.count() == 0:
    returns_from_r.unpersist()

# If returns_from_r does not exist, create error row
if returns_from_r is None:

    returns_from_r = spark.createDataFrame(returns_from_r_pd)

diff = returns_from_r.join(MSquared, on='date', how='inner', suffixes=('_r', '_m'))

diff_filtered = diff.filter(
    (F.col('IBM_diff') == 1) | (F.col('GE_diff') == 1) | (F.col('DOW_diff') == 1) | (F.col('GOOGL_diff') == 1)
)

n = diff_filtered.count()

if n == 0:

# Define tM2 function
