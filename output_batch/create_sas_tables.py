# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

from pyspark.sql import SparkSession
from pyspark.sql.types import DateType, DoubleType, StructField, StructType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# Assume 'dir' is a Python variable holding the directory path

# 1. Import edhec.csv into DataFrame 'edhec_df'

edhec_df = spark.read.option('header', True).option('inferSchema', True).csv(f'{dir}/test/edhec.csv')

# 2. Export 'prices_df' DataFrame to CSV
prices_df.write.mode('overwrite').option('header', True).csv(f'{dir}/test/prices.csv')

# 3. Define schema for managers.csv for type safety

managers_schema = StructType([
    StructField('Date', DateType(), True),
    StructField('HAM1', DoubleType(), True),
    StructField('HAM2', DoubleType(), True),
    StructField('HAM3', DoubleType(), True),
    StructField('HAM4', DoubleType(), True),
    StructField('HAM5', DoubleType(), True),
    StructField('HAM6', DoubleType(), True),
    StructField('EDHEC_LS_EQ', DoubleType(), True),
    StructField('SP500_TR', DoubleType(), True),
    StructField('US_10Y_TR', DoubleType(), True),
    StructField('US_3m_TR', DoubleType(), True)
])

managers_df = (
    spark.read
    .option('header', True)
    .option('delimiter', ',')
    .option('mode', 'DROPMALFORMED')
    .schema(managers_schema)
    .csv(f'{dir}/test/managers.csv')
)

# 4. Read managers.csv into DataFrame 'managers_df' with schema and proper options
