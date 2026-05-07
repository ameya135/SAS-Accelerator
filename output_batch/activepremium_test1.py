# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("ActivePremium_test1").getOrCreate()

# Initialize Spark session

# Active Premium calculation: columns 0-3 are assets, column 4 is benchmark

# Convert pandas DataFrames to Spark DataFrames

# --- Read prices into Spark DataFrame and calculate returns ---

window_spec = Window.orderBy('date')

        prices_spark = prices_spark.withColumn(
            f'{col}_return',
            (F.col(col) - F.lag(col).over(window_spec)) / F.lag(col).over(window_spec)
        )

prices_spark = prices_spark.dropna()

# --- Active Premium calculation in Spark ---

asset_cols = ['IBM', 'GE', 'DOW', 'GOOGL']

bm_col = 'SPY'
for asset in asset_cols:

def active_premium_pd(returns, bm_col):
    return returns.iloc[:, :4].sub(returns.iloc[:, bm_col], axis=0)

    active_premium = active_premium.withColumn(asset, F.col(asset) - F.col(bm_col))

    returns_from_r = None

# Set up variables from macro/environment

# --- Create error rows if DataFrames are empty ---

schema = StructType([
    StructField('date', IntegerType(), True),
    StructField('IBM', DoubleType(), True),
    StructField('GE', DoubleType(), True),
    StructField('DOW', DoubleType(), True),
    StructField('GOOGL', DoubleType(), True),
    StructField('SPY', DoubleType(), True)
])

    returns_from_r = spark.createDataFrame(
        [(1, 999.0, 999.0, 999.0, 999.0, 999.0)],
        schema=schema
    )

# --- Compare DataFrames: absolute difference, criterion 0.00001 ---

diff = diff.withColumn('_type_', F.lit('DIF'))

diff = diff.withColumn('IBM_diff', F.abs(F.col('base.IBM') - F.col('compare.IBM')))

diff = diff.withColumn('GE_diff', F.abs(F.col('base.GE') - F.col('compare.GE')))

keep = False  # Set from macro variable

diff = diff.withColumn('DOW_diff', F.abs(F.col('base.DOW') - F.col('compare.DOW')))

diff = diff.withColumn('GOOGL_diff', F.abs(F.col('base.GOOGL') - F.col('compare.GOOGL')))

diff = diff.filter(
    (F.col('_type_') == 'DIF') & (
        (F.col('IBM_diff') > 1e-5) |
        (F.col('GE_diff') > 1e-5) |
        (F.col('DOW_diff') > 1e-5) |
        (F.col('GOOGL_diff') > 1e-5)
    )
)

# --- Count number of differences ---

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST ActivePremium_test1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST ActivePremium_test1')

data_dir = os.environ.get('dir', '/tmp')  # Directory for input files

# --- Clean up temporary tables if keep is False ---
if not keep:
    for df_name in ['diff', 'prices_spark', 'returns_from_r', 'active_premium']:
        try:
            eval(df_name).unpersist()
        except Exception:
            pass

# --- Read and process prices.csv using pandas ---

prices_path = os.path.join(data_dir, 'prices.csv')

prices_spark = spark.read.csv(prices_path, header=True, inferSchema=True)

for col in prices_spark.columns:
    if col != 'date':

prices_pd = pd.read_csv(prices_path, parse_dates=True, index_col=0)

returns_pd = prices_pd.pct_change().dropna()

returns_active_premium_pd = active_premium_pd(returns_pd, 4)

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

active_premium = spark.createDataFrame(returns_active_premium_pd.reset_index())

# --- Handle empty DataFrames ---
if active_premium.count() == 0:
    active_premium.unpersist()

    active_premium = None
if returns_from_r.count() == 0:
    returns_from_r.unpersist()

if active_premium is None:

    active_premium = spark.createDataFrame(
        [(-1, -999.0, -999.0, -999.0, -999.0, -999.0)],
        schema=schema
    )
if returns_from_r is None:

diff = returns_from_r.alias('base').join(
    active_premium.alias('compare'),
    on='date',
    how='inner'
)

n = diff.count()

# --- Set pass/fail and notes ---
if n == 0:

# Calculate returns using pandas (discrete method)
