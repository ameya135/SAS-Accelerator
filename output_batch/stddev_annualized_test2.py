# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, stddev_samp, max as spark_max
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("StdDevAnnualizedTest2").getOrCreate()

# --- Initialize Spark session ---

returns_df = returns_df.dropna()

# --- Annualize standard deviation (scale=12 for monthly data) ---

scale = 12

annualized_stddev_dict = {}
for ret_col in ['IBM_ret', 'GE_ret', 'DOW_ret', 'GOOGL_ret', 'SPY_ret']:

    returns_from_r = None

    error_row = {'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    annualized_stddev = spark.createDataFrame([error_row])

# --- Set up macro variable equivalents (set these before running) ---

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r = spark.createDataFrame([error_row])

annualized_stddev = annualized_stddev.orderBy(col('date').desc()).limit(1)

def fuzz(x, y, tol=1e-8):
    return abs(x - y) > tol

diff_mask = (
    fuzz(diff_pd['IBM'].iloc[0], diff_pd['IBM'].iloc[1]) or
    fuzz(diff_pd['GE'].iloc[0], diff_pd['GE'].iloc[1]) or
    fuzz(diff_pd['DOW'].iloc[0], diff_pd['DOW'].iloc[1]) or
    fuzz(diff_pd['GOOGL'].iloc[0], diff_pd['GOOGL'].iloc[1]) or
    fuzz(diff_pd['SPY'].iloc[0], diff_pd['SPY'].iloc[1])
)

n = int(diff_mask)

dir_path = dir_macro_variable  # Directory path as string

# --- Set pass/notes based on comparison ---
if n == 0:

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST StdDev_annualized_test2')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST StdDev_annualized_test2')

keep = keep_macro_variable     # Boolean: True to keep temp tables, False to clean up

# --- Read prices CSV as DataFrame ---

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(f'{dir_path}/prices.csv')

returns_df = prices_df
for ticker in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    stddev_val = returns_df.agg(stddev_samp(col(ret_col))).collect()[0][0]
    if stddev_val is not None:
        annualized_stddev_dict[ret_col.replace('_ret', '')] = float(stddev_val) * np.sqrt(scale)
    else:
        annualized_stddev_dict[ret_col.replace('_ret', '')] = None

annualized_stddev_pd = pd.DataFrame([annualized_stddev_dict])
annualized_stddev_pd['date'] = returns_df.agg(spark_max('date')).collect()[0][0]

annualized_stddev = spark.createDataFrame(annualized_stddev_pd)

# --- Create annualized_stddev DataFrame ---

returns_from_r_pd = returns_df.select('date', 'IBM_ret', 'GE_ret', 'DOW_ret', 'GOOGL_ret', 'SPY_ret').toPandas()
returns_from_r_pd.rename(columns={c: c.replace('_ret', '') for c in returns_from_r_pd.columns if '_ret' in c}, inplace=True)

returns_from_r = spark.createDataFrame(returns_from_r_pd)

# --- Prepare returns_from_r DataFrame (simulate R output structure) ---

# --- Drop tables if they have 0 records ---
if annualized_stddev.count() == 0:

    annualized_stddev = None
if returns_from_r.count() == 0:

# --- If annualized_stddev does not exist, create error row ---
if annualized_stddev is None:

# --- If returns_from_r does not exist, create error row ---
if returns_from_r is None:

# --- Keep only the last row in annualized_stddev ---

# --- Compare returns_from_r and annualized_stddev (excluding date) ---

diff = returns_from_r.crossJoin(annualized_stddev.drop('date'))

diff_pd = diff.toPandas()

# --- Clean up temporary tables if keep is False ---
if not keep:
    annualized_stddev.unpersist()
    returns_from_r.unpersist()

# --- Calculate discrete returns (percentage change) ---

window_spec = Window.orderBy('date')

    returns_df = returns_df.withColumn(f'{ticker}_ret', (col(ticker) / lag(col(ticker), 1).over(window_spec)) - 1)
