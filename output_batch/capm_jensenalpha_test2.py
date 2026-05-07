# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, year, month, expr, row_number, when
from pyspark.sql.types import DateType, StructField, StructType
from pyspark.sql.window import Window

spark = SparkSession.builder.appName('CAPM_JensenAlpha_test2').getOrCreate()

# ---- Configuration ----

# ---- Calculate discrete returns ----

# ---- Remove rows with null returns ----
for c in num_cols:

    prices = prices.filter(col(f'{c}_ret').isNotNull())

# ---- Aggregate to monthly returns (geometric) ----

# ---- Jensen's Alpha calculation ----
# Assume market return is the 5th column, risk-free rate is 0.01/12

date_column = 'Date'  # Set your date column name here

window_spec = Window.orderBy(date_column)
for c in num_cols:

    prices = prices.withColumn(f'{c}_ret', (col(c) / lag(col(c), 1).over(window_spec)) - 1)

prices = prices.withColumn('year', year(col(date_column))).withColumn('month', month(col(date_column)))

rf = 0.01 / 12

def jensen_alpha(returns, market, rf):
    # returns: 2D numpy array (rows: time, cols: assets), market: 1D numpy array, rf: float

    alphas = []
    for i in range(returns.shape[1]):

        y = returns[:, i] - rf

        x = market - rf

        beta = np.cov(y, x)[0, 1] / np.var(x)

        alpha = np.mean(y) - beta * np.mean(x)
        alphas.append(alpha)
    return alphas

# Convert Spark DataFrame to Pandas for Jensen's Alpha calculation

prices_csv_dir = '/path/to/csv'  # Set your directory path here

returns_matrix = monthly_returns_pd[asset_cols[:4]].values  # First 4 assets

market_returns = monthly_returns_pd[asset_cols[4]].values   # 5th column as market

jensen_alphas = jensen_alpha(returns_matrix, market_returns, rf)

# ---- Create DataFrame for Jensen's Alpha results ----

jensen_alpha_df = pd.DataFrame({'Asset': asset_cols[:4], 'JensenAlpha': jensen_alphas})

jensen_alpha_spark = spark.createDataFrame(jensen_alpha_df)

# ---- Edit returns: set first row of each return column to null ----
for c in num_cols:

    prices = prices.withColumn(
        f'{c}_ret',
        when(row_number().over(window_spec) == 1, None).otherwise(col(f'{c}_ret'))
    )

# ---- Initialize Spark session ----

prices_schema = StructType([StructField(date_column, DateType(), True)])  # Add other columns as needed

# ---- Load prices CSV as DataFrame ----

prices_path = os.path.join(prices_csv_dir, 'prices.csv')

prices = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

num_cols = [c for c in prices.columns if c != date_column]

monthly_returns = prices.groupBy('year', 'month').agg(
    *[expr(f'EXP(SUM(LOG(1 + {c}_ret))) - 1').alias(f'{c}_monthly_ret') for c in num_cols]
)

monthly_returns_pd = monthly_returns.toPandas()

asset_cols = [c for c in monthly_returns_pd.columns if c.endswith('_monthly_ret')]

# ---- Final DataFrames: prices, monthly_returns, jensen_alpha_spark ----
