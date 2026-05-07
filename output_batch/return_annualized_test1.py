# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, Window, functions as F
from pyspark.sql.types import BooleanType, DoubleType

spark = SparkSession.builder.appName("notes").getOrCreate()

# Initialize Spark session

annualized_returns_pd = annualized_returns_pd[cols_order]

# --- 2. Read prices as Spark DataFrame and calculate annualized returns ---

prices_spark = spark.read.csv(os.path.join(dir, 'prices.csv'), header=True, inferSchema=True)

# Calculate discrete returns in Spark

window_spec = Window.orderBy('date')
for col in prices_spark.columns:
    if col != 'date':

        prices_spark = prices_spark.withColumn(
            f'{col}_return',
            (F.col(col) - F.lag(col).over(window_spec)) / F.lag(col).over(window_spec)
        )

# Remove first row with null returns

min_date = prices_spark.agg(F.min('date')).first()[0]

returns_spark = prices_spark.filter(F.col('date') != min_date)

# Annualize returns in Spark (geometric, scale=252)

def annualize_udf(*cols):

    vals = np.array(cols, dtype=np.float64)

    vals = vals[~np.isnan(vals)]
    if len(vals) == 0:
        return None
    return float(np.prod(1 + vals) ** (252 / len(vals)) - 1)

annualize = F.udf(annualize_udf, DoubleType())

agg_exprs = []
for col in prices_spark.columns:
    if col.endswith('_return'):
        agg_exprs.append(annualize(F.collect_list(F.col(col))).alias(col.replace('_return', '')))

annualized_returns = returns_spark.agg(*agg_exprs)

annualized_returns = annualized_returns.withColumn('date', F.lit(returns_spark.agg(F.max('date')).first()[0]))

# --- 3. Handle empty tables by creating error rows if needed ---

# Macro variables (should be set externally or passed as arguments)
# dir: directory path to data
# keep: whether to keep temp tables (boolean)

error_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

if annualized_returns.count() == 0:

    error_data = [(-1, -999, -999, -999, -999, -999)]

    annualized_returns = spark.createDataFrame(error_data, error_schema)

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_from_r = spark.createDataFrame(error_data, error_schema)

# --- 4. Keep only the last row in annualized_returns ---

window_last = Window.orderBy(F.col('date').desc())

annualized_returns = annualized_returns.withColumn('rn', F.row_number().over(window_last)).filter(F.col('rn') == 1).drop('rn')

# --- 1. Read prices CSV as pandas DataFrame and calculate annualized returns (reference) ---

def fuzz(x, y):
    return abs(x - y) > 1e-8 if x is not None and y is not None else False

fuzz_udf = F.udf(fuzz, BooleanType())

for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    diff = diff.withColumn(f'{col}_DIF', fuzz_udf(F.col(f'{col}_r'), F.col(f'{col}_a')))

# --- 6. Count differences and set pass/notes variables ---

prices_path = os.path.join(dir, 'prices.csv')

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ANNUALIZED_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ANNUALIZED_TEST1')

# --- 7. Clean up temporary tables if keep==False ---
if not keep:
    for view_name in ['diff', 'prices_spark', 'annualized_returns', 'returns_from_r']:
        try:
            spark.catalog.dropTempView(view_name)
        except Exception:
            pass

prices_pd = pd.read_csv(prices_path, parse_dates=['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

annualized_returns_pd = (1 + returns_pd).prod() ** (252 / returns_pd.shape[0]) - 1

cols_order = ['date'] + [col for col in annualized_returns_pd.columns if col != 'date']

returns_from_r = spark.createDataFrame(annualized_returns_pd)

if returns_from_r.count() == 0:

# --- 5. Compare returns_from_r and annualized_returns, output differences ---

diff = returns_from_r.join(annualized_returns, on='date', how='inner', suffixes=('_r', '_a'))

diff_filtered = diff.filter(
    F.col('IBM_DIF') | F.col('GE_DIF') | F.col('DOW_DIF') | F.col('GOOGL_DIF') | F.col('SPY_DIF')
)

n = diff_filtered.count()

if n == 0:

annualized_returns_pd = annualized_returns_pd.to_frame().T
annualized_returns_pd['date'] = returns_pd.index.max()
