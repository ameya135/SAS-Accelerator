# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("CalmarRatioTest2").getOrCreate()

# Initialize Spark session

def calmar_ratio(returns, scale=252):

    ann_return = (1 + returns.mean()) ** scale - 1

    cumulative = (1 + returns).cumprod()

    running_max = cumulative.cummax()

    drawdown = (cumulative - running_max) / running_max

# Calculate Calmar Ratio (annualized return / max drawdown)

    max_drawdown = drawdown.min()
    if max_drawdown == 0:
        return np.nan
    return ann_return / abs(max_drawdown)

# Compute Calmar Ratio for each column

calmar_df = calmar_df[['date'] + [c for c in calmar_df.columns if c != 'date']]

# Convert pandas DataFrames to Spark DataFrames

    error_data = {'date': [-1], 'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

    calmar_spark = spark.createDataFrame(pd.DataFrame(error_data))

    error_data = {'date': [1], 'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

# Set variables from macro or environment

    returns_spark = spark.createDataFrame(pd.DataFrame(error_data))

# Define fuzzy comparison function

def fuzz(x, y, tol=1e-6):
    return abs(x - y) > tol

# Join DataFrames on 'date' and compare columns

# Count number of differences

    pass_test = True

keep = False  # Set from macro or environment

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST CALMAR_RATIO_TEST2')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST CALMAR_RATIO_TEST2')

# Clean up temporary tables if keep is False
if not keep:

    diff = None

    calmar_spark = None

    returns_spark = None

data_dir = os.environ.get('dir', '/path/to/dir')

# Read prices.csv as pandas DataFrame

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

calmar_dict = {col_name: calmar_ratio(returns_pd[col_name]) for col_name in returns_pd.columns}

calmar_df = pd.DataFrame([calmar_dict])
calmar_df['date'] = returns_pd.index.max()

returns_spark = spark.createDataFrame(returns_pd.reset_index())

calmar_spark = spark.createDataFrame(calmar_df)

# Handle empty DataFrames by creating error DataFrames if needed
if calmar_spark.count() == 0:

if returns_spark.count() == 0:

joined = returns_spark.alias('r').join(calmar_spark.alias('c'), on='date', how='inner')

diff = joined.filter(
    fuzz(col('r.IBM'), col('c.IBM')) |
    fuzz(col('r.GE'), col('c.GE')) |
    fuzz(col('r.DOW'), col('c.DOW')) |
    fuzz(col('r.GOOGL'), col('c.GOOGL')) |
    fuzz(col('r.SPY'), col('c.SPY'))
)

n = diff.count()

# Set pass/fail and notes
if n == 0:

# Calculate discrete returns using pandas
