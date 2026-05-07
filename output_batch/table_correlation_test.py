from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("sas_migration").getOrCreate()