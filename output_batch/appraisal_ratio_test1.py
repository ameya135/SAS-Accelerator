# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName("AppraisalRatioTest1").getOrCreate()

# Initialize Spark session

# Appraisal Ratio calculation (custom implementation)

def appraisal_ratio(returns, benchmark, rf=0.01/252):

    excess_returns = returns - rf

    bm_excess = benchmark - rf

    beta = excess_returns.cov(bm_excess) / bm_excess.var()

    alpha = excess_returns.mean() - beta * bm_excess.mean()

    tracking_error = (excess_returns - beta * bm_excess).std()
    return alpha / tracking_error

# Assume first 4 columns are assets, 5th is benchmark

returns_assets = returns_pd[asset_cols]

returns_bm = returns_pd[bm_col]

rf = 0.01 / 252

# Calculate appraisal ratios for each asset

appraisal_ratios = {}
for asset in asset_cols:

    ar = appraisal_ratio(returns_assets[asset], returns_bm, rf)
    appraisal_ratios[asset] = ar

# Prepare Appraisal_Ratio DataFrame

appraisal_ratio_df = pd.DataFrame([appraisal_ratios])
appraisal_ratio_df['SPY'] = returns_bm.name if 'SPY' in returns_bm.name else np.nan
appraisal_ratio_df['date'] = -1

# Set variables from macro or environment

appraisal_ratio_sdf = spark.createDataFrame(appraisal_ratio_df)

# Prepare returns_from_r DataFrame (simulate R output)

# Check if Appraisal_Ratio and returns_from_r have records, drop if empty
if appraisal_ratio_sdf.count() == 0:

    returns_from_r_sdf = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames (simulate PROC COMPARE with fuzz logic)

diff_df = diff_df.withColumn('IBM_DIF', abs(col('base.IBM') - col('compare.IBM')) > 1e-6)

keep = False if os.environ.get('KEEP', 'FALSE') == 'FALSE' else True

diff_df = diff_df.withColumn('GE_DIF', abs(col('base.GE') - col('compare.GE')) > 1e-6)

diff_df = diff_df.withColumn('DOW_DIF', abs(col('base.DOW') - col('compare.DOW')) > 1e-6)

diff_df = diff_df.withColumn('GOOGL_DIF', abs(col('base.GOOGL') - col('compare.GOOGL')) > 1e-6)

    pass_var = True

    notes_var = 'Passed'
    print('NOTE: NO ERROR IN TEST APPRAISAL_RATIO_TEST1')
else:

    pass_var = False

    notes_var = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST APPRAISAL_RATIO_TEST1')

dir_path = os.environ.get('DIR', '.')

# Cleanup if keep is False
if not keep:
    for df_name in ['diff_filtered', 'prices_pd', 'returns_from_r_sdf', 'appraisal_ratio_sdf']:
        if df_name in locals():
            locals().pop(df_name)

# Read prices CSV as DataFrame

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

asset_cols = prices_pd.columns[:4]

bm_col = prices_pd.columns[4]

appraisal_ratio_df = appraisal_ratio_df[['date'] + list(asset_cols) + ['SPY']]

returns_from_r_df = returns_pd.reset_index().copy()

returns_from_r_sdf = spark.createDataFrame(returns_from_r_df)

    appraisal_ratio_sdf = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r_sdf.count() == 0:

diff_df = returns_from_r_sdf.alias('base').join(
    appraisal_ratio_sdf.alias('compare'),
    on=['date'],
    how='outer'
)

diff_filtered = diff_df.filter(
    col('IBM_DIF') | col('GE_DIF') | col('DOW_DIF') | col('GOOGL_DIF')
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:

# Calculate discrete returns (using pandas for financial calculations)
