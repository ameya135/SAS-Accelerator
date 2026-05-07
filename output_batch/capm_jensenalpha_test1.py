# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col
from pyspark.sql.types import DateType, DoubleType, IntegerType, StructField, StructType
from sklearn.linear_model import LinearRegression

spark = SparkSession.builder.appName('CAPM_JensenAlpha_test1').getOrCreate()

# Initialize Spark session

# Calculate discrete returns using pandas, then convert to Spark DataFrame

# --- Jensen's Alpha Calculation ---

def capm_jensen_alpha(returns_df, bm_col, rf=0.01/252):

    results = {}

    bm = returns_df[bm_col] - rf
    for col_name in returns_df.columns:
        if col_name == bm_col or col_name == 'date':
            continue

        y = returns_df[col_name] - rf

        X = bm.values.reshape(-1, 1)

        reg = LinearRegression().fit(X, y.values)

        alpha = reg.intercept_
        results[col_name] = alpha

    results_df = pd.DataFrame([results])
    return results_df

# Compute Jensen's Alpha for IBM, GE, DOW, GOOGL vs SPY

jensen_alpha_pdf = jensen_alpha_pdf[['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']]

returns_from_r = returns_sdf

# Save returns_from_r as Spark DataFrame (mimicking importdatasetfromr)

    jensen_alpha_sdf = None
if returns_from_r.count() == 0:

# Define input parameters (replace with actual values or pass as arguments)

    returns_from_r = None

    error_schema = StructType([
        StructField('date', IntegerType(), True),
        StructField('IBM', DoubleType(), True),
        StructField('GE', DoubleType(), True),
        StructField('DOW', DoubleType(), True),
        StructField('GOOGL', DoubleType(), True),
        StructField('SPY', DoubleType(), True)
    ])

    jensen_alpha_sdf = spark.createDataFrame([(-1, -999.0, -999.0, -999.0, -999.0, -999.0)], error_schema)

# If returns_from_r does not exist, create error DataFrame
if returns_from_r is None:

    error_schema = StructType([
        StructField('date', IntegerType(), True),
        StructField('IBM', DoubleType(), True),
        StructField('GE', DoubleType(), True),
        StructField('DOW', DoubleType(), True),
        StructField('GOOGL', DoubleType(), True),
        StructField('SPY', DoubleType(), True)
    ])

    returns_from_r = spark.createDataFrame([(1, 999.0, 999.0, 999.0, 999.0, 999.0)], error_schema)

# --- Compare DataFrames: compute differences for IBM, GE, DOW, GOOGL ---

# Define fuzz function (tolerance for floating point comparison)

dir = dir  # directory path as string

def fuzz(val_col):
    return pyspark_abs(val_col) > 1e-8

# --- Test Result ---

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST CAPM_JensenAlpha_test1')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST CAPM_JensenAlpha_test1')

# --- Optional: Clean up intermediate DataFrames if not keeping ---
if not keep:

keep = keep  # boolean: True or False

    prices_sdf = None

    returns_from_r = None

    jensen_alpha_sdf = None

    diff = None

    diff_filtered = None

# --- Read and Prepare Data ---
# Read prices.csv as pandas DataFrame

prices_pdf = pd.read_csv(f'{dir}/prices.csv', parse_dates=True)
prices_pdf.set_index(prices_pdf.columns[0], inplace=True)
prices_pdf.index.name = 'date'

returns_pdf = prices_pdf.pct_change().dropna().reset_index()

returns_sdf = spark.createDataFrame(returns_pdf)

jensen_alpha_pdf = capm_jensen_alpha(returns_pdf, 'SPY', rf=0.01/252)
jensen_alpha_pdf['date'] = returns_pdf['date'].iloc[-1]
jensen_alpha_pdf['SPY'] = 0.0

jensen_alpha_sdf = spark.createDataFrame(jensen_alpha_pdf)

# --- Handle Empty DataFrames ---
if jensen_alpha_sdf.count() == 0:

# If Jensen_Alpha does not exist, create error DataFrame
if jensen_alpha_sdf is None:

diff = returns_from_r.alias('base').join(jensen_alpha_sdf.alias('compare'), on='date', how='inner')\
    .select(
        col('base.date'),
        (col('base.IBM') - col('compare.IBM')).alias('IBM_DIF'),
        (col('base.GE') - col('compare.GE')).alias('GE_DIF'),
        (col('base.DOW') - col('compare.DOW')).alias('DOW_DIF'),
        (col('base.GOOGL') - col('compare.GOOGL')).alias('GOOGL_DIF')
    )

diff_filtered = diff.filter(
    fuzz(col('IBM_DIF')) | fuzz(col('GE_DIF')) | fuzz(col('DOW_DIF')) | fuzz(col('GOOGL_DIF'))
)

n = diff_filtered.count()

if n == 0:

# Convert prices DataFrame to Spark DataFrame

prices_sdf = spark.createDataFrame(prices_pdf.reset_index())
