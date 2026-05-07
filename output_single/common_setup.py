from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, upper, when

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Function to clean a string column: upcase(strip(column))
def clean_string_column(df, column_name):
    return df.withColumn(column_name, upper(trim(col(column_name))))

# Function to calculate tax based on amount and region
def calculate_tax(df, amount_col, region_col, tax_col='tax'):
    return df.withColumn(
        tax_col,
        when(col(region_col) == 'NA', col(amount_col) * 0.10)
        .when(col(region_col) == 'EU', col(amount_col) * 0.20)
        .otherwise(col(amount_col) * 0.05)
    )

# Example usage:
# df = clean_string_column(df, 'field')
# df = calculate_tax(df, 'amount', 'region')