# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

spark = SparkSession.builder.appName("Sterling_Ratio_Test2").getOrCreate()

# Initialize Spark session

# Calculate Sterling Ratio (scale=12, excess=0.1/12)

def sterling_ratio(returns_df, scale=12, excess=0.1/12):
    # Calculate rolling max drawdown

    rolling_max = returns_df.drop('date', axis=1).cummax()

    drawdown = (returns_df.drop('date', axis=1) - rolling_max) / rolling_max

    max_drawdown = drawdown.min()
    # Calculate annualized return

    ann_return = (1 + returns_df.drop('date', axis=1)).prod() ** (scale / len(returns_df)) - 1
    # Sterling Ratio calculation

    sr = (ann_return - excess) / abs(max_drawdown)

    sr_df = pd.DataFrame([sr], columns=returns_df.columns[1:])
    sr_df.insert(0, 'date', returns_df['date'].iloc[-1])
    return sr_df

# Convert pandas DataFrames to Spark DataFrames

    error_data = [(-1, -999, -999, -999, -999, -999)]

    error_data = [(1, 999, 999, 999, 999, 999)]

    returns_sdf = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])

# Compare DataFrames by date and columns, output differences where fuzz detected

def fuzz(x, y, tol=1e-6):
    return abs(x - y) > tol

# Set up file paths and macro variables

# Join DataFrames on 'date'

# Check for differences using fuzz function

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST STERLING_RATIO_TEST2')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST STERLING_RATIO_TEST2')

keep = keep if 'keep' in locals() else False

# Optionally clean up intermediate DataFrames if keep is False
if not keep:

    returns_sdf = None

    sterling_ratio_sdf = None

    diff = None

dir_path = dir if 'dir' in locals() else '/tmp'

# Read prices CSV into pandas DataFrame

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pdf = pd.read_csv(prices_path)
prices_pdf['date'] = pd.to_datetime(prices_pdf['date'])

returns_pdf = prices_pdf.set_index('date').pct_change().dropna().reset_index()

sterling_ratio_pdf = sterling_ratio(returns_pdf, scale=12, excess=0.1/12)

returns_sdf = spark.createDataFrame(returns_pdf)

sterling_ratio_sdf = spark.createDataFrame(sterling_ratio_pdf)

# Handle empty DataFrames by replacing with error DataFrames
if sterling_ratio_sdf.count() == 0:

    sterling_ratio_sdf = spark.createDataFrame(error_data, ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY'])
if returns_sdf.count() == 0:

joined = returns_sdf.alias('r').join(sterling_ratio_sdf.alias('s'), on='date', how='inner')

diff = joined.where(
    (fuzz(col('r.IBM'), col('s.IBM'))) |
    (fuzz(col('r.GE'), col('s.GE'))) |
    (fuzz(col('r.DOW'), col('s.DOW'))) |
    (fuzz(col('r.GOOGL'), col('s.GOOGL'))) |
    (fuzz(col('r.SPY'), col('s.SPY')))
)

n = diff.count()

if n == 0:

# Calculate returns (discrete method)
