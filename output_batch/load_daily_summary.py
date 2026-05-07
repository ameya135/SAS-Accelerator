from pyspark.sql import SparkSession, functions as F

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Load the staging.clean_transactions table into a DataFrame
transactions_df = spark.table('staging.clean_transactions')

# Group by 'date', 'region', 'product' and aggregate sums for 'amount', 'tax', and 'total_amount'
daily_sales_df = transactions_df.groupBy('date', 'region', 'product').agg(
    F.sum('amount').alias('total_sales'),
    F.sum('tax').alias('total_tax'),
    F.sum('total_amount').alias('grand_total')
)

# Display the daily sales summary
print('Daily Sales Summary')
daily_sales_df.show()