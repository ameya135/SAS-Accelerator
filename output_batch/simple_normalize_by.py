# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Step 4: Drop the helper column

df_normalized = df_normalized.drop('group_total')

# Assume 'data' is the table name, 'var' is the column to normalize, and 'by' is a list of grouping columns

# Step 1: Compute group-wise sum of 'var'

group_sum_df = spark.table(data).groupBy(by).agg(F.sum(var).alias('group_total'))

# Step 2: Join original data with group-wise sum

df_with_total = spark.table(data).join(group_sum_df, on=by, how='left')

# Step 3: Normalize 'var' by group total

df_normalized = df_with_total.withColumn(var, F.col(var) / F.col('group_total'))
