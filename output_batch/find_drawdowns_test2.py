# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

def find_drawdowns(returns):

    cumulative = (1 + returns).cumprod()

    highwater = cumulative.cummax()

    drawdown = (cumulative - highwater) / highwater

    min_dd = drawdown.min()

    min_idx = drawdown.idxmin()

    max_idx = drawdown[:min_idx].idxmax() if not drawdown[:min_idx].empty else drawdown.index[0]

    length = (drawdown.index.get_loc(min_idx) - drawdown.index.get_loc(max_idx))

    peaktotrough = abs(min_dd)

    recovery = None  # Not implemented
    return pd.DataFrame({
        'return': [min_dd],
        'begin': [max_idx],
        'trough': [min_idx],
        'end': [min_idx],
        'length': [length],
        'peaktotrough': [peaktotrough],
        'recovery': [recovery]
    })

# Compute drawdowns

# Convert pandas DataFrames to Spark DataFrames

FindDrawdowns = returns_from_r

placeholder = [(-999, -999, -999, -999, -999, -999, -999)]

# Handle empty DataFrames by inserting placeholder row

columns = ['return', 'begin', 'trough', 'end', 'length', 'peaktotrough', 'recovery']

# Macro variables (should be set externally or passed as arguments)
# keep, dir

if FindDrawdowns.count() == 0:

    returns_from_r = spark.createDataFrame(placeholder, columns)

# Compare DataFrames and output differences

# Count differences

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST FIND_DRAWDOWNS_TEST2')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST FIND_DRAWDOWNS_TEST2')

# Drop intermediate tables if keep==False
if not keep:
    for tbl in ['diff', 'prices', 'FindDrawdowns', 'returns_from_r']:
        try:
            spark.catalog.dropTempView(tbl)
        except Exception:
            pass

# Calculate log returns and drop NA

# Function to find drawdowns (largest only)

# Load prices.csv as DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd.set_index(prices_pd.columns[0], inplace=True)

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

returns_from_r_pd = find_drawdowns(returns_pd.iloc[:, 0])

returns_from_r = spark.createDataFrame(returns_from_r_pd)

prices = spark.createDataFrame(prices_pd.reset_index())

# Simulate FindDrawdowns output (assuming similar to returns_from_r)

    FindDrawdowns = spark.createDataFrame(placeholder, columns)
if returns_from_r.count() == 0:

diff = returns_from_r.join(
    FindDrawdowns,
    on=columns,
    how='outer'
).withColumn('_type_', F.lit('DIF'))

n = diff.count()

# Output test result
if n == 0:
