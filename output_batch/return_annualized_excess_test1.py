# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# --- Annualized excess return calculation ---

scale = 252

geometric = True
if geometric:

# --- Convert pandas DataFrames to Spark DataFrames ---

returns_from_r = annualized_excess

prices = spark.read.csv(os.path.join(dir, 'prices.csv'), header=True, inferSchema=True)

# --- Read prices.csv as Spark DataFrame (if needed elsewhere) ---

    annualized_excess = None
if returns_from_r.count() == 0:

    returns_from_r = None

# --- Create error DataFrames if needed ---

error_schema = StructType([
    StructField('IBM', DoubleType(), True),
    StructField('GE', DoubleType(), True),
    StructField('DOW', DoubleType(), True),
    StructField('GOOGL', DoubleType(), True)
])

    annualized_excess = spark.createDataFrame([(-999.0, -999.0, -999.0, -999.0)], schema=error_schema)
if returns_from_r is None:

    returns_from_r = spark.createDataFrame([(999.0, 999.0, 999.0, 999.0)], schema=error_schema)

# --- Compare DataFrames (fuzzy logic) ---

returns_from_r_pd = returns_from_r.toPandas()

diff_mask = (
    ~np.isclose(returns_from_r_pd['IBM'], annualized_excess_pd['IBM']) |
    ~np.isclose(returns_from_r_pd['GE'], annualized_excess_pd['GE']) |
    ~np.isclose(returns_from_r_pd['DOW'], annualized_excess_pd['DOW']) |
    ~np.isclose(returns_from_r_pd['GOOGL'], annualized_excess_pd['GOOGL'])
)

diff_pd = returns_from_r_pd[diff_mask]

diff = spark.createDataFrame(diff_pd)

# --- Count differences and set pass/notes variables ---

n = diff.count()
if n == 0:

# Macro variable equivalents (should be set externally or passed as arguments)
# n, dir, nv, keep

    pass_var = True

# Set directory and keep flag (example values, should be set externally)
# dir = '/path/to/data'
# keep = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ANNUALIZED_EXCESS_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ANNUALIZED_EXCESS_TEST1')

# --- Optionally delete intermediate tables if keep == False ---
# (No 'del' statements needed; Spark handles memory management)

# --- Read prices.csv as Pandas DataFrame ---

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

risk_free_col = prices_pd.columns[4]  # 5th column as benchmark

# --- Calculate discrete returns ---

returns_pd = prices_pd.pct_change().dropna()

excess_returns = returns_pd.iloc[:, :4].sub(returns_pd[risk_free_col], axis=0)

    ann_excess = (1 + excess_returns).prod() ** (scale / len(excess_returns)) - 1
else:

    ann_excess = excess_returns.mean() * scale

annualized_excess_pd = pd.DataFrame([ann_excess], columns=excess_returns.columns)

annualized_excess = spark.createDataFrame(annualized_excess_pd.reset_index(drop=True))

# --- Handle empty DataFrames ---
if annualized_excess.count() == 0:

if annualized_excess is None:

annualized_excess_pd = annualized_excess.toPandas()
