# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F, types as T, Window

spark = SparkSession.builder.appName("MSquared_test4").getOrCreate()

# Initialize Spark session

# Calculate log returns, drop NA

# Define tM2 function in Python

        Rf_adj = (1 + Rf) ** scale - 1
    else:

        Rf_adj = Rf * scale

# Apply tM2 to first 4 columns vs 5th column (BM=SPY), Rf=0.01/12, scale=12, geometric=False

# Calculate log returns in Spark for each ticker

# Define input directory and macro variables

tickers = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

window_spec = Window.orderBy('date')
for col in tickers:

    prices_df = prices_df.withColumn(f'{col}_ret', F.log(F.col(col) / F.lag(col).over(window_spec)))

# Drop first row with null returns

prices_df = prices_df.na.drop(subset=[f'{col}_ret' for col in tickers])

def msquared_udf(ibm, ge, dow, googl, spy):

    Ra = np.array([ibm, ge, dow, googl])

    Rb = spy

input_dir = os.environ.get('dir', '/path/to/dir')

msquared_schema = T.DoubleType()

msquared_udf_spark = F.udf(msquared_udf, msquared_schema)

prices_df = prices_df.withColumn(
    'MSquared',
    msquared_udf_spark(
        F.col('IBM_ret'),
        F.col('GE_ret'),
        F.col('DOW_ret'),
        F.col('GOOGL_ret'),
        F.col('SPY_ret')
    )
)

keep = os.environ.get('keep', 'FALSE')

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames and output differences

        MSquared = MSquared.withColumn(col, F.lit(None))

diff = diff.withColumn(
    '_type_',
    F.when(
        (F.col('IBM') != F.col('IBM')) |
        (F.col('GE') != F.col('GE')) |
        (F.col('DOW') != F.col('DOW')) |
        (F.col('GOOGL') != F.col('GOOGL')),
        'DIF'
    ).otherwise('')
)

diff = diff.filter(diff._type_ == 'DIF')

# Read prices CSV as Spark DataFrame

    pass_flag = True

    notes = 'Passed'
else:

    pass_flag = False

    notes = 'Differences detected in outputs.'

prices_path = os.path.join(input_dir, 'prices.csv')

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

prices_pd = prices_df.toPandas().set_index('date')

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

Ra = returns_pd.iloc[:, 0:4]

        SR = (Ra.mean() - Rf) / Ra.std() * np.sqrt(scale)

        SR = (Ra.mean() - Rf) / Ra.std() * scale

Rb = returns_pd.iloc[:, 4]

def tM2(Ra, Rb, Rf=0, scale=12, geometric=True):
    if geometric:

        sb = Rb.std() * np.sqrt(scale)

        sb = Rb.std() * scale

    result = SR * sb + Rf_adj
    return result

tM2_result = tM2(Ra, Rb, Rf=0.01/12, scale=12, geometric=False)

returns_from_r_pd = pd.DataFrame(tM2_result).T
returns_from_r_pd.columns = Ra.columns

returns_from_r = spark.createDataFrame(returns_from_r_pd)

# Convert returns_from_r to Spark DataFrame

    SR = (Ra.mean() - 0.01/12) / Ra.std() * 12

    sb = np.std(Rb) * 12

    Rf_adj = 0.01
    return float(SR * sb + Rf_adj)

MSquared = prices_df.select('date', 'IBM_ret', 'GE_ret', 'DOW_ret', 'GOOGL_ret', 'SPY_ret', 'MSquared')

# MSquared calculation in Spark (BM=SPY, Rf=0.01/12, scale=12, method=LOG)

# Select relevant columns for MSquared DataFrame

# Check if MSquared and returns_from_r have records

nv_MSquared = MSquared.count()

nv_returns_from_r = returns_from_r.count()

# If tables have 0 records, create error DataFrames
if nv_MSquared == 0:

    MSquared = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if nv_returns_from_r == 0:

join_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']
# Ensure columns exist in both DataFrames for join
for col in join_cols:
    if col not in returns_from_r.columns:

        returns_from_r = returns_from_r.withColumn(col, F.lit(None))
    if col not in MSquared.columns:

diff = returns_from_r.join(MSquared, on=join_cols, how='outer')

n = diff.count()

# Set pass/fail flags
if n == 0:

# If keep==FALSE, clean up temporary DataFrames
if keep == 'FALSE':
    MSquared.unpersist()
    returns_from_r.unpersist()
    diff.unpersist()
    prices_df.unpersist()

# Convert prices to Pandas DataFrame for return calculations
