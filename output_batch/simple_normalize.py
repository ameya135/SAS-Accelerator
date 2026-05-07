from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Calculate the sum of the column 'var' and divide by 'sum_param'
s_value = df_data.agg((F.sum(F.col(var)) / F.lit(sum_param)).alias('s')).collect()[0]['s']

# Normalize the column 'var' by dividing by s_value
df_data_normalized = df_data.withColumn(var, F.col(var) / F.lit(s_value))