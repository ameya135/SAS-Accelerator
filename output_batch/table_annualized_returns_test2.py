# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F, types as T

spark = SparkSession.builder.appName("AnnualizedReturnsTest2").getOrCreate()

# Initialize Spark session

# Annualized returns calculation

def annualized_return(returns, rf=0.01, scale=1, geometric=True, digits=8):
    if geometric:

        ann_ret = ((1 + returns).prod() ** (scale / len(returns))) - 1
    else:

        ann_ret = returns.mean() * scale
    return np.round(ann_ret, digits)

# Compute annualized returns for each column

annualized_table_pd = pd.DataFrame([annualized_table_dict])
annualized_table_pd['date'] = -1

cols = ['date'] + [c for c in annualized_table_pd.columns if c != 'date']

annualized_table_pd = annualized_table_pd[cols]

# Prepare returns DataFrame for Spark

# Convert pandas DataFrames to Spark DataFrames

annualized_table = spark.createDataFrame(annualized_table_pd)

# Handle empty DataFrames by creating error rows
if annualized_table.count() == 0:

    error_schema = T.StructType([
        T.StructField('date', T.IntegerType(), True),
        T.StructField('IBM', T.IntegerType(), True),
        T.StructField('GE', T.IntegerType(), True),
        T.StructField('DOW', T.IntegerType(), True),
        T.StructField('GOOGL', T.IntegerType(), True),
        T.StructField('SPY', T.IntegerType(), True)
    ])

    annualized_table = spark.createDataFrame([(-1, -999, -999, -999, -999, -999)], schema=error_schema)

    error_schema = T.StructType([
        T.StructField('date', T.IntegerType(), True),
        T.StructField('IBM', T.IntegerType(), True),
        T.StructField('GE', T.IntegerType(), True),
        T.StructField('DOW', T.IntegerType(), True),
        T.StructField('GOOGL', T.IntegerType(), True),
        T.StructField('SPY', T.IntegerType(), True)
    ])

    returns_from_r = spark.createDataFrame([(1, 999, 999, 999, 999, 999)], schema=error_schema)

# Compare DataFrames: absolute difference, filter where any col > 1e-4

# Count differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_Annualized_Returns_TEST2')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_Annualized_Returns_TEST2')

input_dir = os.environ.get('dir', '/path/to/dir')

    diff = None

    annualized_table = None

    returns_from_r = None

keep = os.environ.get('keep', 'FALSE').upper() == 'TRUE'

# Set up input directory and keep flag from environment variables

# Clean up temporary DataFrames if keep is False
if not keep:

# Read prices CSV as pandas DataFrame

prices_path = os.path.join(input_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path, parse_dates=['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

annualized_table_dict = {
    col: annualized_return(returns_pd[col], rf=0.01, scale=1, geometric=True, digits=8)
    for col in returns_pd.columns
}

returns_from_r_pd = returns_pd.copy()
returns_from_r_pd.reset_index(inplace=True)

returns_from_r = spark.createDataFrame(returns_from_r_pd)

if returns_from_r.count() == 0:

diff = (
    returns_from_r.join(annualized_table, on='date', how='inner', suffixes=('_r', '_a'))
    .withColumn('IBM_DIF', F.abs(F.col('IBM_r') - F.col('IBM_a')))
    .withColumn('GE_DIF', F.abs(F.col('GE_r') - F.col('GE_a')))
    .withColumn('DOW_DIF', F.abs(F.col('DOW_r') - F.col('DOW_a')))
    .withColumn('GOOGL_DIF', F.abs(F.col('GOOGL_r') - F.col('GOOGL_a')))
    .withColumn('SPY_DIF', F.abs(F.col('SPY_r') - F.col('SPY_a')))
    .filter(
        (F.col('IBM_DIF') > 1e-4) |
        (F.col('GE_DIF') > 1e-4) |
        (F.col('DOW_DIF') > 1e-4) |
        (F.col('GOOGL_DIF') > 1e-4) |
        (F.col('SPY_DIF') > 1e-4)
    )
)

n = diff.count()

# Set pass/notes variables and print result
if n == 0:

# Calculate discrete returns using pandas
