# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs, col

spark = SparkSession.builder.appName("DownsideRiskTest3").getOrCreate()

# Initialize Spark session

# Calculate Downside Deviation (MAR=0.01/252, method='subset')

mar = 0.01 / 252

def downside_deviation(returns, mar):

    downside = np.where(returns < mar, returns - mar, 0)
    return np.sqrt(np.mean(downside ** 2, axis=0))

# Convert pandas DataFrames to Spark DataFrames

# If DownsideRisk does not exist, create error row
if 'DownsideRisk' not in [t.name for t in spark.catalog.listTables()]:

    error_row = pd.DataFrame([{'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999, 'date': -1}])

    downside_dev_sdf = spark.createDataFrame(error_row)
    downside_dev_sdf.createOrReplaceTempView('DownsideRisk')

# If returns_from_r does not exist, create error row
if 'returns_from_r' not in [t.name for t in spark.catalog.listTables()]:

    error_row = pd.DataFrame([{'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999, 'date': 1}])

    returns_sdf = spark.createDataFrame(error_row)
    returns_sdf.createOrReplaceTempView('returns_from_r')

# Compare returns_from_r and DownsideRisk for differences (fuzzy match)

returns_df = spark.sql('SELECT * FROM returns_from_r')

downside_dev_df = spark.sql('SELECT * FROM DownsideRisk')

# Set variables from macro or environment

join_cols = ['date']

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST DOWNSIDE_RISK_TEST3')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST DOWNSIDE_RISK_TEST3')

keep = keep if 'keep' in locals() else False

# Drop temp tables if keep is False
if not keep:
    spark.catalog.dropTempView('returns_from_r')
    spark.catalog.dropTempView('DownsideRisk')

dir_path = dir_path if 'dir_path' in locals() else '/tmp'

# Read prices CSV as Pandas DataFrame

prices_path = os.path.join(dir_path, 'prices.csv')

prices_pdf = pd.read_csv(prices_path)
prices_pdf['date'] = pd.to_datetime(prices_pdf['date'])
prices_pdf.set_index('date', inplace=True)

returns_pdf = prices_pdf.pct_change().dropna()

downside_dev = downside_deviation(returns_pdf, mar)

downside_dev_df = pd.DataFrame([downside_dev], columns=returns_pdf.columns)

returns_sdf = spark.createDataFrame(returns_pdf.reset_index())

downside_dev_sdf = spark.createDataFrame(downside_dev_df)
returns_sdf.createOrReplaceTempView('returns_from_r')
downside_dev_sdf.createOrReplaceTempView('DownsideRisk')

# Drop temp views if they have 0 records
if downside_dev_sdf.count() == 0:
    spark.catalog.dropTempView('DownsideRisk')
if returns_sdf.count() == 0:
    spark.catalog.dropTempView('returns_from_r')

diff = returns_df.alias('r').join(downside_dev_df.alias('d'), on=join_cols, how='outer') \
    .select(
        col('r.date'),
        (abs(col('r.IBM') - col('d.IBM')) > 1e-6).alias('IBM_diff'),
        (abs(col('r.GE') - col('d.GE')) > 1e-6).alias('GE_diff'),
        (abs(col('r.DOW') - col('d.DOW')) > 1e-6).alias('DOW_diff'),
        (abs(col('r.GOOGL') - col('d.GOOGL')) > 1e-6).alias('GOOGL_diff'),
        (abs(col('r.SPY') - col('d.SPY')) > 1e-6).alias('SPY_diff')
    )

diff_filtered = diff.filter(
    col('IBM_diff') | col('GE_diff') | col('DOW_diff') | col('GOOGL_diff') | col('SPY_diff')
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:

# Calculate returns (discrete method)
