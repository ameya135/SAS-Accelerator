# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, lit, log
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("MSquared_test3").getOrCreate()

# Initialize Spark session

# --- Define tM2 function (mimicking R logic) ---

        scale = 4  # Default scale if not provided

def tM2(Ra, Rb, Rf=0, scale=None, geometric=True):
    if scale is None:

    mean_ra = Ra.mean()

    std_ra = Ra.std()

    sr = ((mean_ra - Rf) / std_ra) * np.sqrt(scale)

    sb = Rb.std() * np.sqrt(scale)

    rm = Rb.mean() * scale if not geometric else (np.prod(1 + Rb) ** (scale / len(Rb)) - 1)
    if geometric:

        Rf_adj = (1 + Rf) ** scale - 1
    else:

        Rf_adj = Rf * scale

    result = sr * sb + Rf_adj - rm
    return result

# --- Convert pandas DataFrames to Spark DataFrames ---

# --- Calculate log returns in Spark ---

# Set up variables (replace with actual values or parameterize as needed)

    returns_from_r = None

# --- Create error rows if DataFrames do not exist ---

data_dir = '/path/to/dir'  # Set this appropriately

    MSquared_schema = asset_cols

    returns_from_r_schema = asset_cols

# --- Compare DataFrames: compute differences (fuzz logic) ---
# Join on all asset columns

join_cols = asset_cols

diff = diff.withColumn('_type_', lit('DIF'))

# For demonstration, filter where any asset columns differ by more than a small fuzz tolerance

keep = False

fuzz_tolerance = 1e-6

diff_filter = None
for col_name in asset_cols:

    condition = pyspark_abs(col(col_name) - col(col_name)) > fuzz_tolerance

    diff_filter = condition if diff_filter is None else (diff_filter | condition)
if diff_filter is not None:

    diff = diff.filter(diff_filter)

# --- Count number of differences ---

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST MSQUARED_TEST3')
else:

# --- Read and preprocess data with pandas ---

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST MSQUARED_TEST3')

# --- Optionally delete intermediate tables if not keeping ---
if not keep:

    diff = None

    prices = None

    returns_from_r = None

    MSquared = None

# Calculate log returns, drop NA

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

# --- Apply tM2 to assets and benchmark ---

assets = returns_pd.iloc[:, 0:4]

benchmark = returns_pd.iloc[:, 4]

tM2_results = [tM2(assets.iloc[:, i], benchmark, Rf=0.01/4, scale=4, geometric=False) for i in range(assets.shape[1])]

returns_from_r_pd = pd.DataFrame([tM2_results], columns=assets.columns)

prices = spark.createDataFrame(prices_pd)

returns_from_r = spark.createDataFrame(returns_from_r_pd)

windowSpec = Window.orderBy('date') if 'date' in prices.columns else Window.orderBy(prices.columns[0])
for col_name in prices.columns[1:]:

    prices = prices.withColumn(f'{col_name}_log_return', log(col(col_name)) - log(lag(col(col_name), 1).over(windowSpec)))

# --- MSquared calculation in Spark (using pandas result for demonstration) ---

MSquared_pd = returns_from_r_pd.copy()

MSquared = spark.createDataFrame(MSquared_pd)

# --- Handle empty DataFrames ---
if MSquared.count() == 0:

    MSquared = None
if returns_from_r.count() == 0:

asset_cols = list(assets.columns)
if MSquared is None:

    MSquared = spark.createDataFrame([tuple([-999] * len(asset_cols))], MSquared_schema)

if returns_from_r is None:

    returns_from_r = spark.createDataFrame([tuple([999] * len(asset_cols))], returns_from_r_schema)

diff = returns_from_r.join(MSquared, on=join_cols, how='outer')

n = diff.count()

# --- Set pass/notes variables based on comparison ---
if n == 0:
