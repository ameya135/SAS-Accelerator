# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag
from pyspark.sql.types import DoubleType, StringType, StructField, StructType
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("Sort_Drawdowns_test").getOrCreate()

# ---------------------------
# Initialize Spark session
# ---------------------------

def find_drawdowns(returns):

    wealth_index = (1 + returns).cumprod()

    previous_peaks = wealth_index.cummax()

    drawdowns = (wealth_index - previous_peaks) / previous_peaks

# ---------------------------
# Find drawdowns (geometric=True)
# ---------------------------

    trough = drawdowns.idxmin()

    end = drawdowns[trough:].idxmax()

    begin = drawdowns[:trough].idxmax()

    length = (end - begin).days

    peaktotrough = (trough - begin).days

    recovery = (end - trough).days
    return {
        'return': drawdowns.min(),
        'begin': begin,
        'trough': trough,
        'end': end,
        'length': length,
        'peaktotrough': peaktotrough,
        'recovery': recovery
    }

# ---------------------------
# Sort drawdowns (top 7)
# ---------------------------

drawdown_list = []

    returns_col = returns_col.drop(pd.date_range(dd['begin'], dd['end']))

returns_from_r_pd = pd.DataFrame(drawdown_list, columns=['return','begin','trough','end','length','peaktotrough','recovery'])

# ---------------------------
# Convert pandas DataFrame to Spark DataFrame
# ---------------------------

returns_from_r = spark.createDataFrame(returns_from_r_pd)

# ---------------------------
# Set up file paths and flags
# ---------------------------

# ---------------------------
# Calculate returns in Spark (discrete)
# ---------------------------

windowSpec = Window.orderBy('Date')

prices = prices.withColumn('return', (col('IBM') - lag('IBM', 1).over(windowSpec)) / lag('IBM', 1).over(windowSpec))

prices = prices.na.drop(subset=['return'])

# ---------------------------
# Sort drawdowns in Spark (collect to pandas for logic)
# ---------------------------

def spark_find_drawdowns(df):

    pdf = df.select('Date', 'return').toPandas().set_index('Date')

    drawdown_list = []

keep = False  # Set this based on macro variable

    returns_col = pdf['return']
    for _ in range(7):
        if returns_col.empty:
            break

        returns_col = returns_col.drop(pd.date_range(dd['begin'], dd['end']))
    return pd.DataFrame(drawdown_list, columns=['return','begin','trough','end','length','peaktotrough','recovery'])

    SortDrawdowns = None
if returns_from_r.count() == 0:

    returns_from_r = None

# ---------------------------
# Create error rows if tables do not exist
# ---------------------------

dir_path = dir  # Provided macro variable

# ---------------------------
# Compare DataFrames and output differences (fuzzy match)
# ---------------------------

def fuzz(x, y, tol=1e-8):
    if x is None or y is None:
        return False
    return abs(x - y) < tol

diff = spark.createDataFrame(diff_pd[diff_pd['DIF']])

# ---------------------------
# Count number of differences
# ---------------------------

n = diff.count()

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST SORT_DRAWDOWNS_TEST')
else:

# ---------------------------
# Set pass/fail and notes
# ---------------------------
if n == 0:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST SORT_DRAWDOWNS_TEST')

# ---------------------------
# Clean up temporary tables if keep is False
# ---------------------------
if not keep:
    for tbl in ['diff', 'prices', 'SortDrawdowns', 'returns_from_r']:
        try:
            spark.catalog.dropTempView(tbl)
        except Exception:
            pass

# ---------------------------
# Calculate returns (discrete method, drop NA)
# ---------------------------

prices_csv_path = os.path.join(dir_path, 'prices.csv')

# ---------------------------
# Read prices.csv into pandas DataFrame for financial calculations
# ---------------------------

prices_pd = pd.read_csv(prices_csv_path, index_col=0, parse_dates=True)

returns_pd = prices_pd.pct_change().dropna()

returns_col = returns_pd.iloc[:, 0]  # Assuming single asset (IBM)
for _ in range(7):
    if returns_col.empty:
        break

    dd = find_drawdowns(returns_col)
    drawdown_list.append(dd)

# ---------------------------
# Read prices into Spark DataFrame
# ---------------------------

prices = spark.read.option('header', True).option('inferSchema', True).csv(prices_csv_path)

        dd = find_drawdowns(returns_col)
        drawdown_list.append(dd)

SortDrawdowns_pd = spark_find_drawdowns(prices)

SortDrawdowns = spark.createDataFrame(SortDrawdowns_pd)

# ---------------------------
# Handle empty DataFrames
# ---------------------------
if SortDrawdowns.count() == 0:

error_schema = StructType([
    StructField('return', DoubleType(), True),
    StructField('begin', StringType(), True),
    StructField('trough', StringType(), True),
    StructField('end', StringType(), True),
    StructField('length', DoubleType(), True),
    StructField('peaktotrough', DoubleType(), True),
    StructField('recovery', DoubleType(), True)
])
if SortDrawdowns is None:

    SortDrawdowns = spark.createDataFrame([(float(-999), '-999', '-999', '-999', float(-999), float(-999), float(-999))], schema=error_schema)
if returns_from_r is None:

    returns_from_r = spark.createDataFrame([(float(-999), '-999', '-999', '-999', float(-999), float(-999), float(-999))], schema=error_schema)

diff_pd = pd.merge(returns_from_r_pd, SortDrawdowns_pd, how='outer', suffixes=('_r', '_s'))
diff_pd['DIF'] = (
    diff_pd.apply(lambda row: not (
        fuzz(row['return_r'], row['return_s']) and
        fuzz(row['begin_r'], row['begin_s']) and
        fuzz(row['trough_r'], row['trough_s']) and
        fuzz(row['end_r'], row['end_s']) and
        fuzz(row['length_r'], row['length_s']) and
        fuzz(row['peaktotrough_r'], row['peaktotrough_s']) and
        fuzz(row['recovery_r'], row['recovery_s'])
    ), axis=1)
)
