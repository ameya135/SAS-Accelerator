# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import datetime as dt
import re
import requests
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, log
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# ---------------------------
# User-defined parameters
# ---------------------------
# Replace these with actual values or pass as function arguments

period2 = date_to_timestamp(to_date) if to_date else int((dt.datetime.now() - dt.timedelta(days=1)).timestamp())

# ---------------------------
# Download Yahoo Finance CSV
# ---------------------------

session = requests.Session()

resp = session.get(f'https://uk.finance.yahoo.com/quote/{symbol}/history')

txt = resp.text

cookie = resp.cookies.get('B', '')

pattern = re.compile(r'.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')

crumb = None
for line in txt.splitlines():

interval = 'mo'           # e.g., 'mo'

    m = pattern.match(line)
    if m is not None:

def date_to_timestamp(date_str):
    y, m, d = [int(x) for x in date_str.split('-')]
    return int(dt.datetime(y, m, d).timestamp())

        crumb = m.groupdict()['crumb']
        break
if crumb is None:
    raise Exception('Could not find crumb')

url = (
    f'https://query1.finance.yahoo.com/v7/finance/download/{symbol}'
    f'?period1={period1}&period2={period2}&interval=1{interval}&events=history&crumb={crumb}'
)

csv_response = session.get(url, cookies={'B': cookie})

csv_text = csv_response.text

# ---------------------------
# Initialize Spark session
# ---------------------------

# ---------------------------
# Read and preprocess data
# ---------------------------

price_column = 'adj_close'  # e.g., 'adj_close'

df = df.filter(col('Date').isNotNull())

# Optionally keep price DataFrame
if keep_price:

    df_price = df

# ---------------------------
# Calculate returns
# ---------------------------

window_spec = Window.orderBy('Date')
if log_return:

from_date = '2023-01-01'    # e.g., '2023-01-01'

period1 = date_to_timestamp(from_date) if from_date else int((dt.datetime.now() - dt.timedelta(days=365)).timestamp())

# Remove first row with null return

to_date = '2024-01-01'      # e.g., '2024-01-01'

keep_price = 1              # 0 or 1

log_return = 1              # 0 or 1

symbol = 'AAPL'             # e.g., 'AAPL'

csv_file_path = f'/tmp/{symbol.replace("-", "_")}.csv'
with open(csv_file_path, 'w') as f:
    f.write(csv_text)

df = spark.read.option('header', True).option('inferSchema', True).csv(csv_file_path)

symbol_name = symbol.replace('-', '_')

# Rename price column to symbol_name (replace '-' with '_')

df = df.withColumnRenamed(price_column, symbol_name)

# Select only Date and symbol_name columns, sort by Date

df = df.select('Date', symbol_name).orderBy('Date')

    df = df.withColumn(symbol_name, log(col(symbol_name) / lag(col(symbol_name, 1).over(window_spec))))
else:

    df = df.withColumn(symbol_name, (col(symbol_name) / lag(col(symbol_name, 1).over(window_spec))) - 1)

df = df.filter(col(symbol_name).isNotNull())

# ---------------------------
# Helper function: Date to timestamp
# ---------------------------
