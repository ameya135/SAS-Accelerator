# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col, lit
from pyspark.sql.types import BooleanType
from pyspark.sql.functions import udf

spark = SparkSession.builder.appName("OmegaTest").getOrCreate()

# Initialize Spark session

# --- Omega Ratio Calculation ---

    excess = returns[returns > L] - L

    gain = excess.sum()

L = 0.01 / 252

def omega_ratio(returns, L):

    shortfall = L - returns[returns < L]

    loss = shortfall.sum()
    return gain / loss if loss != 0 else np.nan

omega_pdf = pd.DataFrame([omega_dict])

# --- Convert pandas DataFrames to Spark DataFrames ---

omega_sdf = spark.createDataFrame(omega_pdf)

# --- Create Error DataFrames if Views Do Not Exist ---

table_names = [t.name for t in spark.catalog.listTables()]
if 'Omega' not in table_names:

    error_data = [(-1, -999, -999, -999, -999, -999)]

    columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    omega_sdf = spark.createDataFrame(error_data, columns)
    omega_sdf.createOrReplaceTempView('Omega')
if 'returns_from_r' not in table_names:

    error_data = [(1, 999, 999, 999, 999, 999)]

# Set variables from macro or environment

    columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    returns_sdf = spark.createDataFrame(error_data, columns)
    returns_sdf.createOrReplaceTempView('returns_from_r')

# --- Fuzzy Comparison of DataFrames ---

def fuzz_udf(x):
    return abs(x) < 1e-6 if x is not None else False

fuzz = udf(fuzz_udf, BooleanType())

diff_sdf = diff_sdf.withColumn('_type_', lit('DIF')) \
    .withColumn('fuzz_IBM', fuzz(col('base.IBM') - col('compare.IBM'))) \
    .withColumn('fuzz_GE', fuzz(col('base.GE') - col('compare.GE'))) \
    .withColumn('fuzz_DOW', fuzz(col('base.DOW') - col('compare.DOW'))) \
    .withColumn('fuzz_GOOGL', fuzz(col('base.GOOGL') - col('compare.GOOGL'))) \
    .withColumn('fuzz_SPY', fuzz(col('base.SPY') - col('compare.SPY')))

# --- Count Differences and Set Pass/Fail ---

keep = False  # Set from macro or environment

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST OMEGA_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST OMEGA_TEST')

# --- Cleanup Temp Views if Not Keeping ---
if not keep:
    for view in ['Omega', 'returns_from_r']:
        if view in [t.name for t in spark.catalog.listTables()]:
            spark.catalog.dropTempView(view)

data_dir = os.environ.get('dir', '/path/to/dir')

# --- Data Loading ---
# Read prices CSV as pandas DataFrame

prices_pdf = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
prices_pdf['date'] = pd.to_datetime(prices_pdf['date'])
prices_pdf.set_index('date', inplace=True)

# --- Return Calculation ---
# Calculate discrete returns using pandas

returns_pdf = prices_pdf.pct_change().dropna()

omega_dict = {col: omega_ratio(returns_pdf[col], L) for col in returns_pdf.columns}

returns_sdf = spark.createDataFrame(returns_pdf.reset_index())

# --- Register Temp Views ---
returns_sdf.createOrReplaceTempView('returns_from_r')
omega_sdf.createOrReplaceTempView('Omega')

# --- Drop Temp Views if Empty ---
if omega_sdf.count() == 0:
    spark.catalog.dropTempView('Omega')
if returns_sdf.count() == 0:
    spark.catalog.dropTempView('returns_from_r')

diff_sdf = returns_sdf.alias('base').join(
    omega_sdf.alias('compare'),
    on=['date'],
    how='outer'
)

diff_filtered = diff_sdf.filter(
    (col('_type_') == 'DIF') & (
        col('fuzz_IBM') | col('fuzz_GE') | col('fuzz_DOW') | col('fuzz_GOOGL') | col('fuzz_SPY')
    )
)

n = diff_filtered.count()

if n == 0:
