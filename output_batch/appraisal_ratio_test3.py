# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName("AppraisalRatioTest3").getOrCreate()

# Initialize Spark session

# Calculate Appraisal Ratio (Rf=0.01/252)

rf = 0.01 / 252

benchmark_col = 'SPY'  # Assuming SPY is the benchmark column

def appraisal_ratio(asset_returns, benchmark_returns, rf):

    excess_asset = asset_returns - rf

    excess_benchmark = benchmark_returns - rf

    tracking_error = np.std(excess_asset - excess_benchmark, ddof=1)

    ar = (excess_asset.mean() - excess_benchmark.mean()) / tracking_error if tracking_error != 0 else np.nan
    return ar

appraisal_ratios = {}
for asset in asset_cols:

    ar = appraisal_ratio(returns_pdf[asset], returns_pdf[benchmark_col], rf)
    appraisal_ratios[asset] = ar

# Prepare Appraisal Ratio DataFrame

# Convert pandas DataFrames to Spark DataFrames

    error_data = {'date': [-1], 'IBM': [-999], 'GE': [-999], 'DOW': [-999], 'GOOGL': [-999], 'SPY': [-999]}

# Set up variables from dependencies (replace with actual values as needed)

    error_data = {'date': [1], 'IBM': [999], 'GE': [999], 'DOW': [999], 'GOOGL': [999], 'SPY': [999]}

    returns_sdf = spark.createDataFrame(pd.DataFrame(error_data))

diff = diff.withColumn('DIF', (
    (abs(col('IBM')) > 1e-6) |
    (abs(col('GE')) > 1e-6) |
    (abs(col('DOW')) > 1e-6) |
    (abs(col('GOOGL')) > 1e-6)
))

# Count number of differences

    pass_test = True

keep = False  # Set from macro variable or config

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST APPRAISAL_RATIO_TEST3')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST APPRAISAL_RATIO_TEST3')

# Optionally clean up intermediate DataFrames if not keeping
if not keep:

    returns_sdf = None

    appraisal_ratio_sdf = None

    diff = None

    diff_filtered = None

data_dir = 'your_data_directory'  # Set from macro variable or config

# Read prices CSV as DataFrame

prices_pdf = pd.read_csv(f'{data_dir}/prices.csv')
prices_pdf.set_index('date', inplace=True)

# Calculate discrete returns using pandas

returns_pdf = prices_pdf.pct_change().dropna()

asset_cols = [c for c in returns_pdf.columns if c != benchmark_col]

appraisal_ratio_pdf = pd.DataFrame([appraisal_ratios])
appraisal_ratio_pdf['date'] = returns_pdf.index[-1]
appraisal_ratio_pdf[benchmark_col] = np.nan

appraisal_ratio_pdf = appraisal_ratio_pdf[['date'] + asset_cols + [benchmark_col]]

returns_sdf = spark.createDataFrame(returns_pdf.reset_index())

appraisal_ratio_sdf = spark.createDataFrame(appraisal_ratio_pdf)

# Handle empty DataFrames by replacing with error DataFrames
if appraisal_ratio_sdf.count() == 0:

    appraisal_ratio_sdf = spark.createDataFrame(pd.DataFrame(error_data))
if returns_sdf.count() == 0:

diff = returns_sdf.alias('base').join(appraisal_ratio_sdf.alias('compare'), on='date', how='inner') \
    .select(
        col('base.date'),
        *(abs(col(f'base.{c}') - col(f'compare.{c}')).alias(c) for c in ['IBM', 'GE', 'DOW', 'GOOGL'])
    )

# Compare DataFrames and output differences (fuzz logic: abs diff > 1e-6)

diff_filtered = diff.filter(col('DIF'))

n = diff_filtered.count()

# Set pass/notes variables based on comparison
if n == 0:
