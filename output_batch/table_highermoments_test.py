# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("HigherMomentsTest").getOrCreate()

# Initialize Spark session

def table_higher_moments(df):

    moments = {}
    for col_name in df.columns[1:]:

        col_data = df[col_name].dropna()
        moments[col_name] = {
            'mean': np.mean(col_data),
            'std': np.std(col_data, ddof=1),
            'skew': pd.Series(col_data).skew(),
            'kurt': pd.Series(col_data).kurt(),
        }
    return pd.DataFrame(moments).T

# Convert pandas DataFrames to Spark DataFrames

    error_data = [(asset, -999, -999, -999, -999) for asset in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]

    error_data = [(asset, 999, 999, 999, 999) for asset in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]

    returns_sdf = spark.createDataFrame(error_data, ['Asset', 'mean', 'std', 'skew', 'kurt'])

# Compare DataFrames (simulate SAS proc compare with absolute tolerance)

diff = diff.withColumn('mean_diff', pyspark_abs(col('base.mean') - col('compare.mean')))

diff = diff.withColumn('std_diff', pyspark_abs(col('base.std') - col('compare.std')))

diff = diff.withColumn('skew_diff', pyspark_abs(col('base.skew') - col('compare.skew')))

diff = diff.withColumn('kurt_diff', pyspark_abs(col('base.kurt') - col('compare.kurt')))

# Define file path for prices CSV

# Count number of differences

    pass_flag = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_HigherMoments_TEST')
else:

    pass_flag = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_HigherMoments_TEST')

prices_path = f'{dir}/prices.csv'

# Read prices CSV as pandas DataFrame

prices_pd = pd.read_csv(prices_path)

# Calculate discrete returns (PerformanceAnalytics::Return.calculate equivalent)

returns_pd = prices_pd.set_index(prices_pd.columns[0]).pct_change().dropna().reset_index()

higher_moments_pd = table_higher_moments(returns_pd)

returns_sdf = spark.createDataFrame(returns_pd)

higher_moments_sdf = spark.createDataFrame(higher_moments_pd.reset_index().rename(columns={'index': 'Asset'}))

# Handle empty DataFrames by creating error DataFrames
if higher_moments_sdf.count() == 0:

    higher_moments_sdf = spark.createDataFrame(error_data, ['Asset', 'mean', 'std', 'skew', 'kurt'])
if returns_sdf.count() == 0:

diff = higher_moments_sdf.alias('base').join(
    returns_sdf.alias('compare'),
    on='Asset',
    how='inner'
)

# Filter differences based on tolerance

diff_filtered = diff.filter(
    (col('mean_diff') > 1e-7) | 
    (col('std_diff') > 1e-3) | 
    (col('skew_diff') > 1e-3) | 
    (col('kurt_diff') > 1e-3)
)

n = diff_filtered.count()

# Set pass/fail flags and print result
if n == 0:

# Optionally drop intermediate DataFrames if keep==False
# (Assume 'keep' is defined elsewhere in the workflow)
# if not keep:
#     returns_sdf = None
#     higher_moments_sdf = None
#     diff = None
#     diff_filtered = None

# Calculate higher moments (mean, std, skew, kurtosis)
