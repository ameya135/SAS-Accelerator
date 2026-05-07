# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName("DownsideRiskTest2").getOrCreate()

# Initialize Spark session

# Calculate discrete returns using pandas for accuracy

# Calculate Downside Deviation (MAR=0.01/252, method='full')

MAR = 0.01 / 252

def downside_deviation(returns, mar):

    downside = np.where(returns < mar, returns - mar, 0)
    return np.sqrt(np.mean(downside ** 2))

# Calculate downside risk for each row and asset

        dd = downside_deviation(np.array([row[colname]]), MAR)
        downside_risk_dict[colname].append(dd)

# Convert returns and downside risk to Spark DataFrames

    error_data = [(-1, -999, -999, -999, -999, -999)]

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_sdf = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

# Set variables from macro or environment

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST DOWNSIDE_RISK_TEST2')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST DOWNSIDE_RISK_TEST2')

    diff = None

keep = False  # Set from macro or parameter

# If keep is False, drop intermediate DataFrames
if not keep:

    prices_sdf = None

    returns_sdf = None

    downside_risk_sdf = None

data_dir = os.environ.get('dir', '/tmp')  # Directory path

# Read prices.csv as Pandas DataFrame

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])

prices_sdf = spark.createDataFrame(prices_pd)

returns_pd = prices_pd.set_index('date').pct_change().dropna().reset_index()

downside_risk_dict = {'date': [], 'IBM': [], 'GE': [], 'DOW': [], 'GOOGL': [], 'SPY': []}
for idx, row in returns_pd.iterrows():
    downside_risk_dict['date'].append(row['date'])
    for colname in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

downside_risk_pd = pd.DataFrame(downside_risk_dict)

returns_sdf = spark.createDataFrame(returns_pd)

downside_risk_sdf = spark.createDataFrame(downside_risk_pd)

# If tables have 0 records, replace with error rows as in SAS
if downside_risk_sdf.count() == 0:

    downside_risk_sdf = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])
if returns_sdf.count() == 0:

# Compare returns_sdf and downside_risk_sdf for differences

diff = (
    returns_sdf.alias('a')
    .join(downside_risk_sdf.alias('b'), on='date', how='outer')
    .select(
        col('a.date'),
        (abs(col('a.IBM') - col('b.IBM')) > 1e-8).alias('IBM_diff'),
        (abs(col('a.GE') - col('b.GE')) > 1e-8).alias('GE_diff'),
        (abs(col('a.DOW') - col('b.DOW')) > 1e-8).alias('DOW_diff'),
        (abs(col('a.GOOGL') - col('b.GOOGL')) > 1e-8).alias('GOOGL_diff'),
        (abs(col('a.SPY') - col('b.SPY')) > 1e-8).alias('SPY_diff')
    )
    .filter(
        col('IBM_diff') | col('GE_diff') | col('DOW_diff') | col('GOOGL_diff') | col('SPY_diff')
    )
)

n = diff.count()

# Set pass/fail and notes
if n == 0:

# Convert to Spark DataFrame
