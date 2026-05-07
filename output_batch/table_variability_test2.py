# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Convert pandas DataFrames to Spark DataFrames

    error_data = {'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    variability_table = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_from_r = spark.createDataFrame(pd.DataFrame(error_data))

# Compare DataFrames: absolute difference > 1e-4 for any column

diff = diff.withColumn('IBM_DIF', pyspark_abs(col('IBM'))) \
           .withColumn('GE_DIF', pyspark_abs(col('GE'))) \
           .withColumn('DOW_DIF', pyspark_abs(col('DOW'))) \
           .withColumn('GOOGL_DIF', pyspark_abs(col('GOOGL'))) \
           .withColumn('SPY_DIF', pyspark_abs(col('SPY')))

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_variability_TEST2')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_variability_TEST2')

# Clean up temporary tables if keep is False
if not keep:
    for df_name in ['diff', 'prices_pd', 'returns_from_r', 'variability_table']:
        if df_name in locals():
            locals().pop(df_name)

# Read prices CSV as pandas DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)

# Calculate returns using pandas (discrete method)

returns_pd = prices_pd.pct_change().dropna()

variability_table_pd = returns_pd.agg(['std']).round(8)
variability_table_pd.index = ['Variability']

returns_from_r = spark.createDataFrame(returns_pd.reset_index(drop=True))

variability_table = spark.createDataFrame(variability_table_pd.reset_index(drop=True))

# Handle empty DataFrames by replacing with error DataFrames
if variability_table.count() == 0:

if returns_from_r.count() == 0:

diff = returns_from_r.join(variability_table, how='inner') \
    .select(
        (col('returns_from_r.IBM') - col('variability_table.IBM')).alias('IBM'),
        (col('returns_from_r.GE') - col('variability_table.GE')).alias('GE'),
        (col('returns_from_r.DOW') - col('variability_table.DOW')).alias('DOW'),
        (col('returns_from_r.GOOGL') - col('variability_table.GOOGL')).alias('GOOGL'),
        (col('returns_from_r.SPY') - col('variability_table.SPY')).alias('SPY')
    )

diff_filtered = diff.filter(
    (col('IBM_DIF') > 1e-4) |
    (col('GE_DIF') > 1e-4) |
    (col('DOW_DIF') > 1e-4) |
    (col('GOOGL_DIF') > 1e-4) |
    (col('SPY_DIF') > 1e-4)
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:

# Set variables from dependencies (assume these are provided in the environment)
# n, dir, nv, keep are assumed to be set externally

# Calculate variability table (standard deviation as proxy for table.Variability)
