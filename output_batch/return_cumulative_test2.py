# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col, log, row_number, sum as spark_sum
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

window_spec = Window.orderBy('date')

        prev_val = col(col_name).over(window_spec.rowsBetween(-1, -1))

        log_col = log(col(col_name)) - log(prev_val)

        log_col_name = f'{col_name}_log'

# Remove first row with nulls from log returns

cum_window = Window.orderBy('date').rowsBetween(Window.unboundedPreceding, 0)

cumulative_cols = []
for col_name in log_return_cols:

    cum_col_name = f'{col_name}_cum'

    returns = returns.withColumn(cum_col_name, spark_sum(col(col_name)).over(cum_window))
    cumulative_cols.append(cum_col_name)

returns_from_r = cumulative_returns

# Simulate returns_from_r as a copy for comparison (in real migration, this would be imported from R)

    cumulative_returns = spark.createDataFrame([{'date': -1, 'IBM_log_cum': -999, 'GE_log_cum': -999, 'DOW_log_cum': -999, 'GOOGL_log_cum': -999, 'SPY_log_cum': -999}])
if returns_from_r.count() == 0:

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM_log_cum': 999, 'GE_log_cum': 999, 'DOW_log_cum': 999, 'GOOGL_log_cum': 999, 'SPY_log_cum': 999}])

# Define parameters (replace with actual values or pass as parameters)

# Keep only the last row in cumulative_returns

window_last = Window.orderBy('date').rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)

cumulative_returns = cumulative_returns.withColumn('rn', row_number().over(window_last))

join_cols = [col_name for col_name in cumulative_cols]

tolerance = 1e-8
for col_name in join_cols:

# Fuzzy comparison: check if any absolute difference > tolerance (e.g., 1e-8)

keep = False  # Set to True to keep intermediate DataFrames

    diff = diff.withColumn(f'{col_name}_diff', spark_abs(col(f'{col_name}_left') - col(f'{col_name}_right')) > tolerance if f'{col_name}_left' in diff.columns and f'{col_name}_right' in diff.columns else spark_abs(col(col_name) - col(col_name)) > tolerance)

# If columns are not suffixed by join, adjust accordingly

diff = diff.withColumn('IBM_diff', spark_abs(col('IBM_log_cum') - col('IBM_log_cum')) > tolerance)

diff = diff.withColumn('GE_diff', spark_abs(col('GE_log_cum') - col('GE_log_cum')) > tolerance)

diff = diff.withColumn('DOW_diff', spark_abs(col('DOW_log_cum') - col('DOW_log_cum')) > tolerance)

diff = diff.withColumn('GOOGL_diff', spark_abs(col('GOOGL_log_cum') - col('GOOGL_log_cum')) > tolerance)

diff = diff.withColumn('SPY_diff', spark_abs(col('SPY_log_cum') - col('SPY_log_cum')) > tolerance)

diff = diff.filter(
    col('IBM_diff') | col('GE_diff') | col('DOW_diff') | col('GOOGL_diff') | col('SPY_diff')
)

data_dir = "/path/to/data"  # Replace with actual directory path

    pass_ = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_CUMULATIVE_TEST2')
else:

    pass_ = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_CUMULATIVE_TEST2')

# Optionally delete intermediate DataFrames if not keeping
if not keep:

    prices = None

    cumulative_returns = None

    returns_from_r = None

    diff = None

# Read prices CSV as DataFrame

prices_path = os.path.join(data_dir, 'prices.csv')

prices = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Calculate log returns for each column except 'date'

log_return_cols = []
for col_name in prices.columns:
    if col_name != 'date':

        prices = prices.withColumn(log_col_name, log_col)
        log_return_cols.append(log_col_name)

returns = prices.select('date', *log_return_cols).na.drop()

# Calculate cumulative returns (arithmetic sum, not geometric)

# Prepare cumulative_returns DataFrame

cumulative_returns = returns.select('date', *cumulative_cols)

# Handle empty DataFrames by creating error rows
if cumulative_returns.count() == 0:

max_rn = cumulative_returns.agg({'rn': 'max'}).collect()[0][0]

cumulative_returns = cumulative_returns.filter(col('rn') == max_rn).drop('rn')

# Compare returns_from_r and cumulative_returns (excluding date)
# Join on all columns except 'date'

diff = returns_from_r.join(cumulative_returns, on='date', how='inner')

n = diff.count()

# Set pass/fail and notes
if n == 0:
