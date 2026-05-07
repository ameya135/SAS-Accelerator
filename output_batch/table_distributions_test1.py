# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F, types as T
from pyspark.sql.functions import col, lag
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# --- 3. Calculate distribution statistics in pandas ---

# --- 7. Calculate distribution statistics in Spark ---

distribution_table_rows = []

stat_names = ['Mean', 'Std Dev', 'Sample skewness', 'Kurtosis', 'Min', 'Max', 'Median']
for i, stat in enumerate(stat_names):

distribution_table_pd = pd.DataFrame(distribution_table_rows)

distribution_table = spark.createDataFrame(distribution_table_pd)

# --- 6. Calculate returns in Spark (for distribution_table) ---

# Set up variables from dependencies/environment

# --- 8. Handle empty tables by inserting error rows if needed ---
if distribution_table.count() == 0:

    error_row = {'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999, '_stat_': 'Error'}

    distribution_table = spark.createDataFrame([error_row])

    error_row = {'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999, '_stat_': 'Error'}

    returns_from_r = spark.createDataFrame([error_row])

returns_from_r = returns_from_r.withColumn(
    '_stat_',
    F.when(F.col('_stat_') == 'Monthly Std Dev', 'Scaled Std Dev').otherwise(F.col('_stat_'))
)

# --- 10. Sort both DataFrames by _stat_ ---

returns_from_r = returns_from_r.orderBy('_stat_')

data_dir = os.environ.get('dir', '/tmp')  # Directory for input files

prices = spark.read.csv(os.path.join(data_dir, 'prices.csv'), header=True, inferSchema=True)

# --- 5. Read prices as Spark DataFrame ---

window_spec = Window.orderBy(prices.columns[0])

returns_exprs = [
    ((col(c) - lag(col(c), 1).over(window_spec)) / lag(col(c), 1).over(window_spec)).alias(c)
    for c in prices.columns[1:]
]

returns_spark = prices.select(prices.columns[0], *returns_exprs).na.drop()

agg_exprs = []
for c in prices.columns[1:]:
    agg_exprs.extend([
        F.mean(col(c)).alias(f'{c}_Mean'),
        F.stddev(col(c)).alias(f'{c}_Std Dev'),
        F.skewness(col(c)).alias(f'{c}_Sample skewness'),
        F.kurtosis(col(c)).alias(f'{c}_Kurtosis'),
        F.min(col(c)).alias(f'{c}_Min'),
        F.max(col(c)).alias(f'{c}_Max'),
        F.expr(f'percentile_approx({c}, 0.5)').alias(f'{c}_Median'),
    ])

distribution_stats_row = returns_spark.agg(*agg_exprs).collect()[0]

    row = {'_stat_': stat}
    for j, c in enumerate(prices.columns[1:]):

        value = distribution_stats_row[j*7 + i]
        row[c] = float(value) if value is not None else None
    distribution_table_rows.append(row)

distribution_table = distribution_table.orderBy('_stat_')

# --- 11. Compare DataFrames by _stat_ and output differences ---

join_cols = ['_stat_']

compare_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# --- 12. Handle skewness method difference: remove small differences for 'Sample skewness' ---

diff = diff.withColumn(
    'sum_abs',
    F.abs(F.col('IBM')) + F.abs(F.col('GE')) + F.abs(F.col('DOW')) + F.abs(F.col('GOOGL')) + F.abs(F.col('SPY'))
)

diff = diff.filter(~((F.col('_stat_') == 'Sample skewness') & (F.col('sum_abs') < 0.025)))

diff = diff.drop('sum_abs')

# --- 13. Count number of differences ---

keep_tables = os.environ.get('keep', 'FALSE').upper() == 'TRUE'

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_distribution_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_distribution_TEST1')

# --- 15. If keep_tables is False, clean up temporary tables ---
if not keep_tables:
    for df_name in ['diff', 'prices', 'returns_from_r', 'distribution_table']:
        try:

            df = locals().get(df_name)
            if df is not None and hasattr(df, 'unpersist'):
                df.unpersist()
        except Exception:
            pass

# --- 1. Read prices CSV as pandas DataFrame for financial calculations ---

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)

# --- 2. Calculate discrete returns using pandas ---

returns_pd = prices_pd.pct_change().dropna()

stats_dict = {
    'Mean': returns_pd.mean(),
    'Std Dev': returns_pd.std(),
    'Sample skewness': returns_pd.skew(),
    'Kurtosis': returns_pd.kurt(),
    'Min': returns_pd.min(),
    'Max': returns_pd.max(),
    'Median': returns_pd.median(),
}

stats_pd = pd.DataFrame(stats_dict).T.round(8)
stats_pd.index.name = '_stat_'
stats_pd.reset_index(inplace=True)

returns_from_r = spark.createDataFrame(stats_pd)

# --- 4. Create returns_from_r DataFrame from stats_pd ---

if returns_from_r.count() == 0:

# --- 9. Replace 'Monthly Std Dev' with 'Scaled Std Dev' in returns_from_r ---

diff = (
    returns_from_r.alias('base')
    .join(distribution_table.alias('cmp'), on=join_cols, how='inner')
    .select(
        F.col('base._stat_'),
        *[F.abs(F.col(f'base.{c}') - F.col(f'cmp.{c}')).alias(c) for c in compare_cols]
    )
    .withColumn('_type_', F.lit('DIF'))
    .filter(
        (F.abs(F.col('IBM')) > 5e-9) |
        (F.abs(F.col('GE')) > 5e-9) |
        (F.abs(F.col('DOW')) > 5e-9) |
        (F.abs(F.col('GOOGL')) > 5e-9) |
        (F.abs(F.col('SPY')) > 5e-9)
    )
)

n = diff.count()

# --- 14. Set pass/notes variables based on diff count ---
if n == 0:
