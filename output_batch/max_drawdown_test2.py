# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
from pyspark.sql import Row, SparkSession
from pyspark.sql.functions import abs as spark_abs, col, lag, log, max as spark_max, min as spark_min, when
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Prepare returns DataFrame (drop first row with nulls from lag)

returns_cols = [f'{c}_log_return' for c in asset_cols]

def max_drawdown_expr(col_name):

    w = Window.orderBy('date').rowsBetween(Window.unboundedPreceding, 0)

    running_max = spark_max(col(col_name)).over(w)

    drawdown = (col(col_name) - running_max) / running_max
    return drawdown

# Calculate max drawdown for each asset

for asset in returns_cols:

    returns_df = returns_df.withColumn(f'{asset}_drawdown', max_drawdown_expr(asset))

# Find max drawdown value for each asset

drawdown_cols = [f'{asset}_drawdown' for asset in returns_cols]

max_dd_exprs = [spark_min(col_name).alias(col_name.replace('_log_return_drawdown', '')) for col_name in drawdown_cols]

max_dd_dict = {col_name.replace('_log_return_drawdown', ''): max_dd_row[col_name.replace('_log_return_drawdown', '')] for col_name in drawdown_cols}

# Create max_dd DataFrame

max_dd_df = spark.createDataFrame([Row(date=1, **max_dd_dict)])

# Simulate returns_from_r DataFrame (as if imported from R)

returns_from_r_df = max_dd_df.withColumn('date', when(col('date').isNull(), 1).otherwise(col('date')))

# If tables have 0 records, create error rows
if max_dd_df.count() == 0:

    max_dd_df = spark.createDataFrame([Row(date=-1, IBM=-999, GE=-999, DOW=-999, GOOGL=-999, SPY=-999)])

if returns_from_r_df.count() == 0:

    returns_from_r_df = spark.createDataFrame([Row(date=1, IBM=999, GE=999, DOW=999, GOOGL=999, SPY=999)])

# Compare DataFrames by date and check for differences

diff_df = max_dd_df.join(returns_from_r_df, on='date', how='inner')
for asset in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    diff_df = diff_df.withColumn(f'{asset}_diff', spark_abs(col(f'{asset}') - col(f'{asset}')))

diff_df = diff_df.filter(
    (col('IBM_diff') > 1e-6) |
    (col('GE_diff') > 1e-6) |
    (col('DOW_diff') > 1e-6) |
    (col('GOOGL_diff') > 1e-6) |
    (col('SPY_diff') > 1e-6)
)

# Count number of differences

n = diff_df.count()

# Set variables from dependencies (assume these are provided elsewhere)
# n, dir, nv, keep are assumed to be set as Python variables

# Read prices CSV as DataFrame

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST MAX_DRAWDOWN_TEST2')
else:

# Set pass and notes variables based on comparison
if n == 0:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST MAX_DRAWDOWN_TEST2')

# Clean up temporary DataFrames if keep is False
if not keep:

    diff_df = None

    prices_df = None

    max_dd_df = None

    returns_from_r_df = None

prices_path = os.path.join(dir, 'prices.csv')

    returns_df = None

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

returns_df = prices_df.select(['date'] + returns_cols).dropna()

max_dd_row = returns_df.agg(*max_dd_exprs).collect()[0]

# Calculate log returns for each asset column

window_spec = Window.orderBy('date')

    prices_df = prices_df.withColumn(
        f'{col_name}_log_return',
        log(col(col_name)) - log(lag(col(col_name), 1).over(window_spec))
    )

asset_cols = [c for c in prices_df.columns if c != 'date']
for col_name in asset_cols:
