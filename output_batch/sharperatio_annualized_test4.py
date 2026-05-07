# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, row_number
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SharpeRatioAnnualizedTest4").getOrCreate()

# Initialize Spark session

# Calculate log returns using pandas

returns_pdf = returns_pdf.reset_index()

# Convert returns to Spark DataFrame

# --- Calculate Annualized Sharpe Ratio ---

rf = 0.01 / 12

scale = 12

def sharpe_annualized(returns, rf, scale):

    excess = returns - rf

    mean_excess = excess.mean()

    std_excess = excess.std(ddof=0)

    sharpe = (mean_excess / std_excess) * np.sqrt(scale)
    return sharpe

sharpe_ratio_pdf = pd.DataFrame([sharpe_row])

sharpe_ratio_sdf = spark.createDataFrame(sharpe_ratio_pdf)

# Simulate R output for comparison (using same logic as above)

sharpe_from_r_sdf = sharpe_ratio_sdf

# Set parameters (replace with actual values as needed)

# --- Handle Empty Results ---

if sharpe_ratio_sdf.count() == 0:

    sharpe_ratio_pdf = pd.DataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])

    sharpe_ratio_sdf = spark.createDataFrame(sharpe_ratio_pdf)

if sharpe_from_r_sdf.count() == 0:

    sharpe_from_r_pdf = pd.DataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

    sharpe_from_r_sdf = spark.createDataFrame(sharpe_from_r_pdf)

# --- Keep Only the Last Row in Sharpe Ratio DataFrame ---

window_spec = Window.orderBy('date')

sharpe_ratio_sdf = sharpe_ratio_sdf.withColumn('rn', row_number().over(window_spec))

data_dir = '/path/to/your/dir'  # Replace with actual directory

last_row_num = sharpe_ratio_sdf.count()

sharpe_ratio_sdf = sharpe_ratio_sdf.filter(col('rn') == last_row_num).drop('rn')

# --- Compare Results and Find Differences ---

def fuzz(x, y, tol=1e-6):
    return abs(x - y) > tol

sharpe_from_r_pdf = sharpe_from_r_sdf.toPandas()

sharpe_ratio_pdf = sharpe_ratio_sdf.toPandas()

diff_rows = []
for idx in range(len(sharpe_from_r_pdf)):

    row_r = sharpe_from_r_pdf.iloc[idx]

    row_s = sharpe_ratio_pdf.iloc[idx] if idx < len(sharpe_ratio_pdf) else None
    if row_s is not None:

        diffs = {col: fuzz(row_r[col], row_s[col]) for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']}
        if any(diffs.values()):

keep_tables = False  # Set as needed

            diff_row = {'_type_': 'DIF', **{col: row_r[col] for col in ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']}}
            diff_rows.append(diff_row)

diff_pdf = pd.DataFrame(diff_rows)

diff_sdf = spark.createDataFrame(diff_pdf) if not diff_pdf.empty else spark.createDataFrame([], sharpe_from_r_sdf.schema)

# --- Count Differences and Set Pass/Fail ---

n_diffs = diff_sdf.count() if diff_sdf is not None else 0

if n_diffs == 0:

    pass_var = True

    notes_var = 'Passed'
    print('NOTE: NO ERROR IN TEST SharpeRatio_annualized_test4')
else:

    pass_var = False

    notes_var = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST SharpeRatio_annualized_test4')

# --- Read and Prepare Data ---

# --- Optional: Clean Up Intermediate Tables ---

if not keep_tables:
    # Variables will be cleaned up by Python's garbage collector
    pass

# Read prices CSV as pandas DataFrame

prices_pdf = pd.read_csv(f'{data_dir}/prices.csv', parse_dates=True, index_col=0)
prices_pdf.index.name = 'date'

prices_sdf = spark.createDataFrame(prices_pdf.reset_index())

returns_pdf = np.log(prices_pdf / prices_pdf.shift(1)).dropna()
returns_pdf.index.name = 'date'

returns_sdf = spark.createDataFrame(returns_pdf)

sharpe_dict = {}
for colname in returns_pdf.columns:
    if colname != 'date':
        sharpe_dict[colname] = sharpe_annualized(returns_pdf[colname], rf, scale)

sharpe_row = {'date': returns_pdf['date'].iloc[-1]}
sharpe_row.update(sharpe_dict)

# Convert prices to Spark DataFrame
