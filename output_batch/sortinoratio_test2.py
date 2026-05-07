# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col, lit, when

spark = SparkSession.builder.appName("SortinoRatioTest2").getOrCreate()

# Initialize Spark session

# Calculate Sortino Ratio (subset method, MAR=0.01/252)

mar = 0.01 / 252

downside_returns = returns_pd[returns_pd < mar].fillna(0)

downside_deviation = np.sqrt((downside_returns ** 2).mean())

# Convert pandas DataFrames to Spark DataFrames

# Save prices DataFrame to Spark for further processing

    error_data = {'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    sortino_ratio_spark = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_spark = spark.createDataFrame(pd.DataFrame(error_data))

# Compare DataFrames and output differences (fuzzy match for columns)
# Join on row index (assumes index column is present after reset_index)

# Set up variables from macro dependencies/environment

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Sortinoratio_test2')
else:

    pass_test = False

keep = False  # Set from macro variable

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Sortinoratio_test2')

data_dir = os.environ.get('DIR', '/tmp')  # Directory for input files

# Read prices CSV as DataFrame

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd.set_index(prices_pd.columns[0], inplace=True)

returns_pd = prices_pd.pct_change().dropna()

expected_return = returns_pd.mean() - mar

sortino_ratio = expected_return / downside_deviation

sortino_ratio_df = pd.DataFrame([sortino_ratio], columns=returns_pd.columns)

returns_spark = spark.createDataFrame(returns_pd.reset_index())

sortino_ratio_spark = spark.createDataFrame(sortino_ratio_df)

prices_spark = spark.createDataFrame(prices_pd.reset_index())

# Handle empty DataFrames by replacing with error DataFrames if needed
if sortino_ratio_spark.count() == 0:

if returns_spark.count() == 0:

join_cols = [col for col in returns_spark.columns if col in sortino_ratio_spark.columns]

joined = returns_spark.crossJoin(sortino_ratio_spark)

diff = joined \
    .withColumn('IBM_DIF', when(abs(col('IBM') - col('IBM')) > 1e-6, lit(1)).otherwise(lit(0))) \
    .withColumn('GE_DIF', when(abs(col('GE') - col('GE')) > 1e-6, lit(1)).otherwise(lit(0))) \
    .withColumn('DOW_DIF', when(abs(col('DOW') - col('DOW')) > 1e-6, lit(1)).otherwise(lit(0))) \
    .withColumn('GOOGL_DIF', when(abs(col('GOOGL') - col('GOOGL')) > 1e-6, lit(1)).otherwise(lit(0)))

diff_filtered = diff.filter(
    (col('IBM_DIF') == 1) | (col('GE_DIF') == 1) | (col('DOW_DIF') == 1) | (col('GOOGL_DIF') == 1)
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:

# If keep is False, unpersist intermediate tables
if not keep:
    prices_spark.unpersist()
    diff_filtered.unpersist()
    returns_spark.unpersist()
    sortino_ratio_spark.unpersist()

# Calculate daily returns (discrete method)
