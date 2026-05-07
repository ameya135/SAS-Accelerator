# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.functions import abs as pyspark_abs, col, lag, udf
from pyspark.sql.types import BooleanType
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

# --- 2. Read prices.csv into Spark DataFrame ---

# --- 3. Calculate returns in Spark (to be compared with reference) ---

window_spec = Window.orderBy('date')

    returns_spark = returns_spark.withColumn(f'{col_name}_prev', lag(col(col_name)).over(window_spec))

    returns_spark = returns_spark.withColumn(
        col_name, 
        (col(col_name) - col(f'{col_name}_prev')) / col(f'{col_name}_prev')
    )

    returns_spark = returns_spark.drop(f'{col_name}_prev')

returns_spark = returns_spark.dropna()

join_cols = ['date']

for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    diff = diff.withColumn(f'{col_name}_DIF', pyspark_abs(col(f'ref.{col_name}') - col(f'calc.{col_name}')))

# Define a fuzz function (tolerance for floating point comparison)

def fuzz(x):
    return x is not None and x < 1e-8

fuzz_udf = udf(fuzz, BooleanType())

for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

    diff = diff.withColumn(f'fuzz_{col_name}', fuzz_udf(col(f'{col_name}_DIF')))

# Macro variable equivalents

# Filter rows where any difference is above tolerance

    pass_var = True

    notes = 'Passed'
else:
    print('ERROR: PROBLEM IN TEST RETURN_CALCULATE_TEST1')

    pass_var = False

    notes = 'Differences detected in outputs.'

# --- 6. Optionally clean up intermediate DataFrames if not keeping ---
if not keep_intermediate:
    # In PySpark, explicit deletion is not usually necessary, but can be done if desired
    pass

# End of migration

dir_path = os.environ.get('DIR_MACRO_VARIABLE', '/path/to/dir')  # Set this appropriately

prices_spark = spark.read.csv(os.path.join(dir_path, 'prices.csv'), header=True, inferSchema=True)

returns_spark = prices_spark
for col_name in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']:

keep_intermediate = False  # Set to True to keep intermediate DataFrames

# --- 1. Read prices.csv as pandas DataFrame and calculate returns (reference implementation) ---

prices_pd = pd.read_csv(os.path.join(dir_path, 'prices.csv'), parse_dates=True, index_col=0)

returns_pd = prices_pd.pct_change().dropna()
returns_pd.reset_index(inplace=True)
returns_pd.rename(columns={'index': 'date'}, inplace=True)

returns_ref = spark.createDataFrame(returns_pd)

# --- 4. Compare returns_ref and returns_spark DataFrames ---

diff = returns_ref.alias('ref').join(returns_spark.alias('calc'), on=join_cols, how='outer')

diff_filtered = diff.filter(
    ~(col('fuzz_IBM') & col('fuzz_GE') & col('fuzz_DOW') & col('fuzz_GOOGL') & col('fuzz_SPY'))
)

n_diff = diff_filtered.count()

# --- 5. Set pass/notes based on comparison result ---
if n_diff == 0:
    print('NOTE: NO ERROR IN TEST RETURN_CALCULATE_TEST1')

# Convert pandas DataFrame to Spark DataFrame
