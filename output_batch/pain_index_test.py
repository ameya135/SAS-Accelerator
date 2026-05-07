# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("PainIndexTest").getOrCreate()

# ---------------------------
# Initialize Spark session
# ---------------------------

prices_pd = prices_pd.sort_values('date')

# ---------------------------
# Pain Index calculation (PerformanceAnalytics::PainIndex equivalent)
# ---------------------------

def pain_index(returns):

    cumulative = (returns + 1).cumprod()

    running_max = cumulative.cummax()

    drawdown = (cumulative - running_max) / running_max

    pain = drawdown.abs().mean()
    return pain

# Apply Pain Index to each column (excluding date)

# Create PainIndex DataFrame

# ---------------------------
# Convert pandas DataFrames to Spark DataFrames
# ---------------------------

    error_row = {'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    pain_index_sdf = spark.createDataFrame([error_row])

# ---------------------------
# Set up variables
# ---------------------------

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_sdf = spark.createDataFrame([error_row])

# ---------------------------
# Compare DataFrames: calculate difference for relevant columns
# ---------------------------

columns_to_compare = ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

diff_exprs = [
    pyspark_abs(col('returns_from_r.' + c) - col('PainIndex.' + c)).alias(c)
    for c in columns_to_compare
]

# ---------------------------
# Define a fuzz function (tolerance for floating point comparison)
# ---------------------------

def fuzz(col1, col2, tol=1e-6):
    return pyspark_abs(col1 - col2) > tol

dir_path = os.environ.get('DIR', '/path/to/dir')  # Update as needed

# ---------------------------
# Filter rows where any column difference is significant
# ---------------------------

# ---------------------------
# Count number of differences
# ---------------------------

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST PAIN_INDEX_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST PAIN_INDEX_TEST')

keep_tables = os.environ.get('KEEP', 'FALSE').upper() == 'TRUE'

# ---------------------------
# Read prices CSV as DataFrame
# ---------------------------

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pd = pd.read_csv(prices_path)
prices_pd['date'] = pd.to_datetime(prices_pd['date'])

returns_pd = prices_pd.set_index('date').pct_change().dropna()

pain_index_values = {col_name: pain_index(returns_pd[col_name]) for col_name in returns_pd.columns}

pain_index_df = pd.DataFrame([pain_index_values])
pain_index_df['date'] = returns_pd.index.max()

pain_index_df = pain_index_df[['date'] + list(pain_index_values.keys())]

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

pain_index_sdf = spark.createDataFrame(pain_index_df)

# ---------------------------
# Save intermediate tables if keep_tables is True
# ---------------------------
if keep_tables:
    returns_sdf.write.mode('overwrite').parquet(os.path.join(dir_path, 'returns_from_r.parquet'))
    pain_index_sdf.write.mode('overwrite').parquet(os.path.join(dir_path, 'PainIndex.parquet'))

# ---------------------------
# Check if DataFrames are empty, create error rows if needed
# ---------------------------
if pain_index_sdf.count() == 0:

if returns_sdf.count() == 0:

joined = returns_sdf.alias('returns_from_r').join(
    pain_index_sdf.alias('PainIndex'), on='date', how='inner'
)

diff = joined.select('date', *diff_exprs)

diff_filtered = diff.where(
    (fuzz(col('returns_from_r.IBM'), col('PainIndex.IBM'))) |
    (fuzz(col('returns_from_r.GE'), col('PainIndex.GE'))) |
    (fuzz(col('returns_from_r.DOW'), col('PainIndex.DOW'))) |
    (fuzz(col('returns_from_r.GOOGL'), col('PainIndex.GOOGL'))) |
    (fuzz(col('returns_from_r.SPY'), col('PainIndex.SPY')))
)

n_diff = diff_filtered.count()

# ---------------------------
# Set pass/notes variables based on comparison
# ---------------------------
if n_diff == 0:

# ---------------------------
# Clean up temporary tables if keep_tables is False
# ---------------------------
if not keep_tables:
    returns_sdf.unpersist()
    pain_index_sdf.unpersist()
    diff_filtered.unpersist()

# ---------------------------
# Calculate returns (discrete method) in pandas
# ---------------------------
