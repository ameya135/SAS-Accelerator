# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName('SharpeRatioAnnualizedTest1').getOrCreate()

# Initialize Spark session

# --- Calculate discrete returns using pandas ---

# --- Annualized Sharpe Ratio calculation ---

rf = 0.01 / 252

# --- Prepare Sharpe Ratio DataFrame ---

# --- Convert pandas DataFrame to Spark DataFrame ---

# --- Simulate R output (for comparison) ---

Sharpe_from_R = Sharpe_Ratio

    Sharpe_Ratio = None
if Sharpe_from_R.count() == 0:

    Sharpe_from_R = None

    error_data = [(-1, -999, -999, -999, -999, -999)]

    Sharpe_Ratio = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

# Macro variable equivalents

if Sharpe_from_R is None:

    error_data = [(1, 999, 999, 999, 999, 999)]

    Sharpe_from_R = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

Sharpe_Ratio = Sharpe_Ratio.orderBy(col('date').desc()).limit(1)

def fuzz(x, y, tol=1e-6):
    return abs(x - y) > tol

diff_rows = []

Sharpe_from_R_pd = Sharpe_from_R.toPandas()

n = None  # Will be set after comparison

    row_r = Sharpe_from_R_pd.iloc[idx]

    diffs = {col: fuzz(row_r[col], row_s[col]) for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']}
    if any(diffs.values()):
        diff_rows.append({**{'date': row_r['date']}, **{k: row_r[k] for k in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']}})

diff = pd.DataFrame(diff_rows)

n = len(diff)

# --- Output test result ---
if n == 0:

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST SharpeRatio_annualized_test1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST SharpeRatio_annualized_test1')

dir_path = os.environ.get('DIR', '/path/to/dir')

keep = False  # Set to True to keep intermediate files

# --- Clean up if keep is False ---
if not keep:
    pass  # No explicit deletion needed; variables will be garbage collected

# --- Read and preprocess price data ---

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pdf = pd.read_csv(prices_path, parse_dates=['date'])
prices_pdf.set_index('date', inplace=True)

returns_pdf = prices_pdf.pct_change().dropna()

excess_returns = returns_pdf - rf

mean_excess_return = excess_returns.mean()

std_excess_return = excess_returns.std()

sharpe_ratio_annualized = (mean_excess_return / std_excess_return) * np.sqrt(252)

sharpe_ratio_df = pd.DataFrame([sharpe_ratio_annualized])
sharpe_ratio_df.insert(0, 'date', returns_pdf.index.max())
sharpe_ratio_df.columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

Sharpe_Ratio = spark.createDataFrame(sharpe_ratio_df)

# --- Handle empty DataFrames ---
if Sharpe_Ratio.count() == 0:

# --- Insert error rows if DataFrames are None ---
if Sharpe_Ratio is None:

# --- Keep only the last row in Sharpe_Ratio ---

# --- Compare Sharpe_from_R and Sharpe_Ratio (fuzzy match) ---

Sharpe_Ratio_pd = Sharpe_Ratio.toPandas()
for idx in range(len(Sharpe_from_R_pd)):

    row_s = Sharpe_Ratio_pd.iloc[min(idx, len(Sharpe_Ratio_pd)-1)]
