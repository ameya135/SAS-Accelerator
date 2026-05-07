# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("CalmarRatioTest1").getOrCreate()

# Initialize Spark session

# --- Calmar Ratio calculation ---

def calmar_ratio(returns_df, scale=1):
    # Calculate cumulative returns

    cum_returns = returns_df.cumsum()
    # Calculate max drawdown

    max_drawdown = (cum_returns.expanding().max() - cum_returns).max()
    # Calculate annualized return

    annual_return = returns_df.mean() * scale
    # Calmar Ratio
    return annual_return / max_drawdown.replace(0, np.nan)

calmar_ratio_pdf = calmar_ratio_pdf[['date'] + [c for c in calmar_ratio_pdf.columns if c != 'date']]

# --- Convert pandas DataFrames to Spark DataFrames ---

# --- Read prices as Spark DataFrame (if needed elsewhere) ---

    error_data = [(-1, -999, -999, -999, -999, -999)]

    calmar_ratio_sdf = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_sdf = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

# --- Compare DataFrames by date and calculate differences ---

# Set variables from environment or defaults

# --- Count number of differences and set test result ---

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST CALMAR_RATIO_TEST1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST CALMAR_RATIO_TEST1')

# --- Optionally clean up intermediate DataFrames if not keeping ---
if not keep:

    diff = None

data_dir = os.environ.get('dir', '/tmp')

prices_sdf = spark.read.csv(os.path.join(data_dir, 'prices.csv'), header=True, inferSchema=True)

    prices_sdf = None

    calmar_ratio_sdf = None

    returns_sdf = None

keep = os.environ.get('keep', 'FALSE').upper() == 'TRUE'

# --- Read and process prices data using pandas ---

prices_pdf = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
prices_pdf.set_index('date', inplace=True)

# Calculate discrete returns

returns_pdf = prices_pdf.pct_change().dropna()

calmar_ratio_pdf = pd.DataFrame([calmar_ratio(returns_pdf, scale=1)])
calmar_ratio_pdf['date'] = returns_pdf.index[-1]

returns_sdf = spark.createDataFrame(returns_pdf.reset_index())

calmar_ratio_sdf = spark.createDataFrame(calmar_ratio_pdf)

# --- Handle empty DataFrames by creating error rows if needed ---
if calmar_ratio_sdf.count() == 0:

if returns_sdf.count() == 0:

joined = returns_sdf.alias('r').join(calmar_ratio_sdf.alias('c'), on='date', how='inner')

diff = joined.filter(
    (pyspark_abs(col('r.IBM') - col('c.IBM')) > 1e-6) |
    (pyspark_abs(col('r.GE') - col('c.GE')) > 1e-6) |
    (pyspark_abs(col('r.DOW') - col('c.DOW')) > 1e-6) |
    (pyspark_abs(col('r.GOOGL') - col('c.GOOGL')) > 1e-6) |
    (pyspark_abs(col('r.SPY') - col('c.SPY')) > 1e-6)
)

n = diff.count()

if n == 0:
