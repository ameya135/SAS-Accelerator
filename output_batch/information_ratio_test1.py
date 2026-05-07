# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf
from pyspark.sql.types import BooleanType

spark = SparkSession.builder.appName("Information_Ratio_Test1").getOrCreate()

# Initialize Spark session

# Calculate Information Ratio: (mean(portfolio - benchmark) / std(portfolio - benchmark)) * sqrt(252)
# Assume first 4 columns are assets, 5th is benchmark (SPY)

# Convert pandas DataFrames to Spark DataFrames

# Read prices into Spark DataFrame (not used in logic, but kept for compatibility)

    returns_spark = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Define fuzz function for comparison (tolerance for floating point differences)

def fuzz(x, y, tol=1e-6):
    return abs(x - y) > tol if x is not None and y is not None else False

# Register UDF for fuzz

# Set variables from macro or environment

fuzz_udf = udf(fuzz, BooleanType())

# Filter differences where fuzz is True for any key column

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Information_Ratio_TEST1')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Information_Ratio_TEST1')

keep = False if str('${keep}').upper() == 'FALSE' else True

# Cleanup temporary tables if keep is False
if not keep:
    for df_name in ['diff_filtered', 'prices_spark', 'info_ratio_spark', 'returns_spark']:
        try:
            spark.catalog.dropTempView(df_name)
        except Exception:
            pass

dir_path = os.environ.get('dir', '${dir}')

prices_spark = spark.read.csv(os.path.join(dir_path, 'prices.csv'), header=True, inferSchema=True)

# Read prices.csv as pandas DataFrame for compatibility with PerformanceAnalytics logic

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'))
prices_pd.set_index(prices_pd.columns[0], inplace=True)

# Calculate discrete returns (mimicking Return.calculate in R)

returns_pd = prices_pd.pct_change().dropna()

portfolio_returns = returns_pd.iloc[:, 0:4]

benchmark_returns = returns_pd.iloc[:, 4]

excess_returns = portfolio_returns.subtract(benchmark_returns, axis=0)

info_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(252)

info_ratio_df = pd.DataFrame([info_ratio])
info_ratio_df.columns = portfolio_returns.columns

returns_spark = spark.createDataFrame(returns_pd.reset_index())

info_ratio_spark = spark.createDataFrame(info_ratio_df)

# Handle empty DataFrames by creating error DataFrames if needed
if info_ratio_spark.count() == 0:

    info_ratio_spark = spark.createDataFrame([{'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999}])
if returns_spark.count() == 0:

# Compare returns_spark and info_ratio_spark DataFrames
# Only compare columns that exist in both DataFrames

join_cols = [c for c in returns_spark.columns if c in info_ratio_spark.columns]

diff = returns_spark.alias('a').join(info_ratio_spark.alias('b'), on=join_cols, how='outer') \
    .select(*[col('a.'+c).alias(c+'_a') for c in join_cols], *[col('b.'+c).alias(c+'_b') for c in join_cols])

diff_filtered = diff.filter(
    fuzz_udf(col('IBM_a'), col('IBM_b')) |
    fuzz_udf(col('GE_a'), col('GE_b')) |
    fuzz_udf(col('DOW_a'), col('DOW_b')) |
    fuzz_udf(col('GOOGL_a'), col('GOOGL_b'))
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:
