# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lit

spark = SparkSession.builder.appName("Table_Drawdowns_test").getOrCreate()

# Initialize Spark session

def table_drawdowns(returns, top=10, digits=6):

    running_max = np.maximum.accumulate(returns)

    underwater = (returns - running_max) / running_max

    drawdown_ends = np.where((underwater == 0) & (np.roll(underwater, 1) < 0))[0]

    drawdown_starts = np.where((underwater < 0) & (np.roll(underwater, 1) == 0))[0]

    drawdowns = []
    for start in drawdown_starts:

# --- Table Drawdowns logic (top 10 drawdowns, similar to PerformanceAnalytics::table.Drawdowns) ---

        end_candidates = drawdown_ends[drawdown_ends > start]

        end = end_candidates[0] if len(end_candidates) > 0 else len(underwater) - 1

        trough = np.argmin(underwater[start:end+1]) + start

        depth = underwater[trough]

        length = end - start

        to_trough = trough - start

        recovery = end - trough
        drawdowns.append({
            'begindate': returns.index[start],
            'troughdate': returns.index[trough],
            'enddate': returns.index[end],
            'depth': round(depth, digits),
            'length': length,
            'totrough': to_trough,
            'recovery': recovery
        })

    drawdowns = sorted(drawdowns, key=lambda x: x['depth'])[:top]
    return pd.DataFrame(drawdowns)

# Apply drawdown calculation to first column (e.g., 'IBM')

returns_asset = returns_pd[asset_col]

TableDrawdowns_pd = table_drawdowns(returns_asset, top=10, digits=6)

# --- Convert pandas DataFrames to Spark DataFrames ---

# Set variables from dependencies (replace with actual values or pass as arguments)

TableDrawdowns = spark.createDataFrame(TableDrawdowns_pd)

# --- Handle empty DataFrames ---
if TableDrawdowns.count() == 0:

    TableDrawdowns = spark.createDataFrame([{
        'begindate': -999, 'troughdate': None, 'enddate': None,
        'depth': None, 'length': None, 'totrough': None, 'recovery': None
    }])

    returns_from_r = spark.createDataFrame([{
        'from': -999, 'trough': None, 'to': None,
        'depth': None, 'length': None, 'to_trough': None, 'recovery': None
    }])

# --- Compare DataFrames (simulate proc compare with fuzz/abs logic) ---
# Note: The join columns must exist in both DataFrames. Adjust as needed.

diff = diff.withColumn('_type_', lit('DIF')).filter(col('_type_') == 'DIF')

data_dir = os.environ.get('dir', '/tmp')

# --- Count differences ---

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST TABLE_DRAWDOWNS_TEST')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST TABLE_DRAWDOWNS_TEST')

keep = os.environ.get('keep', 'FALSE')

# --- Optionally clean up temporary tables ---
if keep == 'FALSE':
    for df_name in ['diff', 'prices', 'TableDrawdowns', 'returns_from_r']:
        if df_name in locals():
            locals().pop(df_name)

# Calculate returns using pandas (PerformanceAnalytics equivalent)

# --- Read and preprocess data ---
# Read prices.csv as pandas DataFrame and convert to Spark DataFrame

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)

returns_pd = prices_pd.pct_change().dropna()

asset_col = prices_pd.columns[0]

returns_from_r = spark.createDataFrame(returns_pd.reset_index())

prices = spark.createDataFrame(prices_pd.reset_index())

if returns_from_r.count() == 0:

diff = returns_from_r.alias('base').join(
    TableDrawdowns.alias('cmp'),
    (col('base.from') == col('cmp.begindate')) &
    (col('base.trough') == col('cmp.troughdate')) &
    (col('base.to') == col('cmp.enddate')) &
    (pyspark_abs(col('base.depth') - col('cmp.depth')) > 1e-5) &
    (col('base.length') == col('cmp.length')) &
    (col('base.to_trough') == col('cmp.totrough')) &
    (col('base.recovery') == col('cmp.recovery')),
    how='outer'
)

n = diff.count()

# --- Set pass/notes variables and print result ---
if n == 0:
