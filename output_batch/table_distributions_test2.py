# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

def compute_distributions(df, scale=252):

    stats = [
        'Mean', 'Std Dev', 'Scaled Std Dev', 'Skewness', 'Kurtosis', 'Min', 'Max', 'Median'
    ]

    data = []
    for col in df.columns:

        mean = df[col].mean()

        std = df[col].std()

        scaled_std = std * np.sqrt(scale)

        skew = df[col].skew()

        kurt = df[col].kurt()

        minv = df[col].min()

        maxv = df[col].max()

        median = df[col].median()
        data.append([mean, std, scaled_std, skew, kurt, minv, maxv, median])

    data = np.array(data).T

    result = pd.DataFrame(data, columns=df.columns)
    result.insert(0, '_stat_', stats)
    return result

# Convert pandas DataFrames to Spark DataFrames

    returns_from_r = None

# Create error DataFrames if needed

    error_data = [(-999, -999, -999, -999, -999, '_stat_')]

    error_data = [(999, 999, 999, 999, 999, '_stat_')]

# Update _stat_ value if needed

returns_from_r = returns_from_r.withColumn(
    '_stat_',
    F.when(returns_from_r['_stat_'] == 'Monthly Std Dev', 'Scaled Std Dev').otherwise(returns_from_r['_stat_'])
)

# Sort DataFrames by _stat_

returns_from_r = returns_from_r.orderBy('_stat_')

# Read prices CSV as Spark DataFrame

distribution_table = distribution_table.orderBy('_stat_')

# Compare DataFrames and output differences

join_cols = ['_stat_']

diff = diff.filter(
    (F.col('IBM') > 5e-5) | (F.col('GE') > 5e-5) | (F.col('DOW') > 5e-5) |
    (F.col('GOOGL') > 5e-5) | (F.col('SPY') > 5e-5)
)

# Handle skewness special case

diff = diff.withColumn('sum_abs', F.col('IBM') + F.col('GE') + F.col('DOW') + F.col('GOOGL') + F.col('SPY'))

diff = diff.filter(~((F.col('_stat_') == 'Sample skewness') & (F.col('sum_abs') < 5 * 5e-3)))

diff = diff.drop('sum_abs')

# Count number of differences

prices_path = os.path.join(dir, 'prices.csv')

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_distribution_TEST2')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_distribution_TEST2')

# Cleanup if keep == False
if not keep:

    prices_pdf = None

    returns_pdf = None

    returns_from_r = None

prices_pdf = pd.read_csv(prices_path)
prices_pdf.set_index(prices_pdf.columns[0], inplace=True)

    distribution_table = None

    diff = None

# Calculate log returns using pandas

returns_pdf = np.log(prices_pdf / prices_pdf.shift(1)).dropna()

distribution_table_pdf = compute_distributions(returns_pdf, scale=252)

returns_from_r = spark.createDataFrame(distribution_table_pdf)

distribution_table = spark.createDataFrame(distribution_table_pdf)

# Handle empty DataFrames
if distribution_table.count() == 0:

    distribution_table = None
if returns_from_r.count() == 0:

columns = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY', '_stat_']
if distribution_table is None:

    distribution_table = spark.createDataFrame(error_data, columns)
if returns_from_r is None:

    returns_from_r = spark.createDataFrame(error_data, columns)

diff = returns_from_r.alias('base').join(
    distribution_table.alias('compare'), on=join_cols, how='inner'
).select(
    'base._stat_',
    (F.abs(F.col('base.IBM') - F.col('compare.IBM')).alias('IBM')),
    (F.abs(F.col('base.GE') - F.col('compare.GE')).alias('GE')),
    (F.abs(F.col('base.DOW') - F.col('compare.DOW')).alias('DOW')),
    (F.abs(F.col('base.GOOGL') - F.col('compare.GOOGL')).alias('GOOGL')),
    (F.abs(F.col('base.SPY') - F.col('compare.SPY')).alias('SPY'))
)

n = diff.count()

# Macro variables (should be set externally or passed as arguments)
# n, dir, nv, keep

# Set pass/fail and notes
if n == 0:

# Compute distribution statistics
