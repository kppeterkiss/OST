# Setup: In Google Colab run: !pip install pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, rand

# 1. Initialize SparkSession (Simulating a 4-core cluster locally)
spark = SparkSession.builder \
    .appName("OpenSource_Class1_Catalyst") \
    .master("local[4]") \
    .config("spark.sql.adaptive.enabled", "false") \
    .getOrCreate()

# 2. Generate 1,000,000 synthetic log records across 4 partitions
df = spark.range(0, 1_000_000, numPartitions=4) \
    .withColumn("status_code", (rand(seed=42) * 5 + 200).cast("int")) \
    .withColumn("latency_ms", (rand(seed=7) * 500).cast("int"))

# 3. Write as Parquet (Columnar storage with built-in statistics)
df.write.mode("overwrite").parquet("/tmp/server_logs.parquet")

# 4. Lazy Evaluation & Predicate Pushdown
# Notice: No computation happens when defining these transformations
read_df = spark.read.parquet("/tmp/server_logs.parquet")
filtered_df = read_df.filter(col("status_code") == 200).select("id", "latency_ms")

# 5. Inspect the Physical Plan
print("=== Catalyst Physical Execution Plan ===")
filtered_df.explain(True)
# Point out to students: 'PushedFilters: [IsNotNull(status_code), EqualTo(status_code,200)]'
# The engine filters data while reading from disk, avoiding memory loading of unused rows.