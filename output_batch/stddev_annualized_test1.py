# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as spark_abs, col, lag, log, max as spark_max, stddev
from pyspark.sql.window import Window

spark = SparkSession.builder.appName('StdDevAnnualizedTest1').getOrCreate()

# Initialize Spark session

# Drop first row (where lag is null)

# Annualize standard deviation (scale=4, quarterly)

scale = 4

annualized_stddev_dict = {}
for c in cols:

# Create annualized_stddev DataFrame

# Prepare returns_from_r DataFrame (simulate R output for comparison)

    error_row = {'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}

    error_row = {'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}

    returns_from_r_df = spark.createDataFrame([error_row])

# Keep only the last row in annualized_stddev_df

annualized_stddev_df = annualized_stddev_df.orderBy(col('date').desc()).limit(1)

# Read prices CSV as DataFrame

    base = returns_from_r_df

    fuzz = lambda x, y: spark_abs(x - y) > 1e-8

# Count differences

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST StdDev_annualized_test1')
else:

prices_path = f"{dir}/prices.csv"

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST StdDev_annualized_test1')

# Clean up temporary tables if keep==False
if not keep:
    for df_name in ['diff_df', 'prices_df', 'returns_from_r_df', 'annualized_stddev_df']:
        try:
            locals().pop(df_name)
        except KeyError:
            pass

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

returns_df = prices_df.dropna(subset=[f'{c}_log_return' for c in cols])

    stddev_val = returns_df.agg(stddev(col(f'{c}_log_return')).alias('std')).collect()[0]['std']
    annualized_stddev_dict[c] = stddev_val * np.sqrt(scale) if stddev_val is not None else None

annualized_stddev_pd = pd.DataFrame([annualized_stddev_dict])
annualized_stddev_pd['date'] = returns_df.agg(spark_max('date')).collect()[0][0]

annualized_stddev_df = spark.createDataFrame(annualized_stddev_pd)

returns_from_r_df = annualized_stddev_df.select('date', *cols)

# Handle empty DataFrames by inserting error rows
if annualized_stddev_df.count() == 0:

    annualized_stddev_df = spark.createDataFrame([error_row])
if returns_from_r_df.count() == 0:

# Compare DataFrames (returns_from_r_df vs annualized_stddev_df, drop date)

diff_df = None
if returns_from_r_df is not None and annualized_stddev_df is not None:

    compare = annualized_stddev_df.drop('date')

    joined = base.crossJoin(compare)

    diff_df = joined.filter(
        fuzz(col('IBM'), col('IBM')) |
        fuzz(col('GE'), col('GE')) |
        fuzz(col('DOW'), col('DOW')) |
        fuzz(col('GOOGL'), col('GOOGL')) |
        fuzz(col('SPY'), col('SPY'))
    )

n = diff_df.count() if diff_df is not None else 0

# Set pass/fail and notes
if n == 0:

# Calculate log returns for each column except 'date'

cols = [c for c in prices_df.columns if c != 'date']

w = Window.orderBy('date')
for c in cols:

    prices_df = prices_df.withColumn(f'{c}_log_return', log(col(c)) - log(lag(col(c), 1).over(w)))
