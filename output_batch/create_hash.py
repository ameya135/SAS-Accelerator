from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Set the dataset name (should match a registered table or DataFrame view)
dataset_name = 'output_df'  # TODO: Verify this value

def create_hash_dict(spark, dict_name, key_cols_str, data_cols_str, dataset_name):
    """
    Create a dictionary for fast lookup from a Spark DataFrame.
    :param spark: SparkSession object
    :param dict_name: Name to assign the resulting dictionary in globals()
    :param key_cols_str: Comma-separated string of key columns
    :param data_cols_str: Comma-separated string of data columns
    :param dataset_name: Name of the Spark table or view
    """
    key_cols = [col.strip() for col in key_cols_str.split(',')]
    data_cols = [col.strip() for col in data_cols_str.split(',')]
    # Select only the required columns for the hash (dict) lookup
    df = spark.table(dataset_name).select(*(key_cols + data_cols))
    # Collect as dictionary: key tuple -> data dict
    result_dict = {
        tuple(row[k] for k in key_cols): {d: row[d] for d in data_cols}
        for row in df.collect()
    }
    globals()[dict_name] = result_dict