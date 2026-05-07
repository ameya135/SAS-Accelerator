# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
from pyspark.sql import Row, SparkSession
from pyspark.sql.functions import abs, col, kurtosis, lag, lit, skewness, when
from pyspark.sql.window import Window

spark = SparkSession.builder.appName('SkewnessKurtosisRatioTest').getOrCreate()

# Initialize Spark session

returns = returns.dropna()

# Compute SkewnessKurtosisRatio for each return column

def skew_kurt_ratio(df, cols):

    ratios = {}
    for c in cols:

        sk = df.select(skewness(col(c))).first()[0]

        ku = df.select(kurtosis(col(c))).first()[0]
        if ku is not None and ku != 0:
            ratios[c] = sk / ku
        else:
            ratios[c] = None
    return ratios

skratio_row = Row(date=1, **{c.replace('_ret',''): skratio_dict[c] for c in ret_cols})

skratio = spark.createDataFrame([skratio_row])

# Create skratio DataFrame

    returns_from_r = returns_from_r.withColumnRenamed(c, c.replace('_ret',''))

# Handle empty DataFrames by replacing with error rows
if skratio.count() == 0:

    returns_from_r = None

if skratio is None:

    skratio = spark.createDataFrame([Row(date=-1, IBM=-999, GE=-999, DOW=-999, GOOGL=-999, SPY=-999)])

    returns_from_r = spark.createDataFrame([Row(date=1, IBM=999, GE=999, DOW=999, GOOGL=999, SPY=999)])

# Compare DataFrames and output differences

diff = diff.withColumn('_type_', lit('DIF'))

# Count number of differences

    pass_var = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST SkewnessKurtosisRatio_test')
else:

    pass_var = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST SkewnessKurtosisRatio_test')

# Optionally drop intermediate DataFrames if keep==False
if not keep:

    prices = None

    returns = None

    returns_from_r = None

    skratio = None

    diff = None

    diff_filtered = None

# Macro variables (to be set externally or passed as arguments)
# dir: directory containing prices.csv
# keep: whether to keep intermediate DataFrames (boolean)

# Read prices.csv as DataFrame

prices_path = os.path.join(dir, 'prices.csv')

prices = spark.read.option('header', True).option('inferSchema', True).csv(prices_path)

# Calculate returns (discrete method: (price_t / price_t-1) - 1)

windowSpec = Window.orderBy('date') if 'date' in prices.columns else Window.orderBy(prices.columns[0])

returns = prices
for col_name in prices.columns:
    if col_name.lower() != 'date':

        returns = returns.withColumn(f'{col_name}_ret', (col(col_name) / lag(col(col_name), 1).over(windowSpec)) - 1)

ret_cols = [c for c in returns.columns if c.endswith('_ret')]

skratio_dict = skew_kurt_ratio(returns, ret_cols)

# Prepare returns_from_r DataFrame (mimics importdatasetfromr)

returns_from_r = returns.select('date', *ret_cols)
for c in ret_cols:

    skratio = None
if returns_from_r.count() == 0:

if returns_from_r is None:

diff = skratio.join(returns_from_r, on='date', how='inner') \
    .select(
        'date',
        *[
            when(~(abs(col(f'skratio.{c}') - col(f'returns_from_r.{c}')) < 1e-6), lit(1)).alias(c)
            for c in ['IBM', 'GE', 'DOW', 'GOOGL', 'SPY']
        ]
    )

diff_filtered = diff.where(
    (col('_type_') == 'DIF') & (
        (col('IBM') == 1) | (col('GE') == 1) | (col('DOW') == 1) | (col('GOOGL') == 1) | (col('SPY') == 1)
    )
)

n = diff_filtered.count()

# Set pass/notes variables and print result
if n == 0:
