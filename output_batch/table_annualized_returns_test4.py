# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import DoubleType, IntegerType, StructField, StructType

spark = SparkSession.builder.appName("AnnualizedReturnsTest4").getOrCreate()

# Initialize Spark session

# Annualized returns calculation (geometric=FALSE, scale=12, Rf=0.01/12, digits=6)

Rf = 0.01 / 12

scale = 12

def annualized_returns(df, Rf=Rf, scale=scale, digits=6):

    mean_ret = df.mean()

    ann_ret = (mean_ret - Rf) * scale
    return ann_ret.round(digits)

annualized_table_pd = annualized_table_pd.to_frame().T
annualized_table_pd['date'] = -1

annualized_table_pd = annualized_table_pd[['date'] + [col for col in annualized_table_pd.columns if col != 'date']]

# Convert pandas DataFrames to Spark DataFrames

# If tables have 0 records, create default rows

schema = StructType([
    StructField('date', IntegerType(), True),
    StructField('IBM', DoubleType(), True),
    StructField('GE', DoubleType(), True),
    StructField('DOW', DoubleType(), True),
    StructField('GOOGL', DoubleType(), True),
    StructField('SPY', DoubleType(), True)
])

    annualized_spark = spark.createDataFrame([(-1, -999.0, -999.0, -999.0, -999.0, -999.0)], schema=schema)

    returns_spark = spark.createDataFrame([(1, 999.0, 999.0, 999.0, 999.0, 999.0)], schema=schema)

# Compare DataFrames: absolute difference, filter where any col > 1e-4

    diff = diff.withColumn(f'diff_{col}', F.abs(F.col(f'a.{col}') - F.col(f'r.{col}')))

diff = diff.filter(
    (F.col('diff_IBM') > 1e-4) |
    (F.col('diff_GE') > 1e-4) |
    (F.col('diff_DOW') > 1e-4) |
    (F.col('diff_GOOGL') > 1e-4) |
    (F.col('diff_SPY') > 1e-4)
)

# Count differences and set test result

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_Annualized_Returns_TEST4')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_Annualized_Returns_TEST4')

input_dir = os.environ.get('dir', '/path/to/dir')

    prices_pd = None

    returns_pd = None

    returns_spark = None

    annualized_spark = None

    diff = None

keep = os.environ.get('keep', 'FALSE').upper() == 'TRUE'

# Set up input directory and keep flag from environment variables

# Cleanup if keep is False
if not keep:

# Read prices.csv as pandas DataFrame

prices_path = os.path.join(input_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = np.log(prices_pd / prices_pd.shift(1)).dropna()

annualized_table_pd = annualized_returns(returns_pd)

returns_spark = spark.createDataFrame(returns_pd.reset_index())

annualized_spark = spark.createDataFrame(annualized_table_pd)

if annualized_spark.count() == 0:

if returns_spark.count() == 0:

diff = annualized_spark.alias('a').join(
    returns_spark.alias('r'),
    on=['date'],
    how='outer'
)
for col in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

n = diff.count()
if n == 0:

# Calculate log returns using pandas
