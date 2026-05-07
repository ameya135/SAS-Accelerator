# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("KappaTest2").getOrCreate()

# Initialize Spark session

# Kappa calculation (MAR=0.01/252, l=2)

    excess = returns - MAR

    downside = np.where(excess < 0, -excess, 0)

    denom = np.mean(downside ** l)
    return (excess.mean()) / (denom ** (1/l)) if denom != 0 else np.nan

MAR = 0.01 / 252

def kappa(returns, MAR, l):

# Create Kappa DataFrame

kappa_pd = pd.DataFrame([kappa_vals])

kappa_sdf = spark.createDataFrame(kappa_pd)

# Create returns_from_r DataFrame (mimic R output)

# Handle empty tables by replacing with error rows
if kappa_sdf.count() == 0:

    error_row = {'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    kappa_sdf = spark.createDataFrame([error_row])

    error_row = {'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r_sdf = spark.createDataFrame([error_row])

# Compare DataFrames and output differences (fuzz logic: abs diff > 1e-8)

# Set variables from macro or environment

def fuzz(a, b, tol=1e-8):
    return abs(a - b) > tol

kappa_row = kappa_sdf.collect()[0].asDict()

# Count number of differences

    pass_var = True

    notes_var = 'Passed'
    print('NOTE: NO ERROR IN TEST Kappa_TEST2')
else:

keep = False if str('${keep}').upper() == 'FALSE' else True

    pass_var = False

    notes_var = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Kappa_TEST2')

dir_path = os.environ.get('dir', '${dir}')

# Read prices.csv as pandas DataFrame, then convert to Spark DataFrame

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)  # Assume first column is date/index
prices_pd.index = pd.to_datetime(prices_pd.index)

returns_pd = prices_pd.pct_change().dropna()

kappa_vals = {col: kappa(returns_pd[col], MAR, 2) for col in returns_pd.columns}

returns_from_r_sdf = spark.createDataFrame(returns_pd.reset_index())

if returns_from_r_sdf.count() == 0:

returns_row = returns_from_r_sdf.collect()[0].asDict()

diffs = []
for col in ['IBM', 'GE', 'DOW', 'GOOGL']:
    if fuzz(kappa_row.get(col, 0), returns_row.get(col, 0)):
        difs.append({'col': col, 'kappa': kappa_row.get(col, 0), 'returns': returns_row.get(col, 0)})

diff_sdf = spark.createDataFrame(diffs) if difs else spark.createDataFrame([], 'col string, kappa double, returns double')

n = diff_sdf.count()

# Set pass/notes variables and print result
if n == 0:

prices_sdf = spark.createDataFrame(prices_pd.reset_index())

# If keep is False, unpersist temp tables
if not keep:
    prices_sdf.unpersist()
    diff_sdf.unpersist()
    returns_from_r_sdf.unpersist()
    kappa_sdf.unpersist()

# Calculate returns (discrete method, drop NA)
