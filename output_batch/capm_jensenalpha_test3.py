# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, monotonically_increasing_id, when

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# ---------------------------
# Initialize Spark session
# ---------------------------

# ---------------------------
# Jensen's Alpha calculation
# ---------------------------

        y = returns[col] - rf

        x = benchmark - rf

        beta = np.cov(y, x)[0, 1] / np.var(x)

        alpha = y.mean() - beta * x.mean()
        alphas[col] = alpha
    return pd.DataFrame([alphas])

benchmark_col = agg_cols[-1]  # Assumes last column is benchmark

# ---------------------------
# Convert Jensen's Alpha results back to Spark DataFrame
# ---------------------------

# ---------------------------
# Define file paths and parameters
# ---------------------------

    windowed = windowed.withColumn(col_name, when(col('row_num') == 0, lit(None)).otherwise(col(col_name)))

dir_path = dir  # Assumes 'dir' is defined externally as a macro variable or string

prices_csv_path = os.path.join(dir_path, 'prices.csv')

date_column = 'date'  # Set your date column name here

    pdf = pdf.sort_values(by=date_column)

def calculate_discrete_returns(pdf, date_column):

    returns = pdf.iloc[:, 1:].pct_change().dropna()
    returns[date_column] = pdf[date_column].iloc[1:].values
    return returns

# ---------------------------
# Aggregate returns yearly using cumulative product (geometric return)
# ---------------------------
returns_pd[date_column] = pd.to_datetime(returns_pd[date_column])
returns_pd['year'] = returns_pd[date_column].dt.year

def jensen_alpha(returns, benchmark, rf=0.01):

    alphas = {}
    for col in returns.columns:
        if col == 'year':
            continue

# ---------------------------
# Edit_returns macro equivalent: set first row of each numeric column (except date_column) to null
# ---------------------------

# ---------------------------
# Read prices CSV into Spark DataFrame
# ---------------------------

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_csv_path)

prices_pd = prices_df.toPandas()

returns_pd = calculate_discrete_returns(prices_pd, date_column)

agg_cols = [c for c in returns_pd.columns if c not in [date_column, 'year']]

yearly_returns = returns_pd.groupby('year')[agg_cols].apply(lambda x: (1 + x).prod() - 1).reset_index()

jensen_alpha_df = jensen_alpha(yearly_returns, yearly_returns[benchmark_col], rf=0.01)

jensen_alpha_spark_df = spark.createDataFrame(jensen_alpha_df)

numeric_cols = [field.name for field in prices_df.schema.fields if str(field.dataType) != 'StringType' and field.name != date_column]

windowed = prices_df.withColumn('row_num', monotonically_increasing_id())
for col_name in numeric_cols:

prices_edited = windowed.drop('row_num')

# ---------------------------
# Calculate discrete returns using pandas
# ---------------------------
