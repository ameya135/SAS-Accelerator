from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Load daily_sales DataFrame from mart schema
daily_sales_df = spark.table('mart.daily_sales')

# Filter rows where grand_total > 0
filtered_sales_df = daily_sales_df.filter(daily_sales_df.grand_total > 0)

# Display the filtered results
print('Final ETL Report')
filtered_sales_df.show()