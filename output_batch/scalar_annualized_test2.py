# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, round as pyspark_round
from pyspark.sql.types import DoubleType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# --- Collect 'ibm' values for later use (if needed) ---

# --- Annualization logic ---

scales = [4, 12, 52, 252]

annualized_col_names = []

for scale in scales:

    col_name = f'scale_{scale}'
    # For log returns, annualized = ibm_return * scale

    prices_df = prices_df.withColumn(col_name, pyspark_round(col('ibm_return') * scale, 10))
    annualized_col_names.append(col_name)

# --- Assemble results DataFrame ---

results_df = results_df.withColumnRenamed('ibm_return', 'ibm')

# 'results_df' now contains: ibm, scale_4, scale_12, scale_52, scale_252

# --- Read and preprocess prices data ---
# Replace 'dir' with your directory path as needed

prices_pdf = pd.read_csv(f'{dir}/prices.csv')

prices_pdf = prices_pdf[['ibm']]  # Keep only 'ibm' column

# Calculate log returns
prices_pdf['ibm_return'] = np.log(prices_pdf['ibm'] / prices_pdf['ibm'].shift(1))

prices_pdf = prices_pdf.iloc[1:101].reset_index(drop=True)  # Keep rows 1 to 100

# Convert to Spark DataFrame

prices_df = spark.createDataFrame(prices_pdf)

ibm_values = [row['ibm'] for row in prices_df.select('ibm').collect()]

results_df = prices_df.select(['ibm_return'] + annualized_col_names)
