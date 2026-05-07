# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Frequency count for 'region'

# Frequency count for 'high_value_flag'

# Utility functions

def clean_string(col):
    """Remove non-alphanumeric characters and trim whitespace."""
    return F.trim(F.regexp_replace(col, '[^A-Za-z0-9 ]', ''))

def calc_tax(amount_col, region_col):
    """Calculate tax based on region."""
    return (
        F.when(region_col == 'CA', amount_col * 0.08)
         .when(region_col == 'NY', amount_col * 0.09)
         .otherwise(amount_col * 0.07)
    )

# Load raw transactions data

raw_transactions_df = spark.table('staging.raw_transactions')

# Clean and transform data

clean_transactions_df = (
    raw_transactions_df
    .withColumn('product', clean_string(F.col('product')))
    .withColumn('region', clean_string(F.col('region')))
    .withColumn('tax', calc_tax(F.col('amount'), F.col('region')))
    .withColumn('total_amount', F.col('amount') + F.col('tax'))
    .withColumn('high_value_flag', F.when(F.col('total_amount') > 200, F.lit(1)).otherwise(F.lit(0)))
)

region_freq_df = (
    clean_transactions_df
    .groupBy('region')
    .count()
    .orderBy('region')
)

high_value_flag_freq_df = (
    clean_transactions_df
    .groupBy('high_value_flag')
    .count()
    .orderBy('high_value_flag')
)

# Uncomment to save cleaned data to table
# clean_transactions_df.write.mode('overwrite').saveAsTable('staging.clean_transactions')
