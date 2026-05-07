# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("AppraisalRatioTest2").getOrCreate()

# --- Initialize Spark session ---

# --- Calculate Appraisal Ratio using pandas ---

def appraisal_ratio(returns, benchmark_col, rf=0.01/252):

    asset_cols = returns.columns.difference([benchmark_col, 'date'])

    excess_returns = returns[asset_cols].subtract(returns[benchmark_col], axis=0) - rf

    tracking_error = excess_returns.std(ddof=1)

    mean_excess = excess_returns.mean()

    ratio = mean_excess / tracking_error.replace(0, np.nan)

    result = pd.DataFrame([ratio], columns=asset_cols)
    result['date'] = returns['date'].iloc[-1]
    result[benchmark_col] = returns[benchmark_col].iloc[-1]
    return result

tables = [t.name for t in spark.catalog.listTables()]
if 'Appraisal_Ratio' not in tables:

# --- If tables do not exist, create error DataFrames ---

    error_data = [{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}]

    appraisal_ratio_sdf = spark.createDataFrame(pd.DataFrame(error_data))
    appraisal_ratio_sdf.createOrReplaceTempView('Appraisal_Ratio')

if 'returns_from_r' not in tables:

    error_data = [{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}]

    returns_sdf = spark.createDataFrame(pd.DataFrame(error_data))
    returns_sdf.createOrReplaceTempView('returns_from_r')

# --- Define macro variables (should be set externally or passed as arguments) ---
# Example placeholders (replace with actual values or pass as arguments)
# dir = '/path/to/data'
# keep = False

# --- Compare DataFrames and output differences (fuzz logic: abs diff > 1e-6) ---

diff_sdf = diff_sdf.withColumn('IBM_DIF', pyspark_abs(col('base.IBM') - col('compare.IBM')) > 1e-6)

diff_sdf = diff_sdf.withColumn('GE_DIF', pyspark_abs(col('base.GE') - col('compare.GE')) > 1e-6)

diff_sdf = diff_sdf.withColumn('DOW_DIF', pyspark_abs(col('base.DOW') - col('compare.DOW')) > 1e-6)

diff_sdf = diff_sdf.withColumn('GOOGL_DIF', pyspark_abs(col('base.GOOGL') - col('compare.GOOGL')) > 1e-6)

# --- Count number of differences ---

# --- Read prices CSV into Spark DataFrame ---

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST APPRAISAL_RATIO_TEST2')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST APPRAISAL_RATIO_TEST2')

# --- If keep is FALSE, drop intermediate tables ---
if not keep:
    for view in ['Appraisal_Ratio', 'returns_from_r']:
        if view in [t.name for t in spark.catalog.listTables()]:
            spark.catalog.dropTempView(view)

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])

prices_sdf = spark.createDataFrame(prices_pd)

# --- Calculate discrete returns using pandas ---
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()
returns_pd.reset_index(inplace=True)

returns_sdf = spark.createDataFrame(returns_pd)

appraisal_ratio_pd = appraisal_ratio(returns_pd, benchmark_col='SPY', rf=0.01/252)

appraisal_ratio_sdf = spark.createDataFrame(appraisal_ratio_pd)

# --- Register DataFrames as temporary views for SQL operations ---
appraisal_ratio_sdf.createOrReplaceTempView('Appraisal_Ratio')
returns_sdf.createOrReplaceTempView('returns_from_r')

# --- Check if tables have 0 records and drop if so ---
if appraisal_ratio_sdf.count() == 0:
    spark.catalog.dropTempView('Appraisal_Ratio')
if returns_sdf.count() == 0:
    spark.catalog.dropTempView('returns_from_r')

diff_sdf = returns_sdf.alias('base').join(
    appraisal_ratio_sdf.alias('compare'),
    on='date',
    how='inner'
)

diff_filtered = diff_sdf.filter(
    (col('IBM_DIF') | col('GE_DIF') | col('DOW_DIF') | col('GOOGL_DIF'))
)

n = diff_filtered.count()

# --- Set pass/fail and notes variables ---
if n == 0:
