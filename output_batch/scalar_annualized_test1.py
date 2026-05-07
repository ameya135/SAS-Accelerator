# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, Window, functions as F
from pyspark.sql.functions import pandas_udf
from pyspark.sql.types import DoubleType

spark = SparkSession.builder.appName("annualized_scalar").getOrCreate()

# Initialize Spark session

# Annualized return calculation helper

    returns = np.array(returns)

def annualized_return(returns, scale):

    returns = returns[~np.isnan(returns)]
    if len(returns) == 0:
        return float('nan')

    compounded = np.prod(1 + returns)

    n_periods = len(returns)
    return compounded ** (scale / n_periods) - 1

# Register pandas UDFs for each scale
@pandas_udf(DoubleType())

def scale_4_udf(returns: pd.Series) -> float:
    return annualized_return(returns, 4)

@pandas_udf(DoubleType())

def scale_12_udf(returns: pd.Series) -> float:
    return annualized_return(returns, 12)

@pandas_udf(DoubleType())

def scale_52_udf(returns: pd.Series) -> float:
    return annualized_return(returns, 52)

@pandas_udf(DoubleType())

def scale_252_udf(returns: pd.Series) -> float:
    return annualized_return(returns, 252)

# Add a row index for windowing

prices_sdf = prices_sdf.withColumn('row_num', F.monotonically_increasing_id() + 1)

# Define window spec for cumulative calculation

window_spec = Window.orderBy('row_num').rowsBetween(Window.unboundedPreceding, 0)

# Calculate cumulative returns array up to each row

prices_sdf = prices_sdf.withColumn('returns_array', F.collect_list('ibm_return').over(window_spec))

# Read prices CSV as DataFrame (assume 'dir' is defined elsewhere)

# Calculate annualized returns for each scale

prices_sdf = prices_sdf.withColumn('scale_4', scale_4_udf('returns_array'))

prices_sdf = prices_sdf.withColumn('scale_12', scale_12_udf('returns_array'))

prices_sdf = prices_sdf.withColumn('scale_52', scale_52_udf('returns_array'))

prices_sdf = prices_sdf.withColumn('scale_252', scale_252_udf('returns_array'))

# Select final columns

prices_pdf = pd.read_csv(f'{dir}/prices.csv')
# Select only the 'ibm' column

prices_pdf = prices_pdf[['ibm']].copy()

# Calculate discrete returns
prices_pdf['ibm_return'] = prices_pdf['ibm'].pct_change()
# Keep rows 1 to 100 (first return is NaN)

prices_pdf = prices_pdf.iloc[1:101].reset_index(drop=True)

# Convert to Spark DataFrame

prices_sdf = spark.createDataFrame(prices_pdf)

annualized_scalar = prices_sdf.select('ibm', 'scale_4', 'scale_12', 'scale_52', 'scale_252')
