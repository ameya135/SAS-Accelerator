# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession, functions as F, Window

spark = SparkSession.builder.appName("CalendarReturnsTest1").getOrCreate()

# Initialize Spark session

calendar_returns_pdf = monthly_returns_pdf[['SPY']].copy()
calendar_returns_pdf['Year'] = calendar_returns_pdf.index.year
calendar_returns_pdf['Month'] = calendar_returns_pdf.index.strftime('%b').str.upper()

calendar_returns_pivot = calendar_returns_pdf.pivot(index='Year', columns='Month', values='SPY')

months = ['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC']

calendar_returns_pivot = calendar_returns_pivot.reindex(columns=months)

calendar_returns_pivot = calendar_returns_pivot.round(6)
calendar_returns_pivot.reset_index(inplace=True)

# Convert pandas DataFrame to Spark DataFrame

returns_from_r = spark.createDataFrame(calendar_returns_pivot)

# --- PySpark Section: Calculate Calendar Returns ---

prices = prices.withColumn('Date', F.to_date('Date'))

# Calculate discrete returns using window functions

window_spec = Window.orderBy('Date')

prices = prices.withColumn('prev_SPY', F.lag('SPY').over(window_spec))

prices = prices.withColumn('SPY_RETURN', (F.col('SPY') / F.col('prev_SPY')) - 1)

# Extract Year and Month

prices = prices.withColumn('Year', F.year('Date'))

prices = prices.withColumn('Month', F.date_format('Date', 'MMM').upper())

# Macro variables (replace with actual values or pass as arguments)

# Aggregate to monthly returns (geometric)

# Pivot to calendar format

# Filter for rows where January is not null

# --- Handle Empty Results ---

    error_data = {m: -999 for m in months}

    Calendar_Returns = spark.createDataFrame([error_data])

dir = os.environ.get('DIR', '/path/to/dir')

prices = spark.read.csv(os.path.join(dir, 'prices.csv'), header=True, inferSchema=True)

# Read prices.csv as Spark DataFrame

monthly_returns = prices.groupBy('Year', 'Month').agg(
    (F.expr('product(SPY_RETURN + 1)') - 1).alias('SPY')
)

calendar_returns = monthly_returns.groupBy('Year').pivot('Month', months).agg(F.first('SPY'))

Calendar_Returns = calendar_returns.filter(F.col('JAN').isNotNull())

if Calendar_Returns.count() == 0:

if returns_from_r.count() == 0:

    error_data = {m: 999 for m in months}

    returns_from_r = spark.createDataFrame([error_data])

# --- Compare DataFrames and Output Differences ---

join_cols = months

returns_from_r = returns_from_r.select(*(['Year'] + months))

Calendar_Returns = Calendar_Returns.select(*(['Year'] + months))

diff = returns_from_r.alias('left').join(
    Calendar_Returns.alias('right'),
    on='Year',
    how='outer'
)

# Join on all months

for m in months:

keep = os.environ.get('KEEP', 'FALSE')

    diff = diff.withColumn(f'DIF_{m}', F.abs(F.col(f'left.{m}') - F.col(f'right.{m}')))

diff_filtered = diff.filter(
    ' OR '.join([f'ABS(left.{m} - right.{m}) > 1e-4' for m in months])
)

n = diff_filtered.count()

# --- Set Pass/Fail and Notes ---

if n == 0:

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_CalendarReturns_TEST1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_CalendarReturns_TEST1')

# --- Cleanup Intermediate Tables if Needed ---

# --- Pandas Section: Calculate Calendar Returns as Reference ---

if keep == 'FALSE':
    prices.unpersist(blocking=True)
    diff_filtered.unpersist(blocking=True)
    returns_from_r.unpersist(blocking=True)
    Calendar_Returns.unpersist(blocking=True)

# Read prices.csv into a Pandas DataFrame

prices_pdf = pd.read_csv(os.path.join(dir, 'prices.csv'))
prices_pdf['Date'] = pd.to_datetime(prices_pdf['Date'])
prices_pdf.set_index('Date', inplace=True)

returns_pdf = prices_pdf.pct_change().dropna()

monthly_returns_pdf = returns_pdf.resample('M').apply(lambda x: (1 + x).prod() - 1)

# Calculate discrete returns, resample monthly, cumulative geometric returns
