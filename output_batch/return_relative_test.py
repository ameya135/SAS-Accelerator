# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, row_number
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Calculate relative returns: columns 0-3 vs column 4 (SPY)

relative_returns_pd = relative_returns_pd[['date', 'IBM_SPY', 'GE_SPY', 'DOW_SPY', 'GOOGL_SPY', 'SPY']]

# Convert pandas DataFrames to Spark DataFrames

# --- Calculate returns and relative returns in Spark ---

prices = prices.dropna()

# Remove first row (firstobs=2 in SAS)

relative_cum = relative_cum.withColumn(
    'row_num', row_number().over(Window.orderBy('date'))
).filter(col('row_num') > 1).drop('row_num')

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# --- Compare DataFrames (fuzzy compare for IBM, GE, DOW, GOOGL) ---

# Set up variables (replace with actual values or pass as arguments)

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_RELATIVE_TEST')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_RELATIVE_TEST')

keep = False  # Set to True to keep intermediate tables

# --- Cleanup if keep is False ---
if not keep:
    for df_name in ['diff', 'prices', 'relative_cum', 'returns_from_r']:
        try:
            locals()[df_name].unpersist()
        except Exception:
            pass

data_dir = '/path/to/data'  # Replace with actual directory path

# Calculate discrete returns and drop NA

# --- Read and process prices.csv using pandas ---

prices_pd = pd.read_csv(os.path.join(data_dir, 'prices.csv'))

returns_pd = prices_pd.pct_change().dropna()

relative_returns_pd = returns_pd.iloc[:, 0:4].div(returns_pd.iloc[:, 4], axis=0)
relative_returns_pd.columns = ['IBM_SPY', 'GE_SPY', 'DOW_SPY', 'GOOGL_SPY']
relative_returns_pd['SPY'] = returns_pd.iloc[:, 4]
relative_returns_pd['date'] = prices_pd.iloc[1:, 0].values  # assuming first column is date

returns_from_r = spark.createDataFrame(
    relative_returns_pd.rename(columns={'IBM_SPY': 'IBM', 'GE_SPY': 'GE', 'DOW_SPY': 'DOW', 'GOOGL_SPY': 'GOOGL'})
)

prices = spark.createDataFrame(prices_pd)

windowSpec = Window.orderBy('date')
for colname in prices.columns[1:]:

    prices = prices.withColumn(
        f'{colname}_ret',
        (col(colname) - lag(col(colname), 1).over(windowSpec)) / lag(col(colname), 1).over(windowSpec)
    )

relative_cum = prices.select(
    'date',
    (col('IBM_ret') / col('SPY_ret')).alias('IBM'),
    (col('GE_ret') / col('SPY_ret')).alias('GE'),
    (col('DOW_ret') / col('SPY_ret')).alias('DOW'),
    (col('GOOGL_ret') / col('SPY_ret')).alias('GOOGL'),
    col('SPY_ret').alias('SPY')
).filter(~col('date').isNull())

# --- Handle empty DataFrames ---
if relative_cum.count() == 0:

    relative_cum = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r.count() == 0:

diff = returns_from_r.join(
    relative_cum, on='date', how='inner', suffixes=('_r', '_c')
).withColumn(
    'IBM_DIF', pyspark_abs(col('IBM_r') - col('IBM_c'))
).withColumn(
    'GE_DIF', pyspark_abs(col('GE_r') - col('GE_c'))
).withColumn(
    'DOW_DIF', pyspark_abs(col('DOW_r') - col('DOW_c'))
).withColumn(
    'GOOGL_DIF', pyspark_abs(col('GOOGL_r') - col('GOOGL_c'))
).filter(
    (col('IBM_DIF') > 1e-8) | (col('GE_DIF') > 1e-8) | (col('DOW_DIF') > 1e-8) | (col('GOOGL_DIF') > 1e-8)
)

n = diff.count()

if n == 0:
