import mysql.connector
import redis
import pickle
from pprint import pprint as pp
from timeit_decorator import timeit
import hashlib

# docker inspect mysql | grep IPAddress to get IP
db = mysql.connector.connect(
    host="127.0.0.1", 
    user="ck",
    password="rootp",
    database="fin_db"
)
cursor = db.cursor()

# Query MySQL if Cache Miss
print("Executing query...")

# Redis Connection
cache = redis.StrictRedis(host='localhost', port=6379, decode_responses=False)

@timeit(log_level=None)  # Ensure log_level=None to print directly to console
def execute_query(query):
  redis_working = True
  sql_hash = hashlib.sha256(query.encode()).hexdigest()
  cache_key = f"query:{sql_hash}"
  # print("Hash: ", sql_hash)

  try:
    cached_data = cache.get(cache_key)
    if cached_data:
      print("Cache hit!")
      return pickle.loads(cached_data)
  except Exception as e:
    redis_working = False
    raise "***** Error accessing REDIS"
    # print("***** Error accessing REDIS")
  
  cursor.execute(query)
  result = cursor.fetchall()

  if result and redis_working:
    # Store result in Redis with TTL of 3600 seconds
    cache.setex(cache_key, 3600, pickle.dumps(result))
    print("Data retrieved from MySQL and cached")
  
  return result



# Example usage
print("Fetching users...")
# sql = "SELECT * FROM User , (SELECT SLEEP(3)) AS delay"
# sql = "SELECT * FROM User"
sql = "SELECT * FROM User u JOIN Email e ON u.UserID = e.UserID"
sql = f"{sql} , (SELECT SLEEP(3)) AS delay;"
# res = execute_query(sql)
print(execute_query(sql))  # First call => cache miss
print("\n\nFetching users again....")
# res = execute_query(sql)
print(execute_query(sql))   # cache hit