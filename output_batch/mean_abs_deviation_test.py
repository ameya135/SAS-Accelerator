# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, mean as pyspark_mean, col, lag
from pyspark.sql.window import Window

spark = SparkSession.builder.appName('MeanAbsDeviationTest').getOrCreate()

# Initialize Spark session

# --- Calculate returns (discrete method: (P_t/P_{t-1}) - 1) ---

# --- Remove first row (with null returns), keep only return columns ---

# --- Calculate Mean Absolute Deviation for each return column ---

mean_abs_dev_exprs = [pyspark_mean(pyspark_abs(col(c))).alias(c.replace('_ret', '')) for c in returns_cols]

# --- If views do not exist, create error rows ---

table_names = [t.name for t in spark.catalog.listTables()]
if 'mean_abs_dev' not in table_names:

    error_data = [{'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}]

    mean_abs_dev_sdf = spark.createDataFrame(pd.DataFrame(error_data))
    mean_abs_dev_sdf.createOrReplaceTempView('mean_abs_dev')

if 'returns_from_r' not in table_names:

    error_data = [{'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}]

    returns_only = spark.createDataFrame(pd.DataFrame(error_data))
    returns_only.createOrReplaceTempView('returns_from_r')

# --- Compare the two DataFrames and output differences ---

compare_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# Macro variables (replace with actual values or pass as arguments)

diff_exprs = [
    (pyspark_abs(col(f'returns_from_r.{c}') - col(f'mean_abs_dev.{c}')) > 1e-8).alias(f'fuzz_{c}')
    for c in compare_cols
]

# --- Count number of differences ---

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST mean_abs_dev_TEST')
else:

    pass_test = False

data_dir = dir  # directory path as string

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST mean_abs_dev_TEST')

keep_temp_views = keep  # boolean: True to keep temp views, False to drop

# --- Cleanup temp views if keep_temp_views is False ---
if not keep_temp_views:
    for view in ['prices', 'diff', 'returns_from_r', 'mean_abs_dev']:
        spark.catalog.dropTempView(view)

# --- Read CSV into Spark DataFrame ---

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)

prices_sdf = spark.createDataFrame(prices_pd)
prices_sdf.createOrReplaceTempView('prices')

window_spec = Window.orderBy('Date') if 'Date' in prices_sdf.columns else Window.orderBy(prices_sdf.columns[0])

returns_sdf = prices_sdf
for col_name in prices_sdf.columns:
    if col_name != 'Date':

        returns_sdf = returns_sdf.withColumn(f'{col_name}_ret', (col(col_name) / lag(col(col_name), 1).over(window_spec)) - 1)

returns_cols = [c for c in returns_sdf.columns if c.endswith('_ret')]

returns_only = returns_sdf.select(*returns_cols).na.drop()
returns_only.createOrReplaceTempView('returns_from_r')

mean_abs_dev_sdf = returns_only.agg(*mean_abs_dev_exprs)
mean_abs_dev_sdf.createOrReplaceTempView('mean_abs_dev')

# --- Drop views if they have 0 records ---
if mean_abs_dev_sdf.count() == 0:
    spark.catalog.dropTempView('mean_abs_dev')
if returns_only.count() == 0:
    spark.catalog.dropTempView('returns_from_r')

joined = returns_only.alias('returns_from_r').crossJoin(mean_abs_dev_sdf.alias('mean_abs_dev'))

diff = joined.select(
    *[col(f'returns_from_r.{c}').alias(c) for c in compare_cols],
    *diff_exprs
)

diff_filtered = diff.where(' or '.join([f'fuzz_{c}' for c in compare_cols]))
diff_filtered.createOrReplaceTempView('diff')

n = diff_filtered.count()

# --- Set pass/fail and notes ---
if n == 0:
