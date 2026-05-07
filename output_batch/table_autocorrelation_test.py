# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
import statsmodels.api as sm
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as ps_abs, col

spark = SparkSession.builder.appName("table_autocorrelation_TEST").getOrCreate()

# ---------------------------
# Initialize Spark session
# ---------------------------

p_value = lb_test['lb_pvalue'].iloc[0]

# ---------------------------
# Prepare pandas DataFrames for output
# ---------------------------

returns_from_r_pd = pd.DataFrame({
    'rho1': [autocorrs[0]],
    'rho2': [autocorrs[1]],
    'rho3': [autocorrs[2]],
    'rho4': [autocorrs[3]],
    'rho5': [autocorrs[4]],
    'rho6': [autocorrs[5]],
    'Q_6__p_value': [p_value]
})

AutoCorrelations_pd = pd.DataFrame({
    'lag1': [autocorrs[0]],
    'lag2': [autocorrs[1]],
    'lag3': [autocorrs[2]],
    'lag4': [autocorrs[3]],
    'lag5': [autocorrs[4]],
    'lag6': [autocorrs[5]],
    'p_value': [p_value]
})

# ---------------------------
# Convert pandas DataFrames to Spark DataFrames
# ---------------------------

returns_from_r = spark.createDataFrame(returns_from_r_pd)

AutoCorrelations = spark.createDataFrame(AutoCorrelations_pd)

# ---------------------------
# Handle empty DataFrames by inserting default rows
# ---------------------------
if AutoCorrelations.count() == 0:

    AutoCorrelations = spark.createDataFrame([(-999,)*7], ['lag1','lag2','lag3','lag4','lag5','lag6','p_value'])
if returns_from_r.count() == 0:

    returns_from_r = spark.createDataFrame([(999,)*7], ['rho1','rho2','rho3','rho4','rho5','rho6','Q_6__p_value'])

# ---------------------------
# Compare DataFrames: absolute difference > 1e-4 for any lag or p_value
# ---------------------------

diff = AutoCorrelations.join(returns_from_r, how='inner') \
    .withColumn('lag1_diff', ps_abs(col('lag1') - col('rho1'))) \
    .withColumn('lag2_diff', ps_abs(col('lag2') - col('rho2'))) \
    .withColumn('lag3_diff', ps_abs(col('lag3') - col('rho3'))) \
    .withColumn('lag4_diff', ps_abs(col('lag4') - col('rho4'))) \
    .withColumn('lag5_diff', ps_abs(col('lag5') - col('rho5'))) \
    .withColumn('lag6_diff', ps_abs(col('lag6') - col('rho6'))) \
    .withColumn('p_value_diff', ps_abs(col('p_value') - col('Q_6__p_value')))

diff_filtered = diff.filter(
    (col('lag1_diff') > 1e-4) |
    (col('lag2_diff') > 1e-4) |
    (col('lag3_diff') > 1e-4) |
    (col('lag4_diff') > 1e-4) |
    (col('lag5_diff') > 1e-4) |
    (col('lag6_diff') > 1e-4) |
    (col('p_value_diff') > 1e-4)
)

# ---------------------------
# Count differences and set pass/notes variables
# ---------------------------

n_diff = diff_filtered.count()

if n_diff == 0:

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_autocorrelation_TEST')
else:

    pass_var = False

# ---------------------------
# Macro variables (should be set externally or passed as arguments)
# Example:
# dir = '/path/to/dir'
# keep = False
# ---------------------------
# dir, keep must be defined before running this script

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_autocorrelation_TEST')

# ---------------------------
# Drop intermediate tables if keep is False
# ---------------------------
if not keep:
    AutoCorrelations.unpersist()
    returns_from_r.unpersist()
    diff_filtered.unpersist()

# ---------------------------
# Read prices.csv and calculate returns/autocorrelations
# ---------------------------

prices_pd = pd.read_csv(os.path.join(dir, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)

returns_pd = prices_pd.pct_change().dropna()

lb_test = sm.stats.acorr_ljungbox(returns_pd, lags=[6], return_df=True)

# Calculate autocorrelations up to lag 6

autocorrs = [returns_pd.corrwith(returns_pd.shift(lag)).mean() for lag in range(1, 7)]

# Calculate Ljung-Box Q statistic and p-value for lag 6
