# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName('AnnualizedReturnsTest1').getOrCreate()

# ---- Configuration / Macro Variables ----
# Set these variables externally or before running the script
# Example:
# keep = False
# dir = '/path/to/dir'

rf = 0.01 / 252

scale = 252

def annualized_return(returns, rf=rf, scale=scale):

    excess = returns - rf

    compounded = (1 + excess).prod()

    n_periods = returns.shape[0]
    return compounded ** (scale / n_periods) - 1

annualized_table_pd = pd.DataFrame([annualized_dict])

# ---- Convert pandas DataFrames to Spark DataFrames ----

# ---- Initialize Spark Session ----

annualized_table = spark.createDataFrame(annualized_table_pd)

# ---- Handle Empty DataFrames ----
if annualized_table.count() == 0:

    returns_from_r = None

# ---- Insert Error Rows if Needed ----
if annualized_table is None:

    error_row = {'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    annualized_table = spark.createDataFrame([error_row])

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r = spark.createDataFrame([error_row])

# ---- Compare DataFrames for Differences ----

join_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

diff = diff.withColumn('_type_', F.lit('DIF'))

# ---- Count Differences and Set Pass/Fail ----

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_Annualized_Returns_TEST1')
else:

# ---- Load Data ----

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_Annualized_Returns_TEST1')

# ---- Cleanup if Not Keeping Intermediates ----
if not keep:

    diff = None

    returns_from_r = None

    annualized_table = None

    prices_pd = None

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path, parse_dates=['date'])
prices_pd.set_index('date', inplace=True)

# ---- Calculate Discrete Returns ----

returns_pd = prices_pd.pct_change().dropna()

annualized_dict = {col: annualized_return(returns_pd[col]) for col in returns_pd.columns}

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

    annualized_table = None
if returns_from_r.count() == 0:

if returns_from_r is None:

diff = returns_from_r.crossJoin(annualized_table).select([
    F.abs(returns_from_r[c] - annualized_table[c]).alias(c) for c in join_cols
])

diff_filtered = diff.filter(
    (F.col('IBM') > 1e-4) | (F.col('GE') > 1e-4) | (F.col('DOW') > 1e-4) | (F.col('GOOGL') > 1e-4) | (F.col('SPY') > 1e-4)
)

n = diff_filtered.count()

if n == 0:

# ---- Calculate Annualized Returns (Geometric) ----
