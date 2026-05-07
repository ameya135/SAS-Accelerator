# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col

spark = SparkSession.builder.appName("DrawdownDeviationTest").getOrCreate()

# Initialize Spark session

# Drawdown Deviation calculation (using pandas)

def drawdown_deviation(returns):

    cumulative = (1 + returns).cumprod()

    highwater = cumulative.cummax()

    drawdowns = (cumulative - highwater) / highwater
    return drawdowns.std()

# Calculate drawdown deviation for each column

dd_dev_pd = pd.DataFrame([dd_dev_dict])

# Convert pandas DataFrames to Spark DataFrames

dd_dev_sdf = spark.createDataFrame(dd_dev_pd)

# Handle empty DataFrames by inserting default rows
if dd_dev_sdf.count() == 0:

    returns_sdf = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames: find differences using a cross join and tolerance logic

def fuzz(a, b, tol=1e-6):
    return spark_abs(a - b) > tol

# Set variables from macro or environment

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST DRAWDOWN_DEVIATION_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST DRAWDOWN_DEVIATION_TEST')

keep = False  # Set from macro or parameter

# Cleanup if keep is False (no explicit deletion needed in Python)

data_dir = os.environ.get('dir', '/path/to/dir')

# Load prices CSV as Pandas DataFrame

prices_path = os.path.join(data_dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])
prices_pd.set_index('date', inplace=True)

returns_pd = prices_pd.pct_change().dropna()

dd_dev_dict = {col_name: drawdown_deviation(returns_pd[[col_name]])[0] for col_name in returns_pd.columns}

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

    dd_dev_sdf = spark.createDataFrame([{'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_sdf.count() == 0:

joined = returns_sdf.alias('r').crossJoin(dd_dev_sdf.alias('d'))

diff = joined.where(
    fuzz(col('r.IBM'), col('d.IBM')) |
    fuzz(col('r.GE'), col('d.GE')) |
    fuzz(col('r.DOW'), col('d.DOW')) |
    fuzz(col('r.GOOGL'), col('d.GOOGL')) |
    fuzz(col('r.SPY'), col('d.SPY'))
)

n = diff.count()

# Output test result
if n == 0:

# Calculate discrete returns using pandas
