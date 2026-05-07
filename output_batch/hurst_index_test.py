# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col, lit
from pyspark.sql.types import BooleanType
from pyspark.sql.functions import udf

spark = SparkSession.builder.appName("HurstIndexTest").getOrCreate()

# Initialize Spark session

# --- Read and Prepare Data ---

# Set the directory path for prices.csv

prices_path = os.path.join(os.getcwd(), 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

# --- Calculate Returns and Hurst Index ---

returns_pd = calculate_returns(prices_pd)

hurst_values = {col: hurst_exponent(returns_pd[col].values) for col in returns_pd.columns}

hurst_df_pd = pd.DataFrame([hurst_values], index=[returns_pd.index[-1]])
hurst_df_pd.index.name = 'date'

# --- Convert pandas DataFrames to Spark DataFrames ---

returns_spark = spark.createDataFrame(returns_pd.reset_index())

hurst_spark = spark.createDataFrame(hurst_df_pd.reset_index())

# --- Read prices into Spark DataFrame for further processing (if needed) ---

prices_spark = spark.read.csv(prices_path, header=True, inferSchema=True)

# --- Handle Empty DataFrames ---

if hurst_spark.count() == 0:

    hurst_spark = None
if returns_spark.count() == 0:

    returns_spark = None

# --- Create Error DataFrames if Needed ---

error_columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

if hurst_spark is None:

# --- Helper Functions ---

    error_data = [{col: -999 if col != 'date' else -1 for col in error_columns}]

    hurst_spark = spark.createDataFrame(error_data)

if returns_spark is None:

    error_data = [{col: 999 if col != 'date' else 1 for col in error_columns}]

    returns_spark = spark.createDataFrame(error_data)

# --- Compare DataFrames and Output Differences ---

def fuzz_udf(x, y, tol=1e-6):
    if x is None or y is None:
        return True
    return abs(x - y) > tol

fuzz = udf(fuzz_udf, BooleanType())

diff = returns_spark.alias('base').join(
    hurst_spark.alias('compare'),
    on='date',
    how='outer'
)

diff = diff.withColumn('_type_', lit('DIF')) \
    .withColumn('IBM_diff', fuzz(col('base.IBM'), col('compare.IBM'))) \
    .withColumn('GE_diff', fuzz(col('base.GE'), col('compare.GE'))) \
    .withColumn('DOW_diff', fuzz(col('base.DOW'), col('compare.DOW'))) \
    .withColumn('GOOGL_diff', fuzz(col('base.GOOGL'), col('compare.GOOGL'))) \
    .withColumn('SPY_diff', fuzz(col('base.SPY'), col('compare.SPY')))

diff_filtered = diff.filter(
    (col('_type_') == 'DIF') & (
        col('IBM_diff') | col('GE_diff') | col('DOW_diff') | col('GOOGL_diff') | col('SPY_diff')
    )
)

# --- Count Differences and Set Pass/Fail ---

n = diff_filtered.count()

if n == 0:

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST HURST_INDEX_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST HURST_INDEX_TEST')

# --- Clean Up Temporary Tables if Needed ---

    returns = df_pd.pct_change().dropna()
    return returns

def calculate_returns(df_pd):
    """Calculate percentage returns for a pandas DataFrame."""

# Set 'keep' to True or False as needed before running this script
# Example: keep = False
if 'keep' in locals() and not keep:
    pass  # No explicit deletion needed in Python; rely on garbage collection

def hurst_exponent(ts):
    """Calculate the Hurst exponent of a time series."""

    lags = range(2, 20)

    tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]

    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0
