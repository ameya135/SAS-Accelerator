# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, exp, lag, lit, log, sum as pyspark_sum
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

annualized_returns_pd = annualized_returns_pd[['date'] + [col for col in annualized_returns_pd.columns if col != 'date']]

# Convert pandas DataFrame to Spark DataFrame

# Drop first row with null returns

def annualize_return(df, return_cols):

    n_periods = df.count()

    agg_exprs = [
        (pyspark_sum(log(lit(1) + col(c))) / lit(n_periods)).alias(f'ann_{c}')
        for c in return_cols
    ]

    ann_df = df.agg(*agg_exprs)
    for c in return_cols:

# Set up variables (simulate macro variables)

        ann_df = ann_df.withColumn(f'ann_{c}', exp(col(f'ann_{c}')) - 1)
    return ann_df

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

keep = False  # Set this based on your workflow

# Keep only the last row in annualized_returns

annualized_returns = annualized_returns.orderBy(col('date').desc()).limit(1)

def fuzz(col1, col2, tol=1e-6):
    return pyspark_abs(col1 - col2) > tol

diff = diff.withColumn('IBM_DIF', fuzz(col('IBM'), col('ann_IBM_return')))

diff = diff.withColumn('GE_DIF', fuzz(col('GE'), col('ann_GE_return')))

diff = diff.withColumn('DOW_DIF', fuzz(col('DOW'), col('ann_DOW_return')))

diff = diff.withColumn('GOOGL_DIF', fuzz(col('GOOGL'), col('ann_GOOGL_return')))

diff = diff.withColumn('SPY_DIF', fuzz(col('SPY'), col('ann_SPY_return')))

data_dir = '/path/to/your/data'  # Set your directory path as string

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_ANNUALIZED_TEST2')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_ANNUALIZED_TEST2')

# Read prices CSV as DataFrame (Pandas)

prices_path = f'{data_dir}/prices.csv'

prices_pd = pd.read_csv(prices_path, parse_dates=['date'])
prices_pd.set_index('date', inplace=True)

# Calculate discrete returns using pandas

returns_pd = prices_pd.pct_change().dropna()

# Annualize returns (scale=1, geometric=TRUE) in pandas

annualized_returns_pd = (1 + returns_pd).prod() ** (1 / len(returns_pd)) - 1

annualized_returns_pd = annualized_returns_pd.to_frame().T
annualized_returns_pd['date'] = returns_pd.index[-1]

returns_from_r = spark.createDataFrame(annualized_returns_pd)

# Read prices into Spark DataFrame

prices = spark.read.csv(prices_path, header=True, inferSchema=True)

# Calculate discrete returns in PySpark

windowSpec = Window.orderBy('date')
for col_name in prices.columns:
    if col_name != 'date':

        prices = prices.withColumn(
            f'{col_name}_return',
            (col(col_name) - lag(col(col_name), 1).over(windowSpec)) / lag(col(col_name), 1).over(windowSpec)
        )

returns_cols = [f'{col}_return' for col in prices.columns if col != 'date']

returns = prices.dropna(subset=returns_cols)

# Annualize returns in PySpark (scale=1, geometric=TRUE)

annualized_returns = annualize_return(returns, returns_cols)

max_date = returns.agg({'date': 'max'}).collect()[0][0]

annualized_returns = annualized_returns.withColumn('date', lit(max_date))

# Check if annualized_returns and returns_from_r have records

annualized_returns_count = annualized_returns.count()

returns_from_r_count = returns_from_r.count()

# If tables have 0 records, create error DataFrames
if annualized_returns_count == 0:

    annualized_returns = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r_count == 0:

# Compare returns_from_r and annualized_returns

diff = returns_from_r.join(annualized_returns, on='date', how='inner')

diff_filtered = diff.filter(
    col('IBM_DIF') | col('GE_DIF') | col('DOW_DIF') | col('GOOGL_DIF') | col('SPY_DIF')
)

n = diff_filtered.count()

# Set pass/notes variables based on comparison
if n == 0:
