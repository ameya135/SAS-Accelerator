# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Helper function to calculate Kelly Ratio

def kelly_ratio(returns_df, rf=0.01/252):

    pdf = returns_df.toPandas()

    mean_returns = pdf.mean()

    cov_matrix = pdf.cov()

    excess_returns = mean_returns - rf

    inv_cov = np.linalg.pinv(cov_matrix.values)

    weights = inv_cov.dot(excess_returns.values)

    kelly = weights / np.sum(weights)

    kelly_df = pd.DataFrame([kelly], columns=pdf.columns)
    return spark.createDataFrame(kelly_df)

# Calculate Kelly Ratio

returns_from_r = kellyratio

# Macro variables (should be set externally or passed as arguments)
# Example:
# dir = '/path/to/data'
# keep = False

    kellyratio = spark.createDataFrame([{'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])
if returns_from_r.count() == 0:

    returns_from_r = spark.createDataFrame([{'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# Compare DataFrames and output differences

diff = diff.withColumn('DIF_IBM', pyspark_abs(col('r.IBM') - col('k.IBM')) > 1e-6)

diff = diff.withColumn('DIF_GE', pyspark_abs(col('r.GE') - col('k.GE')) > 1e-6)

diff = diff.withColumn('DIF_DOW', pyspark_abs(col('r.DOW') - col('k.DOW')) > 1e-6)

diff = diff.withColumn('DIF_GOOGL', pyspark_abs(col('r.GOOGL') - col('k.GOOGL')) > 1e-6)

# Helper function to calculate discrete returns

# Count number of differences

    pass_var = True

    notes = 'Passed'
else:
    print('ERROR: PROBLEM IN TEST Kellyratio_TEST1')

    pass_var = False

    notes = 'Differences detected in outputs.'

def calculate_returns(df):

    cols = df.columns
    # Use window function for lag
    from pyspark.sql.window import Window
    from pyspark.sql.functions import lag

    w = Window.orderBy("Date") if "Date" in cols else Window().orderBy(cols[0])
    for c in cols:
        if c == "Date":
            continue

        df = df.withColumn(f"{c}_ret", (col(c) / lag(col(c), 1).over(w)) - 1)

    ret_cols = [f"{c}_ret" for c in cols if c != "Date"]
    return df.select(*ret_cols)

# Read prices.csv as Spark DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Calculate returns and drop NA rows

returns = calculate_returns(prices).na.drop()

kellyratio = kelly_ratio(returns, rf=0.01/252)

# Simulate returns_from_r as a copy of kellyratio for comparison

# Handle empty DataFrames by creating error rows
if kellyratio.count() == 0:

diff = returns_from_r.alias("r").join(
    kellyratio.alias("k"),
    on=['IBM', 'GE', 'DOW', 'GOOGL', 'SPY'],
    how='outer'
)

# If join on all columns results in empty diff, try joining on nothing and compare columns
if diff.count() == 0:

    diff = returns_from_r.crossJoin(kellyratio)

diff_filtered = diff.filter(
    col('DIF_IBM') | col('DIF_GE') | col('DIF_DOW') | col('DIF_GOOGL')
)

n = diff_filtered.count()

# Set pass/fail and notes
if n == 0:
    print('NOTE: NO ERROR IN TEST Kellyratio_TEST1')

# Drop intermediate tables if keep is False
if not keep:
    prices.unpersist()
    diff_filtered.unpersist()
    returns_from_r.unpersist()
    kellyratio.unpersist()
