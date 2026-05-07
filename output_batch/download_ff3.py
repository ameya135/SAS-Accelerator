# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import io
import requests
import tempfile
import zipfile
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, StructField, StructType

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

    tmp_csv_path = tmp_csv.name

# Define schema for the Fama-French 3-factor data

ff3_schema = StructType([
    StructField('Date', DateType(), True),
    StructField('Mkt_RF', DoubleType(), True),
    StructField('SMB', DoubleType(), True),
    StructField('HML', DoubleType(), True),
    StructField('RF', DoubleType(), True)
])

# Read the CSV into a DataFrame

ff3_df = spark.read.csv(tmp_csv_path, header=True, schema=ff3_schema, mode='DROPMALFORMED')

# Filter out rows with missing Date

ff3_df = ff3_df.filter(F.col('Date').isNotNull())

# Divide Mkt_RF, SMB, HML, RF by 100
for col in ['Mkt_RF', 'SMB', 'HML', 'RF']:

    ff3_df = ff3_df.withColumn(col, F.col(col) / 100)

# Download and extract CSV from zip file

url = 'http://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip'

response = requests.get(url)

zip_bytes = io.BytesIO(response.content)

with zipfile.ZipFile(zip_bytes) as zf:

    csv_filename = [name for name in zf.namelist() if name.endswith('.CSV')][0]
    with zf.open(csv_filename) as csvfile:

        csv_data = csvfile.read()

# Save CSV to a temporary file for Spark to read
with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_csv:
    tmp_csv.write(csv_data)
