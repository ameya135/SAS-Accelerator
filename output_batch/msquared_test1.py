# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag
from pyspark.sql.types import ArrayType, DoubleType
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("MSquared_test1").getOrCreate()

# Initialize Spark session

# Define tM2 function (Python equivalent of R's tM2)

    def sharpe_ratio_annualized(R, Rf=0, scale=None, geometric=True):

    def stddev_annualized(R, scale=None):
        return np.std(R, ddof=1) * np.sqrt(scale if scale else 1)

    def return_annualized(R, scale=None, geometric=True):
        if geometric:
            return (np.prod(1 + R)**(1/len(R)) - 1) * (scale if scale else 1)
        else:
            return np.mean(R) * (scale if scale else 1)

# Set directory variable (ensure this is defined before running)

returns_from_r_pd = returns_from_r_pd[['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]

# Calculate discrete returns in Spark

windowSpec = Window.orderBy('date')
for colname in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    prices_df = prices_df.withColumn(
        f'{colname}_return',
        (col(colname) - lag(col(colname), 1).over(windowSpec)) / lag(col(colname), 1).over(windowSpec)
    )

# Drop first row with null returns

prices_df = prices_df.na.drop(subset=[f'{c}_return' for c in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']])

dir = '/path/to/your/data'  # <-- Update this path as needed

def msquared_udf(IBM, GE, DOW, GOOGL, SPY):

    Ra = np.column_stack([IBM, GE, DOW, GOOGL])

    Rb = np.array(SPY)

msquared_udf_spark = spark.udf.register(
    "msquared_udf_spark",
    lambda IBM, GE, DOW, GOOGL, SPY: msquared_udf(IBM, GE, DOW, GOOGL, SPY),
    ArrayType(DoubleType())
)

MSquared_pd = pd.DataFrame([msquared_row], columns=['IBM', 'GE', 'DOW', 'GOOGL'])
MSquared_pd['SPY'] = tM2(
    prices_pd['SPY'].pct_change().dropna(),
    prices_pd['SPY'].pct_change().dropna(),
    Rf=0.01/252, scale=252, geometric=True
)
MSquared_pd['date'] = -1

        excess = R - Rf
        if geometric:

            mean_ret = (np.prod(1 + excess)**(1/len(excess)) - 1) * (scale if scale else 1)
        else:

            mean_ret = np.mean(excess) * (scale if scale else 1)

        std_ret = np.std(excess, ddof=1) * np.sqrt(scale if scale else 1)
        return mean_ret / std_ret if std_ret != 0 else np.nan

        Rf_adj = (1 + Rf)**(scale if scale else 1) - 1
    else:

        Rf_adj = Rf * (scale if scale else 1)

MSquared_pd = MSquared_pd[['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]

MSquared = spark.createDataFrame(MSquared_pd)

# MSquared calculation in Spark using UDF

# Aggregate MSquared results

# Read prices.csv as DataFrame

# Handle empty DataFrames
if MSquared.count() == 0:

    returns_from_r = spark.createDataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames (fuzzy float comparison)

# Count differences

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST MSQUARED_TEST1')
else:

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(f'{dir}/prices.csv')

msquared_row = prices_df.agg(
    msquared_udf_spark(
        col('IBM_return'),
        col('GE_return'),
        col('DOW_return'),
        col('GOOGL_return'),
        col('SPY_return')
    ).alias('msquared')
).collect()[0]['msquared']

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST MSQUARED_TEST1')

# Clean up temporary tables if keep==False

keep = False  # <-- Set this as needed
if not keep:
    for tbl in ['diff', 'prices_df', 'returns_from_r', 'MSquared']:
        if tbl in spark.catalog.listTables():
            spark.catalog.dropTempView(tbl)

# Convert prices_df to Pandas for return calculations

prices_pd = prices_df.toPandas().set_index('date')

returns_pd = prices_pd.pct_change().dropna()

Ra = returns_pd.iloc[:, 0:4]

    SR = sharpe_ratio_annualized(Ra, Rf=Rf, scale=scale, geometric=geometric)

Rb = returns_pd.iloc[:, 4]

def tM2(Ra, Rb, Rf=0, scale=None, geometric=True):

    sb = stddev_annualized(Rb, scale=scale)

    rm = return_annualized(Rb, scale=scale, geometric=geometric)
    if geometric:

    result = SR * sb + Rf_adj - rm
    return result

# Apply tM2 to columns 0:4 as Ra, column 4 as Rb (IBM, GE, DOW, GOOGL, SPY)

tM2_results = []
for i in range(Ra.shape[1]):
    tM2_results.append(tM2(Ra.iloc[:, i], Rb, Rf=0.01/252, scale=252, geometric=True))

returns_from_r_pd = pd.DataFrame([tM2_results], columns=Ra.columns)
returns_from_r_pd['SPY'] = tM2(Rb, Rb, Rf=0.01/252, scale=252, geometric=True)
returns_from_r_pd['date'] = 1

# Convert returns_from_r_pd to Spark DataFrame

returns_from_r = spark.createDataFrame(returns_from_r_pd)

    results = []
    for i in range(Ra.shape[1]):
        results.append(float(tM2(Ra[:, i], Rb, Rf=0.01/252, scale=252, geometric=True)))
    return results

    MSquared = spark.createDataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r.count() == 0:

diff = returns_from_r.join(MSquared, on='date', how='inner', suffixes=('_r', '_m')) \
    .withColumn('IBM_diff', pyspark_abs(col('IBM_r') - col('IBM_m'))) \
    .withColumn('GE_diff', pyspark_abs(col('GE_r') - col('GE_m'))) \
    .withColumn('DOW_diff', pyspark_abs(col('DOW_r') - col('DOW_m'))) \
    .withColumn('GOOGL_diff', pyspark_abs(col('GOOGL_r') - col('GOOGL_m'))) \
    .filter(
        (col('IBM_diff') > 1e-6) |
        (col('GE_diff') > 1e-6) |
        (col('DOW_diff') > 1e-6) |
        (col('GOOGL_diff') > 1e-6)
    )

n = diff.count()

# Set pass/notes variables
if n == 0:

# Calculate discrete returns, drop NA
