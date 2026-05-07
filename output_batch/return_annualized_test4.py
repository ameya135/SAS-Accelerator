# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, Window, functions as F

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

annualized_returns_pdf = annualized_returns_pdf[['date'] + [col for col in annualized_returns_pdf.columns if col != 'date']]

# Convert pandas DataFrames to Spark DataFrames

    error_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    error_data = [(-1, -999, -999, -999, -999, -999)]

    annualized_returns = spark.createDataFrame(error_data, error_schema)

    error_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_from_r = spark.createDataFrame(error_data, error_schema)

# Keep only the last row of annualized_returns

window_last = Window.orderBy(F.col('date').desc())

annualized_returns = annualized_returns.withColumn('rn', F.row_number().over(window_last)).filter(F.col('rn') == 1).drop('rn')

def fuzz(x, y, tol=1e-8):
    return abs(x - y) < tol if x is not None and y is not None else False

diff_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# Macro variables (should be set externally or passed as arguments)
# Example usage:
# dir = '/path/to/dir'
# keep = False

diff_rows = []

diff = spark.createDataFrame(diff_rows, diff_schema) if diff_rows else spark.createDataFrame([], diff_schema)

n = diff.count()

# Set n = number of differences

# Set pass/notes based on n
if n == 0:

    pass_ = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ANNUALIZED_TEST4')
else:

    pass_ = False

# Read prices CSV as Spark DataFrame via pandas

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ANNUALIZED_TEST4')

# Optionally drop intermediate DataFrames if keep==False
if not keep:

    diff = None

    annualized_returns = None

    returns_from_r = None

prices_path = os.path.join(dir, 'prices.csv')

prices_pdf = pd.read_csv(prices_path, parse_dates=['date'])
prices_pdf.set_index('date', inplace=True)

# Calculate log returns using pandas

returns_pdf = np.log(prices_pdf / prices_pdf.shift(1)).dropna()

annualized_returns_pdf = returns_pdf.mean() * 12

annualized_returns_pdf = annualized_returns_pdf.to_frame().T
annualized_returns_pdf['date'] = returns_pdf.index.max()

returns_from_r = spark.createDataFrame(returns_pdf.reset_index())

annualized_returns = spark.createDataFrame(annualized_returns_pdf)

# Handle empty DataFrames by replacing with error rows
if annualized_returns.count() == 0:

if returns_from_r.count() == 0:

# Fuzzy compare returns_from_r and annualized_returns

r_r = returns_from_r.collect()[0]

a_r = annualized_returns.collect()[0]
if any([not fuzz(getattr(r_r, col), getattr(a_r, col)) for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]):
    diff_rows.append(tuple([getattr(r_r, col) for col in diff_schema]))

# Annualize returns (arithmetic mean * 12)
