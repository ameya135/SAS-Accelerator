from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Function to get numeric column names from a DataFrame, excluding specified columns
def get_numeric_column_names(df, exclude_cols):
    """
    Returns a list of numeric column names from the DataFrame, excluding specified columns.
    :param df: Input Spark DataFrame
    :param exclude_cols: String of space-separated column names to exclude
    :return: List of numeric column names
    """
    exclude_set = set(col.strip().upper() for col in exclude_cols.split() if col.strip())
    numeric_types = {'int', 'bigint', 'double', 'float', 'decimal', 'long', 'short'}
    numeric_cols = [
        field.name
        for field in df.schema.fields
        if field.dataType.typeName() in numeric_types and field.name.upper() not in exclude_set
    ]
    return numeric_cols

# Example usage:
# numeric_column_names = get_numeric_column_names(table_df, exclude_cols)