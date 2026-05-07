# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, row_number, lit
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Convert pandas DataFrames to Spark DataFrames

# --- Handle empty DataFrames with error values ---

    error_data_cum = [(-1, -999, -999, -999, -999, -999)]

    error_data_ret = [(1, 999, 999, 999, 999, 999)]

    cumulative_returns = returns_from_r

window_spec = Window.orderBy(col('date').asc())

cumulative_returns = cumulative_returns.withColumn('rn', row_number().over(window_spec))

compare_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']
# Add suffixes to distinguish columns after join

# Calculate differences
for c in compare_cols:

    diff = diff.withColumn(f'diff_{c}', pyspark_abs(col(f"{c}_ret") - col(f"{c}_cum")))

# Define a fuzz function (tolerance for floating point comparison)

def fuzz(col1, col2, tol=1e-6):
    return pyspark_abs(col1 - col2) > tol

# Apply fuzz logic and filter differences

diff = diff.withColumn('_type_', lit('DIF'))

diff = diff.filter(
    (col('_type_') == 'DIF') & (
        fuzz(col('IBM_ret'), col('IBM_cum')) |
        fuzz(col('GE_ret'), col('GE_cum')) |
        fuzz(col('DOW_ret'), col('DOW_cum')) |
        fuzz(col('GOOGL_ret'), col('GOOGL_cum')) |
        fuzz(col('SPY_ret'), col('SPY_cum'))
    )
)

# --- Count number of differences and set pass/notes ---

# --- Read and preprocess prices data ---

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_CUMULATIVE_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_CUMULATIVE_TEST1')

# --- Clean up temporary DataFrames if keep is False ---
if not keep:
    for df_name in ['diff', 'prices_sdf', 'cumulative_returns', 'returns_from_r']:
        try:
            spark.catalog.dropTempView(df_name)
        except Exception:
            pass

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

prices_sdf = spark.createDataFrame(prices_pd.reset_index())

# Calculate discrete returns

returns_pd = prices_pd.pct_change().dropna()

cumulative_returns_pd = (1 + returns_pd).cumprod() - 1
cumulative_returns_pd.reset_index(inplace=True)

returns_from_r = spark.createDataFrame(cumulative_returns_pd)

error_schema = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']
if returns_from_r.count() == 0:

    cumulative_returns = spark.createDataFrame(error_data_cum, error_schema)

    returns_from_r = spark.createDataFrame(error_data_ret, error_schema)
else:

# --- Keep only the last row of cumulative_returns ---

max_rn = cumulative_returns.agg({'rn': 'max'}).collect()[0][0]

cumulative_returns = cumulative_returns.filter(col('rn') == max_rn).drop('rn')

# --- Compare returns_from_r and cumulative_returns (excluding date column) ---

cumulative_returns_alias = cumulative_returns.select(
    *[col(c).alias(f"{c}_cum") for c in compare_cols]
)

returns_from_r_alias = returns_from_r.select(
    *[col(c).alias(f"{c}_ret") for c in compare_cols]
)

# Cross join since only last row of cumulative_returns is kept

diff = returns_from_r_alias.crossJoin(cumulative_returns_alias)

n = diff.count()
if n == 0:

# Set variables from dependencies (assume these are provided in the environment)
# n, dir, nv, keep are assumed to be set externally

# Calculate cumulative returns (geometric)
