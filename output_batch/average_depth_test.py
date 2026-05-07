# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs

spark = SparkSession.builder.appName("Average_Depth_Test").getOrCreate()

# Initialize Spark session

# Calculate average drawdown (using pandas, as PySpark lacks direct equivalent)

def average_drawdown(returns):

    drawdowns = (returns.cumsum() - returns.cumsum().cummax())
    return drawdowns.mean()

# Convert pandas DataFrames to Spark DataFrames

# Drop temp views if they have 0 records
if spark.sql('SELECT COUNT(*) as cnt FROM Avg_DD').collect()[0]['cnt'] == 0:
    spark.catalog.dropTempView('Avg_DD')
if spark.sql('SELECT COUNT(*) as cnt FROM returns_from_r').collect()[0]['cnt'] == 0:
    spark.catalog.dropTempView('returns_from_r')

# If tables do not exist, create error rows

table_names = [t.name for t in spark.catalog.listTables()]
if 'Avg_DD' not in table_names:

    error_row = {'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    avg_dd_sdf = spark.createDataFrame([error_row])
    avg_dd_sdf.createOrReplaceTempView('Avg_DD')

if 'returns_from_r' not in table_names:

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_sdf = spark.createDataFrame([error_row])
    returns_sdf.createOrReplaceTempView('returns_from_r')

# Compare the two tables and output differences (fuzz logic: abs diff > 1e-6)

diff_df = spark.sql('''
    SELECT
        r.date,
        r.IBM as IBM_r, a.IBM as IBM_a,
        r.GE as GE_r, a.GE as GE_a,
        r.DOW as DOW_r, a.DOW as DOW_a,
        r.GOOGL as GOOGL_r, a.GOOGL as GOOGL_a,
        r.SPY as SPY_r, a.SPY as SPY_a
    FROM returns_from_r r
    FULL OUTER JOIN Avg_DD a ON r.date = a.date
    WHERE
        abs(r.IBM - a.IBM) > 1e-6 OR
        abs(r.GE - a.GE) > 1e-6 OR
        abs(r.DOW - a.DOW) > 1e-6 OR
        abs(r.GOOGL - a.GOOGL) > 1e-6 OR
        abs(r.SPY - a.SPY) > 1e-6
''')

# Check for differences and set pass/fail variables
if diff_df.count() == 0:
    print('NOTE: NO ERROR IN TEST AVERAGE_DEPTH_TEST')

# Set up variables from macro or environment

    pass_var = True

    notes_var = 'Passed'
else:
    print('ERROR: PROBLEM IN TEST AVERAGE_DEPTH_TEST')

    pass_var = False

    notes_var = 'Differences detected in outputs.'

keep = False  # Set from macro or parameter

# Cleanup temp views if keep is False
if not keep:
    spark.catalog.dropTempView('returns_from_r')
    spark.catalog.dropTempView('Avg_DD')

data_dir = os.environ.get('dir', '/path/to/dir')

# Read prices CSV as pandas DataFrame for financial calculations

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))
prices_pd.set_index('date', inplace=True)

# Calculate returns (discrete method)

returns_pd = prices_pd.pct_change().dropna()

avg_dd_pd = pd.DataFrame({col: [average_drawdown(returns_pd[col])] for col in returns_pd.columns})
avg_dd_pd['date'] = returns_pd.index[-1] if not returns_pd.empty else -1

avg_dd_pd = avg_dd_pd[['date'] + [col for col in returns_pd.columns]]

returns_sdf = spark.createDataFrame(returns_pd.reset_index())

avg_dd_sdf = spark.createDataFrame(avg_dd_pd)

# Register as temp views for SQL operations
returns_sdf.createOrReplaceTempView('returns_from_r')
avg_dd_sdf.createOrReplaceTempView('Avg_DD')
