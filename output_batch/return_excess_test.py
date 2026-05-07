# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, lit
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("RETURN_EXCESS_TEST").getOrCreate()

# --- Initialize Spark session ---

# --- Prepare pandas DataFrame to match output structure ---

returns_excess_pdf = returns_excess_pdf.reset_index()
returns_excess_pdf.columns = ['date', 'IBM', 'GE', 'DOW', 'GOOGL', 'SPY']

# --- Convert pandas DataFrame to Spark DataFrame ---

prices = spark.read.csv(f'{dir_path}/prices.csv', header=True, inferSchema=True)

# --- Read prices.csv as Spark DataFrame ---

# --- Calculate discrete returns in Spark ---

window_spec = Window.orderBy('date')
for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    prices = prices.withColumn(
        f'{col_name}_ret',
        (col(col_name) / lag(col(col_name), 1).over(window_spec)) - 1
    )

# --- Calculate excess returns in Spark ---
for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

risk_premium = prices.select(
    col('date'),
    col('IBM_excess').alias('IBM'),
    col('GE_excess').alias('GE'),
    col('DOW_excess').alias('DOW'),
    col('GOOGL_excess').alias('GOOGL'),
    col('SPY_excess').alias('SPY')
).where(col('IBM_excess').isNotNull())

# --- Apply comparison threshold (criterion=1e-6) ---

# --- Count number of differences ---

# --- Macro variable equivalents (should be set externally) ---
# Set these before running the script
# dir_path = '/path/to/data'
# keep = True or False

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST RETURN_EXCESS_TEST')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST RETURN_EXCESS_TEST')

# --- Clean up temporary DataFrames if keep is False ---
if not keep:
    for df in ['returns_from_r', 'risk_premium', 'prices', 'diff_filtered']:
        if df in locals():
            try:
                locals()[df].unpersist()
            except Exception:
                pass

# --- Read prices.csv as Pandas DataFrame for reference calculation ---

prices_pdf = pd.read_csv(f'{dir_path}/prices.csv', parse_dates=['date'])

prices_pdf = prices_pdf.sort_values('date').set_index('date')

# --- Calculate discrete returns and excess returns using pandas ---

returns_pdf = prices_pdf.pct_change().dropna()

returns_excess_pdf = returns_pdf - rf

returns_from_r = spark.createDataFrame(returns_excess_pdf)

# --- Prepare risk_premium DataFrame to match returns_from_r structure ---

# --- Compare returns_from_r and risk_premium DataFrames ---

joined = returns_from_r.alias('r').join(
    risk_premium.alias('p'), on='date', how='inner'
)

diff = joined.select(
    'date',
    pyspark_abs(col('r.IBM') - col('p.IBM')).alias('IBM'),
    pyspark_abs(col('r.GE') - col('p.GE')).alias('GE'),
    pyspark_abs(col('r.DOW') - col('p.DOW')).alias('DOW'),
    pyspark_abs(col('r.GOOGL') - col('p.GOOGL')).alias('GOOGL'),
    pyspark_abs(col('r.SPY') - col('p.SPY')).alias('SPY')
)

diff_filtered = diff.where(
    (col('IBM') > 1e-6) | (col('GE') > 1e-6) | (col('DOW') > 1e-6) | (col('GOOGL') > 1e-6) | (col('SPY') > 1e-6)
)

n = diff_filtered.count()

# --- Set pass/notes variables based on comparison ---
if n == 0:

rf = 0.04 / 12

    prices = prices.withColumn(
        f'{col_name}_excess',
        col(f'{col_name}_ret') - lit(rf)
    )
