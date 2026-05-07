from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()