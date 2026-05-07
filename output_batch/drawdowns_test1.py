# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName("DrawdownsTest1").getOrCreate()

# Initialize Spark session

# Calculate drawdown peaks for IBM (first column)

def drawdown_peak(series):

    running_max = np.maximum.accumulate(series)

    drawdowns = (series - running_max) / running_max
    return drawdowns

# --- Convert pandas DataFrames to Spark DataFrames ---

# --- Read prices.csv as Spark DataFrame if needed ---

# --- Keep only IBM and skip first row as in SAS ---

    error_data = [(pd.Timestamp(-1), -999, -999, -999, -999, -999)]

    columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    drawdowns_sdf = spark.createDataFrame(error_data, columns)

    error_data = [(pd.Timestamp(1), 999, 999, 999, 999, 999)]

# Define file paths and macro variables (assumed provided)

    columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

    returns_sdf = spark.createDataFrame(error_data, columns)

# --- Count number of differences ---

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST DRAWDOWNS_TEST1')
else:

    pass_var = False

dir_path = dir      # Provided macro variable

prices_sdf = spark.read.csv(os.path.join(dir_path, 'prices.csv'), header=True, inferSchema=True)

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST DRAWDOWNS_TEST1')

    diff_sdf = None

    prices_sdf = None

    drawdowns_sdf = None

    returns_sdf = None

keep = keep         # Provided macro variable (should be boolean True/False)

# --- Clean up temporary tables if keep is False ---
if not keep:

# --- Read and process prices data using pandas ---

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

# Calculate returns (discrete method)

returns_pd = prices_pd.pct_change().dropna()

ibm_drawdown = drawdown_peak(returns_pd.iloc[:, 0] * 100) / 100

ibm_drawdown_df = ibm_drawdown.reset_index()
ibm_drawdown_df.columns = ['date', 'IBM']

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

drawdowns_sdf = spark.createDataFrame(ibm_drawdown_df)

first_date = drawdowns_sdf.first()['date']

drawdowns_sdf = drawdowns_sdf.select('date', 'IBM').where(col('date') != first_date)

# --- Handle empty DataFrames by creating error rows as in SAS ---
if drawdowns_sdf.count() == 0:

if returns_sdf.count() == 0:

# --- Compare returns_sdf and drawdowns_sdf on IBM column, output differences ---

diff_sdf = returns_sdf.join(drawdowns_sdf, on='date', how='inner', suffixes=('_r', '_d')) \
    .withColumn('IBM_DIF', abs(col('IBM_r') - col('IBM_d'))) \
    .filter(col('IBM_DIF') > 1e-8)

n = diff_sdf.count()

# --- Set pass/fail and notes based on comparison ---
if n == 0:
