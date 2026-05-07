# Generated PySpark code from SAS migration
# Execution order optimized by ExecutionOrderOptimizer

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lag, last as spark_last, lit
from pyspark.sql.window import Window

spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

# Initialize Spark session

    temp_beta = CAPM_alpha_beta(returns, BM=BM, Rf=0, dateColumn=dateColumn)

    temp_beta = temp_beta.filter(col('_stat_') == 'Betas')
else:

    temp_beta = Systematic_Risk(returns, BM=BM, Rf=0, scale=scale, VARDEF=VARDEF, dateColumn=dateColumn)

    temp_treynor = temp_treynor.withColumn(f'Treynor_{v}', 
                                           col(v) / col(f'{v}_beta') if f'{v}_beta' in temp_treynor.columns else lit(None))

# Drop intermediate columns if present

drop_cols = [BM, dateColumn, '_stat_']

temp_treynor = temp_treynor.drop(*[c for c in drop_cols if c in temp_treynor.columns])

# Add _STAT_ column

temp_treynor = temp_treynor.withColumn('_STAT_', lit('Treynor Ratio'))

# Select only the last row based on dateColumn

window_last = Window.orderBy(col(dateColumn).asc()).rowsBetween(Window.unboundedPreceding, Window.unboundedFollowing)

temp_treynor = temp_treynor.withColumn('last_row', spark_last(col(dateColumn)).over(window_last))

# Get list of variable columns to process

vars = get_number_column_names(returns, exclude=[dateColumn, 'Rf', BM])

# Calculate Treynor Ratio for each variable in vars
for v in vars:
    # Avoid division by zero

# Calculate excess returns and annualize them

temp_rp = return_excess(returns, Rf=0, dateColumn=dateColumn)

# Join temp_rp and temp_beta on variable columns

join_cols = [v for v in vars if v in temp_beta.columns and v in temp_rp.columns]

temp_treynor = temp_rp.join(temp_beta, on=join_cols, how='inner')

last_date = temp_treynor.agg({"last_row": "max"}).collect()[0][0]

outData = temp_treynor.filter(col(dateColumn) == last_date).drop('last_row')

# outData now contains the final Treynor Ratio results

# Assume macro variables are provided as Python variables: outData, method, scale, BM, dateColumn, modified, VARDEF
# Helper functions for return_excess, return_annualized, CAPM_alpha_beta, Systematic_Risk, get_number_column_names must be implemented elsewhere

temp_rp = return_annualized(temp_rp, scale=scale, method=method, dateColumn=dateColumn)

# Calculate beta or systematic risk depending on 'modified' flag
if not modified:
