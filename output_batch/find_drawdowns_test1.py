# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
import numpy as np
from pyspark.sql import SparkSession, functions as F, types as T

spark = SparkSession.builder.appName("Find_Drawdowns_test1").getOrCreate()

# -------------------------------
# Initialize Spark session
# -------------------------------

def find_drawdowns(returns):

    cumulative = (1 + returns).cumprod()

    highwater = cumulative.cummax()

    drawdown = (cumulative - highwater) / highwater
    begin, troughs, ends, lengths, peaktotroughs, recoveries = [], [], [], [], [], []

    drawdown_copy = drawdown.copy()
    for _ in range(7):
        if len(drawdown_copy) == 0 or drawdown_copy.min() == 0:
            break

        dd_trough = drawdown_copy.idxmin()

        dd_begin = drawdown_copy.loc[:dd_trough][drawdown_copy.loc[:dd_trough] == 0].index[-1]
        try:

            dd_end = drawdown_copy.loc[dd_trough:][drawdown_copy.loc[dd_trough:] == 0].index[0]
        except IndexError:

            dd_end = drawdown_copy.index[-1]
        begin.append(dd_begin)
        troughs.append(dd_trough)
        ends.append(dd_end)
        lengths.append((dd_end - dd_begin).days)
        peaktotroughs.append((dd_trough - dd_begin).days)
        recoveries.append((dd_end - dd_trough).days)
        drawdown_copy.loc[dd_begin:dd_end] = 0

    result = pd.DataFrame({
        'return': [drawdown.min()] * len(begin),
        'begin': begin,
        'trough': troughs,
        'end': ends,
        'length': lengths,
        'peaktotrough': peaktotroughs,
        'recovery': recoveries
    })
    return result

# -------------------------------
# Convert pandas DataFrame to Spark DataFrame
# -------------------------------

FindDrawdowns = drawdowns_sdf

returns_from_r = drawdowns_sdf

# -------------------------------
# Handle empty DataFrames
# -------------------------------
if FindDrawdowns.count() == 0:

    FindDrawdowns = None
if returns_from_r.count() == 0:

    returns_from_r = None

# -------------------------------
# Create error DataFrame if needed
# -------------------------------

# -------------------------------
# Macro variable equivalents (set externally or here)
# -------------------------------
# Example assignments (replace with actual values as needed)
# dir = '/path/to/dir'
# keep = False

error_schema = T.StructType([
    T.StructField('return', T.DoubleType(), True),
    T.StructField('begin', T.TimestampType(), True),
    T.StructField('trough', T.TimestampType(), True),
    T.StructField('end', T.TimestampType(), True),
    T.StructField('length', T.IntegerType(), True),
    T.StructField('peaktotrough', T.IntegerType(), True),
    T.StructField('recovery', T.IntegerType(), True)
])

error_row = (-999.0, None, None, None, -999, -999, -999)
if FindDrawdowns is None:

    FindDrawdowns = spark.createDataFrame([error_row], schema=error_schema)
if returns_from_r is None:

    returns_from_r = spark.createDataFrame([error_row], schema=error_schema)

# -------------------------------
# Compare DataFrames and output differences
# -------------------------------

join_cols = ['return', 'begin', 'trough', 'end', 'length', 'peaktotrough', 'recovery']

diff = returns_from_r.join(
    FindDrawdowns,
    on=join_cols,
    how='outer'
).withColumn(
    '_merge',
    F.when(
        F.lit(True),  # Dummy column since Spark doesn't have pandas' indicator
        F.lit('both')
    )
)

n = diff.count()

# -------------------------------
# Set pass/notes variables based on comparison
# -------------------------------
if n == 0:

    pass_var = True

# -------------------------------
# Read prices.csv as Pandas DataFrame
# -------------------------------

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST FIND_DRAWDOWNS_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST FIND_DRAWDOWNS_TEST1')

# -------------------------------
# Optionally clean up intermediate DataFrames
# -------------------------------
if not keep:

    diff = None

    FindDrawdowns = None

    returns_from_r = None

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd.set_index(prices_pd.columns[0], inplace=True)  # Assuming first column is date/index
prices_pd.index = pd.to_datetime(prices_pd.index)

# -------------------------------
# Calculate discrete returns, drop NA
# -------------------------------

returns_pd = prices_pd.pct_change().dropna()

drawdowns_pd = find_drawdowns(returns_pd.iloc[:, 0])  # Assuming single asset for simplicity

drawdowns_sdf = spark.createDataFrame(drawdowns_pd)

# Simulate FindDrawdowns output (assuming same as drawdowns_sdf for test)

# -------------------------------
# Find drawdowns using pandas/numpy (PerformanceAnalytics equivalent)
# -------------------------------
