# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

import os
import numpy as np
import pandas as pd
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("AnnualizedReturnsTest3").getOrCreate()

# Initialize Spark session

    pdf = pdf.sort_values('date')

    returns = np.log(pdf.iloc[:, 1:].div(pdf.iloc[:, 1:].shift(1)))
    returns['date'] = pdf['date']
    return returns.dropna()

# --- Annualized returns calculation ---

def table_annualized_returns(pdf, rf=0.01/4, scale=4, geometric=False, digits=6):

    ann_rets = {}
    for col in pdf.columns:
        if col == 'date':
            continue

        mean_ret = pdf[col].mean()

        ann_ret = (mean_ret - rf) * scale if not geometric else (np.exp(mean_ret * scale) - 1)
        ann_rets[col] = round(ann_ret, digits)
    ann_rets['date'] = pdf['date'].iloc[-1] if len(pdf['date']) > 0 else None
    return pd.DataFrame([ann_rets])

    annualized_table_pd = pd.DataFrame([{'date': -1, 'IBM': -999, 'GE': -999, 'DOW': -999, 'GOOGL': -999, 'SPY': -999}])

    returns_pd = pd.DataFrame([{'date': 1, 'IBM': 999, 'GE': 999, 'DOW': 999, 'GOOGL': 999, 'SPY': 999}])

# --- Compare returns and annualized returns ---

join_cols = ['date']

# Macro variable equivalents (should be set externally or passed as arguments)
# Example: dir = '/path/to/dir', keep = False
# dir, keep must be defined before running this script

# --- Filter for significant differences ---

# --- Count number of differences ---

    pass_test = True

    notes = 'Passed'
    print('NOTE: NO ERROR IN TEST table_Annualized_Returns_TEST3')
else:

    pass_test = False

    notes = 'Differences detected in outputs.'
    print('ERROR: PROBLEM IN TEST table_Annualized_Returns_TEST3')

# --- Cleanup if keep is False ---
if not keep:
    for df_name in ['diff_filtered_sdf', 'prices_sdf', 'annualized_table_sdf', 'returns_sdf']:
        if df_name in locals():
            locals().pop(df_name)

# --- Read prices.csv as DataFrame ---

prices_path = os.path.join(dir, 'prices.csv')

prices_pd = pd.read_csv(prices_path, parse_dates=True, index_col=0)
prices_pd.index.name = 'date'

returns_pd = calculate_log_returns(prices_pd)

returns_sdf = spark.createDataFrame(returns_pd)

annualized_table_pd = table_annualized_returns(returns_pd, rf=0.01/4, scale=4, geometric=False, digits=6)

annualized_table_sdf = spark.createDataFrame(annualized_table_pd)

# --- Handle empty tables by inserting default rows ---
if annualized_table_sdf.count() == 0:

    annualized_table_sdf = spark.createDataFrame(annualized_table_pd)

if returns_sdf.count() == 0:

    returns_sdf = spark.createDataFrame(returns_pd)

diff_sdf = returns_sdf.alias('r').join(annualized_table_sdf.alias('a'), on=join_cols, how='inner') \
    .select(
        F.col('r.date'),
        (F.abs(F.col('r.IBM') - F.col('a.IBM'))).alias('IBM'),
        (F.abs(F.col('r.GE') - F.col('a.GE'))).alias('GE'),
        (F.abs(F.col('r.DOW') - F.col('a.DOW'))).alias('DOW'),
        (F.abs(F.col('r.GOOGL') - F.col('a.GOOGL'))).alias('GOOGL'),
        (F.abs(F.col('r.SPY') - F.col('a.SPY'))).alias('SPY')
    )

diff_filtered_sdf = diff_sdf.filter(
    (F.col('IBM') > 1e-4) | (F.col('GE') > 1e-4) | (F.col('DOW') > 1e-4) | (F.col('GOOGL') > 1e-4) | (F.col('SPY') > 1e-4)
)

n = diff_filtered_sdf.count()

# --- Test result reporting ---
if n == 0:

prices_sdf = spark.createDataFrame(prices_pd.reset_index())

# --- Calculate log returns ---

def calculate_log_returns(pdf):
