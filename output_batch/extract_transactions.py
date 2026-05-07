# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import DateType, DoubleType, StringType, StructField, StructType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Define schema for transactions DataFrame

transaction_schema = StructType([
    StructField('transaction_id', StringType(), True),
    StructField('region', StringType(), True),
    StructField('amount', DoubleType(), True),
    StructField('product', StringType(), True),
    StructField('date', DateType(), True)
])

# Prepare transaction data

transaction_data = [
    ('T001', 'NA', 100.00, 'WidgetA', datetime.strptime('2023-01-01', '%Y-%m-%d').date()),
    ('T002', 'EU', 200.00, 'WidgetB', datetime.strptime('2023-01-01', '%Y-%m-%d').date()),
    ('T003', 'AS', 150.00, 'WidgetA', datetime.strptime('2023-01-02', '%Y-%m-%d').date()),
    ('T004', 'NA', 120.00, 'WidgetC', datetime.strptime('2023-01-02', '%Y-%m-%d').date()),
    ('T005', 'EU', 250.00, 'WidgetB', datetime.strptime('2023-01-03', '%Y-%m-%d').date())
]

# Create DataFrame with schema

transactions_df = spark.createDataFrame(transaction_data, schema=transaction_schema)

transactions_sorted_df = transactions_df.orderBy('transaction_id')

# Sort the transactions DataFrame by 'transaction_id'
