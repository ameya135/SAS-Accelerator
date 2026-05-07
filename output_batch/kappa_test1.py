# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# --- Initialize Spark session ---

# --- Kappa calculation (MAR=0.01/252, l=1) ---

    excess = series - MAR

    downside = np.minimum(excess, 0) ** l

    denom = np.mean(np.abs(downside))
    return excess.mean() / (denom ** (1/l)) if denom != 0 else np.nan

MAR = 0.01 / 252

def kappa(series, MAR, l):

L = 1

# --- Convert returns and kappa to Spark DataFrames ---

kappa_pd = pd.DataFrame([kappa_dict])

kappa_spark = spark.createDataFrame(kappa_pd)

# --- Handle empty DataFrames by creating error rows ---
if kappa_spark.count() == 0:

    error_row = {col: -999 for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']}

    kappa_spark = spark.createDataFrame([error_row])

    error_row = {col: 999 for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']}

    returns_spark = spark.createDataFrame([error_row])

# --- Set up variables from macro variables ---

# --- Compare DataFrames: compute differences for specified columns ---
# Since the join keys are not specified, using crossJoin for demonstration

for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    diff = diff.withColumn(f'{col_name}_DIF', abs(col(col_name) - col(col_name)))

fuzz_tolerance = 1e-6
for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    diff = diff.withColumn(f'fuzz_{col_name}', col(f'{col_name}_DIF') > fuzz_tolerance)

# --- Count number of differences ---

keep = False  # Set from macro variable

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Kappa_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Kappa_TEST1')

# --- End of script ---

dir_path = dir_macro_variable  # Set from macro variable

# --- Read prices.csv as DataFrame ---

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pd = pd.read_csv(prices_path)

prices_pd_xts = prices_pd.set_index(prices_pd.columns[0])

returns_pd = prices_pd_xts.pct_change().dropna()

kappa_dict = {col_name: kappa(returns_pd[col_name], MAR, L) for col_name in returns_pd.columns}

returns_spark = spark.createDataFrame(returns_pd.reset_index())

if returns_spark.count() == 0:

diff = returns_spark.crossJoin(kappa_spark)

# --- Fuzz function: treat as difference if abs diff > tolerance ---

diff_filtered = diff.filter(
    col('fuzz_IBM') | col('fuzz_GE') | col('fuzz_DOW') | col('fuzz_GOOGL')
)

n = diff_filtered.count()

# --- Set pass/fail and notes ---
if n == 0:

# --- Calculate returns (discrete method, drop NA) ---
