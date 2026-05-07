# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName('DownsideFrequencyTest').getOrCreate()

# --- Initialize Spark session ---

MAR = 0.01 / 252

# --- Downside Frequency calculation (MAR = 0.01/252) ---

downside_frequency_pd = downside_frequency_pd[['date'] + [c for c in downside_frequency_pd.columns if c != 'date']]

# --- Convert pandas DataFrames to Spark DataFrames ---

# --- Save DataFrames for comparison ---

returns_from_r = returns_sdf

DownsideFrequency = downside_frequency_sdf

# --- If tables have 0 records, create error DataFrames ---

error_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']
if DownsideFrequency.count() == 0:

    error_data = [(-1, -999, -999, -999, -999, -999)]

    DownsideFrequency = spark.createDataFrame(error_data, error_schema)
if returns_from_r.count() == 0:

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_from_r = spark.createDataFrame(error_data, error_schema)

# --- Compare DataFrames and output differences ---

# --- Set variables from macro or environment ---

diff = returns_from_r.alias('base').join(
    DownsideFrequency.alias('compare'),
    on='date',
    how='inner'
)

diff = diff.select(
    col('base.date'),
    (abs(col('base.IBM') - col('compare.IBM'))).alias('IBM_DIF'),
    (abs(col('base.GE') - col('compare.GE'))).alias('GE_DIF'),
    (abs(col('base.DOW') - col('compare.DOW'))).alias('DOW_DIF'),
    (abs(col('base.GOOGL') - col('compare.GOOGL'))).alias('GOOGL_DIF'),
    (abs(col('base.SPY') - col('compare.SPY'))).alias('SPY_DIF')
)

diff = diff.withColumn(
    'DIF',
    (col('IBM_DIF') > 1e-8) |
    (col('GE_DIF') > 1e-8) |
    (col('DOW_DIF') > 1e-8) |
    (col('GOOGL_DIF') > 1e-8) |
    (col('SPY_DIF') > 1e-8)
)

diff_filtered = diff.filter(col('DIF'))

n = diff_filtered.count()

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST DOWNSIDE_FREQUENCY_TEST')
else:

# --- Set pass/fail and notes ---
if n == 0:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST DOWNSIDE_FREQUENCY_TEST')

keep = False if str(keep).upper() == 'FALSE' else True

# --- Cleanup if keep is False ---
if not keep:

    returns_from_r = None

    DownsideFrequency = None

    diff = None

dir_path = dir

# --- Read prices CSV as DataFrame ---

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

downside_mask = returns_pd < MAR

downside_frequency_pd = downside_mask.sum() / len(returns_pd)

downside_frequency_pd = downside_frequency_pd.to_frame().T
downside_frequency_pd['date'] = returns_pd.index[-1]

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

downside_frequency_sdf = spark.createDataFrame(downside_frequency_pd)

# --- Calculate discrete returns ---
