from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, upper, when

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Function to clean a string column: strip whitespace and convert to uppercase
def clean_string_column(df, field):
    return df.withColumn(field, upper(trim(col(field))))

# Function to calculate tax based on amount and region
def calculate_tax(df, amount_col, region_col, tax_col_name='tax'):
    return df.withColumn(
        tax_col_name,
        when(col(region_col) == 'NA', col(amount_col) * 0.10)
        .when(col(region_col) == 'EU', col(amount_col) * 0.20)
        .otherwise(col(amount_col) * 0.05)
    )

# Example usage:
# df = clean_string_column(df, 'field')
# df = calculate_tax(df, 'amount', 'region')