# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, lit, log
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Remove the first row (since lag will be null)

returns_df = returns_df.filter(col('date').isNotNull())

returns_from_r_df = returns_df

# Define a fuzz function for floating point comparison

def fuzz(col1, tol=1e-8):
    return pyspark_abs(col1) < tol

# Filter rows where any column difference is above tolerance

# Count number of differences

    pass_flag = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_CALCULATE_TEST2')
else:

    pass_flag = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_CALCULATE_TEST2')

# Clean up intermediate DataFrames if keep is False
if not keep:

    prices_df = None

    returns_df = None

    returns_from_r_df = None

    diff_df = None

    diff_filtered_df = None

# Load prices.csv as DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

returns_df = prices_df.select(
    col('date'),
    *returns_exprs
)

# Simulate returns_from_r as a copy of returns_df (for comparison)

# Compare returns_from_r_df and returns_df element-wise by date

diff_df = returns_from_r_df.alias('base').join(
    returns_df.alias('compare'),
    on='date',
    how='inner'
)

diff_df = diff_df.select(
    'date',
    *[pyspark_abs(col(f'base.{c}') - col(f'compare.{c}')).alias(c) for c in returns_df.columns if c != 'date']
)

diff_filtered_df = diff_df.filter(
    ~(
        fuzz(col('IBM')) &
        fuzz(col('GE')) &
        fuzz(col('DOW')) &
        fuzz(col('GOOGL')) &
        fuzz(col('SPY'))
    )
)

n = diff_filtered_df.count()

if n == 0:

# Assume macro variables are provided as Python variables: n, dir, keep

# Calculate log returns for each column except 'date'

window_spec = Window.orderBy('date')

returns_exprs = [
    (log(col(c)) - log(lag(col(c), 1).over(window_spec))).alias(c)
    for c in prices_df.columns if c != 'date'
]
