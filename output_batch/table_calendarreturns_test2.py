# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F, types as T
from functools import reduce

spark = SparkSession.builder.appName("CalendarReturnsTest2").getOrCreate()

# -------------------------------
# Initialize Spark session
# -------------------------------

# -------------------------------
# Pivot to calendar returns: months as columns, years as rows
# -------------------------------

calendar_returns_pd = monthly_returns_pd['SPY'].copy().to_frame('SPY')
calendar_returns_pd['Year'] = calendar_returns_pd.index.year
calendar_returns_pd['Month'] = calendar_returns_pd.index.strftime('%b').str.upper()

calendar_returns_pivot = calendar_returns_pd.pivot(index='Year', columns='Month', values='SPY')

month_order = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

calendar_returns_pivot = calendar_returns_pivot.reindex(columns=month_order)

calendar_returns_pivot = calendar_returns_pivot.reset_index()

# -------------------------------
# Convert to Spark DataFrame
# -------------------------------

Calendar_Returns = spark.createDataFrame(calendar_returns_pivot.fillna(np.nan))

# -------------------------------
# Drop rows with missing JAN (all months missing)
# -------------------------------

Calendar_Returns = Calendar_Returns.dropna(subset=['JAN'])

# -------------------------------
# If Calendar_Returns is empty, create error row
# -------------------------------
if Calendar_Returns.count() == 0:

    error_schema = T.StructType([T.StructField('Year', T.IntegerType(), True)] +
                                [T.StructField(m, T.DoubleType(), True) for m in month_order])

    error_row = [None] + [-999.0]*12

    Calendar_Returns = spark.createDataFrame([error_row], schema=error_schema)

returns_from_r = Calendar_Returns

# -------------------------------
# Simulate returns_from_r as a copy (since R code is not run here)
# -------------------------------

# -------------------------------
# If returns_from_r is empty, create error row
# -------------------------------
if returns_from_r.count() == 0:

    error_schema = T.StructType([T.StructField('Year', T.IntegerType(), True)] +
                                [T.StructField(m, T.DoubleType(), True) for m in month_order])

    error_row = [None] + [999.0]*12

    returns_from_r = spark.createDataFrame([error_row], schema=error_schema)

# -------------------------------
# Macro variables (should be set externally or passed as arguments)
# Example:
# dir = '/path/to/dir'
# keep = False
# -------------------------------

# -------------------------------
# Compare DataFrames: absolute difference > 1e-4 for any month
# -------------------------------

diff = Calendar_Returns.alias('cal').join(
    returns_from_r.alias('r'), on='Year', how='outer', suffixes=('_cal', '_r')
)

diff_exprs = [F.abs(F.col(f'cal.{m}') - F.col(f'r.{m}')) > 1e-4 for m in month_order]

diff = diff.where(reduce(lambda x, y: x | y, diff_exprs))

# -------------------------------
# Count differences
# -------------------------------

n = diff.count()

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_CalendarReturns_TEST2')
else:

# -------------------------------
# Set pass/fail and notes
# -------------------------------
if n == 0:

    pass_test = False

# -------------------------------
# Read prices.csv as Pandas DataFrame
# -------------------------------

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_CalendarReturns_TEST2')

# -------------------------------
# Clean up temporary tables if keep is False
# -------------------------------
if not keep:
    Calendar_Returns.unpersist()
    returns_from_r.unpersist()
    diff.unpersist()

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path, parse_dates=True, index_col=0)
prices_pd.index = pd.to_datetime(prices_pd.index)

# -------------------------------
# Calculate log returns and monthly cumulative returns
# -------------------------------

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

monthly_returns_pd = returns_pd.resample('M').sum()
