# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName('TableUpDownRatiosTest').getOrCreate()

# Initialize Spark session

def table_updown_ratios(returns, bm_col):

    bm = returns.iloc[:, bm_col]

    up = (returns > 0).sum()

    down = (returns < 0).sum()

    up_bm = (bm > 0).sum()

    down_bm = (bm < 0).sum()

    ratios = (up / up_bm) / (down / down_bm)
    return pd.DataFrame([ratios], columns=returns.columns)

# Compute up/down ratios using the 5th column as benchmark

# Convert pandas DataFrames to Spark DataFrames

    error_row = {'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    TableUpDownRatios = spark.createDataFrame([error_row])

    error_row = {'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r = spark.createDataFrame([error_row])

# Define file paths and macro variables

# Define fuzz function for float comparison

def fuzz(col1, col2, tol=1e-6):
    return F.abs(col1 - col2) > tol

# Compare DataFrames and output differences

# Add difference columns

diff = diff.withColumn('IBM_DIF', fuzz(F.col('r.IBM'), F.col('t.IBM')))

diff = diff.withColumn('GE_DIF', fuzz(F.col('r.GE'), F.col('t.GE')))

diff = diff.withColumn('DOW_DIF', fuzz(F.col('r.DOW'), F.col('t.DOW')))

diff = diff.withColumn('GOOGL_DIF', fuzz(F.col('r.GOOGL'), F.col('t.GOOGL')))

# Filter rows with any differences

data_dir = os.environ.get('dir', '/tmp')

# Count number of differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST TableUpDownRatios_test')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST TableUpDownRatios_test')

keep = os.environ.get('keep', 'FALSE')

prices_csv_path = os.path.join(data_dir, 'prices.csv')

# Read prices.csv into a pandas DataFrame

prices_pdf = pd.read_csv(prices_csv_path)
prices_pdf.set_index(prices_pdf.columns[0], inplace=True)
prices_pdf.index = pd.to_datetime(prices_pdf.index)

returns_pdf = prices_pdf.pct_change().dropna()

returns_from_r_pdf = table_updown_ratios(returns_pdf, 4)  # 0-based index, 5th col is index 4
returns_from_r_pdf.index = [0]

TableUpDownRatios_pdf = returns_from_r_pdf.copy()

returns_from_r = spark.createDataFrame(returns_from_r_pdf.reset_index(drop=True))

TableUpDownRatios = spark.createDataFrame(TableUpDownRatios_pdf.reset_index(drop=True))

# Handle empty DataFrames by replacing with error rows
if TableUpDownRatios.count() == 0:

if returns_from_r.count() == 0:

diff = returns_from_r.alias('r').join(
    TableUpDownRatios.alias('t'),
    on=['IBM', 'GE', 'DOW', 'GOOGL', 'SPY'],
    how='outer'
)

diff_filtered = diff.filter(
    F.col('IBM_DIF') | F.col('GE_DIF') | F.col('DOW_DIF') | F.col('GOOGL_DIF')
)

n = diff_filtered.count()

# Set pass/fail and notes based on comparison
if n == 0:

# Clean up temporary DataFrames if keep is FALSE
if keep == 'FALSE':
    returns_from_r.unpersist()
    TableUpDownRatios.unpersist()
    diff.unpersist()
    diff_filtered.unpersist()

# Calculate discrete returns
