# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, when, monotonically_increasing_id
from pyspark.sql.types import NumericType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# ---- Configuration ----
# Define file paths and column names

# ---- Convert Spark DataFrame to Pandas for financial calculations ----

returns_pd = returns_pd.groupby('Year').tail(1)

# ---- Adjusted Sharpe Ratio calculation ----

rf = 0.01

excess_returns = returns_pd[returns_column] - rf

sharpe_ratio = excess_returns.mean() / excess_returns.std(ddof=0)

data_dir = '/path/to/data'  # Set your data directory here

skewness = excess_returns.skew()

kurtosis = excess_returns.kurtosis()

adj_sharpe = sharpe_ratio * (1 + (skewness / 6) * sharpe_ratio - ((kurtosis - 3) / 24) * sharpe_ratio ** 2)
returns_pd['AdjustedSharpeRatio'] = adj_sharpe * 100

# ---- Prepare final returns DataFrame with date as a column ----

returns_pd = returns_pd.reset_index().rename(columns={returns_pd.index.name: date_column})

# ---- Convert back to Spark DataFrame ----

prices_csv_path = os.path.join(data_dir, 'prices.csv')

for col_name in numeric_cols:

date_column = 'Date'        # Set your date column name here

# ---- Set first row of all numeric columns (except date_column) to null ----

returns_column = 'Returns'  # Set your returns column name here

# ---- Initialize Spark session ----

# ---- Read prices CSV into Spark DataFrame ----

prices_df = spark.read.option('header', True).option('inferSchema', True).csv(prices_csv_path)

prices_pd = prices_df.toPandas()

# ---- Calculate discrete returns using pandas ----
prices_pd.set_index(date_column, inplace=True)
prices_pd[returns_column] = prices_pd.iloc[:, 0].pct_change()  # Assumes first column after date is price

returns_pd = prices_pd.dropna(subset=[returns_column])

# ---- Accumulate returns yearly (geometric cumulative return per year) ----
returns_pd['Year'] = pd.to_datetime(returns_pd.index).year
returns_pd['CumulativeReturn'] = (1 + returns_pd[returns_column]).groupby(returns_pd['Year']).cumprod() - 1

returns_spark_df = spark.createDataFrame(returns_pd)

numeric_cols = [f.name for f in returns_spark_df.schema.fields if isinstance(f.dataType, NumericType) and f.name != date_column]

first_row_id = returns_spark_df.select(monotonically_increasing_id().alias('row_id')).orderBy('row_id').limit(1).collect()[0]['row_id']

    returns_spark_df = returns_spark_df.withColumn(
        col_name,
        when(monotonically_increasing_id() == first_row_id, None).otherwise(col(col_name))
    )
