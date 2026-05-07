# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, Window, functions as F
from pyspark.sql.types import BooleanType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Convert pandas DataFrame to Spark DataFrame

# --- Spark Section: Calculate yearly returns ---

prices = prices.withColumn('date', F.to_date(F.col(prices.columns[0])))

# Calculate discrete returns for each column except 'date'

window_spec = Window.orderBy('date')

        lag_col = f'{col}_lag'

        ret_col = f'{col}_ret'

        prices = prices.withColumn(lag_col, F.lag(col).over(window_spec))

# Select only return columns and drop nulls

# Accumulate returns yearly (geometric)

agg_returns = agg_returns.withColumn('year', F.year('date'))
for col in return_cols:

    agg_returns = agg_returns.withColumn(col, F.col(col) + 1)

agg_returns = agg_returns.groupBy('year').agg(
    *[F.expr(f'product({col}) - 1').alias(col.replace('_ret', '')) for col in return_cols]
)

# Remove first row (mimicking firstobs=2)

agg_returns = agg_returns.orderBy('year')

# Set macro variables (replace with actual values as needed)

# --- Comparison Section ---
# Join on year/date and compare columns

def fuzz(x, y):
    return abs(x - y) > 1e-8 if x is not None and y is not None else True

# List of asset columns (update as needed)

for col in asset_cols:

    diff = diff.withColumn(
        f'fuzz_{col}',
        F.udf(fuzz, BooleanType())(F.col(f'{col}'), F.col(col))
    )

fuzz_cols = [f'fuzz_{col}' for col in asset_cols]

keep = False  # Set from macro variable

diff = diff.filter(F.reduce(lambda x, y: x | y, [F.col(c) for c in fuzz_cols]))

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ACCUMULATE_TEST3')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ACCUMULATE_TEST3')

# --- Cleanup Section ---
if not keep:
    for df_name in ['diff', 'prices', 'agg_returns', 'returns_from_r']:
        if spark.catalog._jcatalog.tableExists(df_name):
            spark.catalog.dropTempView(df_name)

dir_path = dir  # Set from macro variable

prices = spark.read.csv(os.path.join(dir_path, 'prices.csv'), header=True, inferSchema=True)

return_cols = []
for col in prices.columns:
    if col != 'date':

        prices = prices.withColumn(ret_col, (F.col(col) - F.col(lag_col)) / F.col(lag_col))
        return_cols.append(ret_col)

agg_returns = prices.select(['date'] + return_cols).dropna()

row_count = agg_returns.count()
if row_count > 1:

    agg_returns = agg_returns.limit(row_count - 1)

# --- Pandas Section: Calculate yearly returns (mimicking R logic) ---

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)

returns_pd = prices_pd.pct_change().dropna()
returns_pd.index = pd.to_datetime(returns_pd.index)

returns_yearly = returns_pd.add(1).groupby(returns_pd.index.year).prod() - 1
returns_yearly.reset_index(inplace=True)
returns_yearly.rename(columns={'index': 'date'}, inplace=True)

returns_from_r = spark.createDataFrame(returns_yearly)

diff = returns_from_r.join(agg_returns, returns_from_r['date'] == agg_returns['year'], 'outer')

asset_cols = [col for col in returns_from_r.columns if col != 'date']

n = diff.count()

if n == 0:
