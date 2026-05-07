# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from performanceanalytics import information_ratio, return_calculate  # Assume custom Python equivalents
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("Information_Ratio_Test2").getOrCreate()

# Initialize Spark session

# Calculate Information Ratio: first 4 columns vs 5th column (BM)

ir_pd = pd.DataFrame(ir_pd)

# Convert results back to Spark DataFrames

    returns_spark_df = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames: compute differences with fuzz logic

diff_df = diff_df.filter(
    (pyspark_abs(col('IBM_diff')) > 1e-6) |
    (pyspark_abs(col('GE_diff')) > 1e-6) |
    (pyspark_abs(col('DOW_diff')) > 1e-6) |
    (pyspark_abs(col('GOOGL_diff')) > 1e-6) |
    (pyspark_abs(col('SPY_diff')) > 1e-6)
)

# Count differences

    pass_flag = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Information_Ratio_TEST2')
else:

    pass_flag = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Information_Ratio_TEST2')

# Cleanup section (if keep is False)
if not keep:

# Read prices CSV as Spark DataFrame

    prices_df = None

    info_ratio_spark_df = None

    returns_spark_df = None

    diff_df = None

prices_path = f'{dir}/prices.csv'

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Convert to Pandas DataFrame for calculation

prices_pd = prices_df.toPandas()

# Calculate returns using discrete method and drop NA

returns_pd = return_calculate(prices_pd, method='discrete').dropna()

ir_pd = information_ratio(returns_pd.iloc[:, 0:4], returns_pd.iloc[:, 4], scale=1)

returns_spark_df = spark.createDataFrame(returns_pd.reset_index())

info_ratio_spark_df = spark.createDataFrame(ir_pd.reset_index(drop=True))

# Handle empty DataFrames by replacing with error DataFrames
if info_ratio_spark_df.count() == 0:

    info_ratio_spark_df = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_spark_df.count() == 0:

diff_df = returns_spark_df.join(info_ratio_spark_df, on='date', how='outer', suffixes=('_r', '_i')) \
    .select(
        col('date'),
        (col('IBM_r') - col('IBM_i')).alias('IBM_diff'),
        (col('GE_r') - col('GE_i')).alias('GE_diff'),
        (col('DOW_r') - col('DOW_i')).alias('DOW_diff'),
        (col('GOOGL_r') - col('GOOGL_i')).alias('GOOGL_diff'),
        (col('SPY_r') - col('SPY_i')).alias('SPY_diff')
    )

n = diff_df.count()

# Set pass/fail flags and print result
if n == 0:
