# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col

spark = SparkSession.builder.appName("SortinoRatioTest1").getOrCreate()

# === Configuration / Macro Variables (set externally or above) ===
# dir: directory containing 'prices.csv'
# keep: whether to keep intermediate Spark tables (True/False)

mar = 0.01 / 252

# === Convert Pandas DataFrames to Spark DataFrames ===

# === Read prices into Spark DataFrame (if needed elsewhere) ===

# === Initialize Spark Session ===

    error_data = {'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    sortino_ratio_spark = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_spark = spark.createDataFrame(pd.DataFrame(error_data))

def fuzz(col1, col2):
    return spark_abs(col1 - col2) > 1e-6

join_cols = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# Check for differences in each column

# === Count Differences ===

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST Sortinoratio_test1')
else:

    pass_var = False

# === Read prices.csv as Pandas DataFrame ===

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Sortinoratio_test1')

prices_path = os.path.join(dir, 'prices.csv')

prices_spark = spark.read.csv(prices_path, header=True, inferSchema=True)

prices_pd = pd.read_csv(prices_path)
prices_pd.set_index(prices_pd.columns[0], inplace=True)

# === Calculate Returns (Pandas) ===

returns_pd = prices_pd.pct_change().dropna()

downside_returns = np.where(returns_pd < mar, returns_pd - mar, 0)

downside_deviation = np.sqrt((downside_returns ** 2).mean())

mean_return = returns_pd.mean()

sortino_ratio = (mean_return - mar) / downside_deviation

sortino_ratio_df = pd.DataFrame([sortino_ratio], columns=returns_pd.columns)

returns_spark = spark.createDataFrame(returns_pd.reset_index())

sortino_ratio_spark = spark.createDataFrame(sortino_ratio_df)

# === Handle Empty DataFrames by Creating Error DataFrames ===
if sortino_ratio_spark.count() == 0:

if returns_spark.count() == 0:

joined = returns_spark.join(
    sortino_ratio_spark,
    on=join_cols,
    how='outer',
    suffixes=('_r', '_s')
)

# Join on all columns present in both DataFrames

diff = joined.filter(
    fuzz(col('IBM_r'), col('IBM_s')) |
    fuzz(col('GE_r'), col('GE_s')) |
    fuzz(col('DOW_r'), col('DOW_s')) |
    fuzz(col('GOOGL_r'), col('GOOGL_s')) |
    fuzz(col('SPY_r'), col('SPY_s'))
)

# === Compare DataFrames and Output Differences (fuzz logic: abs diff > 1e-6) ===

n = diff.count()

# === Set Pass/Notes Variables and Print Result ===
if n == 0:

# === Optionally Unpersist Intermediate Tables ===
if not keep:
    prices_spark.unpersist()
    diff.unpersist()
    returns_spark.unpersist()
    sortino_ratio_spark.unpersist()

# === Calculate Sortino Ratio (MAR=0.01/252) ===
