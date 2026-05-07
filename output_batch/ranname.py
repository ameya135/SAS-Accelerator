from pyspark.sql import SparkSession
import random

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

def generate_random_name():
    """
    Generate a random name string in the format '_XXXXXX',
    where XXXXXX is a zero-padded integer between 000000 and 999999.
    """
    rand_num = round(random.random() * 1000000)
    return f'_{rand_num:06d}'