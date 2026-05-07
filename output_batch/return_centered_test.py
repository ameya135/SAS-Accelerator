# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, lit, mean as pyspark_mean, monotonically_increasing_id
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Convert pandas DataFrame to Spark DataFrame

centered_returns = returns

# Remove first row (firstobs=2 equivalent)

centered_returns = centered_returns.withColumn('row_id', monotonically_increasing_id())

centered_returns = centered_returns.filter(col('row_id') > 0).drop('row_id')

# --- Handle empty DataFrames ---
if centered_returns.count() == 0:

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Set up variables (replace with actual values or pass as arguments)

# --- Compare DataFrames (simulate proc compare with fuzz logic) ---
# Rename columns for join

centered_returns_renamed = centered_returns.select(
    col('date'),
    col('IBM_return').alias('IBM_c'),
    col('GE_return').alias('GE_c'),
    col('DOW_return').alias('DOW_c'),
    col('GOOGL_return').alias('GOOGL_c'),
    col('SPY_return').alias('SPY_c')
)

diff = diff.withColumn('IBM_DIF', pyspark_abs(col('IBM') - col('IBM_c')))

diff = diff.withColumn('GE_DIF', pyspark_abs(col('GE') - col('GE_c')))

diff = diff.withColumn('DOW_DIF', pyspark_abs(col('DOW') - col('DOW_c')))

diff = diff.withColumn('GOOGL_DIF', pyspark_abs(col('GOOGL') - col('GOOGL_c')))

diff = diff.withColumn('SPY_DIF', pyspark_abs(col('SPY') - col('SPY_c')))

diff = diff.filter(
    (col('IBM_DIF') > 1e-8) |
    (col('GE_DIF') > 1e-8) |
    (col('DOW_DIF') > 1e-8) |
    (col('GOOGL_DIF') > 1e-8) |
    (col('SPY_DIF') > 1e-8)
)

keep = False  # Set to True to keep intermediate DataFrames

# --- Count differences and set test result ---

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_MEAN_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_MEAN_TEST')

# --- Optional cleanup ---
if not keep:

    prices = None

    centered_returns = None

data_dir = '/path/to/data'  # Replace with actual directory path

prices = spark.read.csv(os.path.join(data_dir, 'prices.csv'), header=True, inferSchema=True)

# --- Read prices.csv into Spark DataFrame ---

window_spec = Window.orderBy('date')
for col_name in prices.columns:
    if col_name != 'date':

        prices = prices.withColumn(
            f'{col_name}_return',
            (col(col_name) - lag(col(col_name), 1).over(window_spec)) / lag(col(col_name), 1).over(window_spec)
        )

returns_cols = [f'{c}_return' for c in prices.columns if c != 'date']

returns = prices.select('date', *returns_cols).dropna()

# --- Calculate returns and centered returns in Spark ---

# Center the returns
for col_name in returns_cols:

    mean_val = returns.select(pyspark_mean(col(col_name))).collect()[0][0]

    returns = returns.withColumn(col_name, col(col_name) - lit(mean_val))

    returns_from_r = None

    diff = None

# --- Read and process prices.csv using pandas for R logic compatibility ---

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))

# Calculate discrete returns and center them (pandas)

returns_pd = prices_pd.pct_change().dropna()

returns_centered_pd = returns_pd - returns_pd.mean()

returns_from_r = spark.createDataFrame(returns_centered_pd.reset_index())

    centered_returns = spark.createDataFrame([{'date': -1, 'IBM_return': -999, 'GE_return': -999, 'DOW_return': -999, 'GOOGL_return': -999, 'SPY_return': -999}])
if returns_from_r.count() == 0:

returns_from_r_renamed = returns_from_r.select(
    col('date'),
    col('IBM'),
    col('GE'),
    col('DOW'),
    col('GOOGL'),
    col('SPY')
)

diff = returns_from_r_renamed.join(centered_returns_renamed, on='date', how='outer')

n = diff.count()

if n == 0:
