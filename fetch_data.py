from db_connect import get_connection
import pandas as pd

conn = get_connection()

df = pd.read_sql("SELECT TOP 10 * FROM LOV_MATERIAL", conn)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', 200)
pd.set_option('display.max_columns', None)

print(df)
