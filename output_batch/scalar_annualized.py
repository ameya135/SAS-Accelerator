import math
from pyspark.sql import SparkSession

# Initialize Spark session
spark = SparkSession.builder.appName("SAS_Migration").getOrCreate()

def scalar_annualized(value, scale=1, method='DISCRETE', value_type='VALUE'):
    """
    Annualizes a value based on the specified method and type.
    :param value: Numeric value to annualize
    :param scale: Scaling factor (e.g., number of periods)
    :param method: 'DISCRETE' or 'LOG'
    :param value_type: 'VALUE' or 'STD'
    :return: Annualized value
    """
    method_upper = method.upper()
    value_type_upper = value_type.upper()
    if value_type_upper == 'VALUE':
        if method_upper == 'DISCRETE':
            return (1 + value) ** scale - 1
        elif method_upper == 'LOG':
            return value * scale
    elif value_type_upper == 'STD':
        return value * math.sqrt(scale)
    return None