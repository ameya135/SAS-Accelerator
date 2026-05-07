# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, max as spark_max, monotonically_increasing_id

spark = SparkSession.builder.appName("StandardDeviationTest2").getOrCreate()

# Initialize Spark session

# Annualize standard deviation (scale=252)

annualized_stddev_pd = annualized_stddev_pd[['date'] + [c for c in annualized_stddev_pd.columns if c != 'date']]

# Convert pandas DataFrames to Spark DataFrames

    error_data = {'date': [-1], 'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    annualized_stddev_sdf = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'date': [1], 'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_sdf = spark.createDataFrame(pd.DataFrame(error_data))

# Keep only the last row of annualized_stddev_sdf

def fuzz(x, y, tol=1e-8):
    return abs(x - y) < tol

# Set variables from macro or environment

    pass_var = True

    notes_var = 'Passed'
    print('NOTE: NO ERROR IN TEST Standard_Deviation_test2')
else:

    pass_var = False

    notes_var = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST Standard_Deviation_test2')

keep = False if str('${keep}').upper() == 'FALSE' else True

# Clean up temporary DataFrames if keep is False
if not keep:

    returns_sdf = None

    annualized_stddev_sdf = None

dir_path = os.environ.get('dir', '${dir}')

# Read prices CSV as DataFrame

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pd = pd.read_csv(prices_path, parse_dates=True, index_col=0)

returns_pd = prices_pd.pct_change().dropna()

annualized_stddev_pd = returns_pd.std() * np.sqrt(252)

annualized_stddev_pd = annualized_stddev_pd.to_frame().T
annualized_stddev_pd['date'] = returns_pd.index.max()

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

annualized_stddev_sdf = spark.createDataFrame(annualized_stddev_pd)

# Handle empty DataFrames by replacing with error rows
if annualized_stddev_sdf.count() == 0:

if returns_sdf.count() == 0:

window_id = annualized_stddev_sdf.withColumn('row_id', monotonically_increasing_id())

max_row_id = window_id.agg(spark_max('row_id')).collect()[0][0]

annualized_stddev_sdf = window_id.filter(col('row_id') == max_row_id).drop('row_id')

# Compare returns_sdf and annualized_stddev_sdf using fuzz logic

returns_pd_last = returns_sdf.toPandas().iloc[[-1]].reset_index(drop=True)

annualized_stddev_pd_last = annualized_stddev_sdf.toPandas().reset_index(drop=True)

diff_rows = []
for colname in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:
    if not fuzz(returns_pd_last.at[0, colname], annualized_stddev_pd_last.at[0, colname]):
        diff_rows.append({'_type_': 'DIF', colname: True})

diff_count = len(diff_rows)

# Set pass/notes variables based on diff_count
if diff_count == 0:

# Calculate discrete returns using pandas
