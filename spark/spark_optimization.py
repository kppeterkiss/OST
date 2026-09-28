# -------------------------------------------------------------
# STEP 1: Environment Setup & Spark Session
# -------------------------------------------------------------
# In Google Colab, execute: !pip install pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, rand, floor, when, concat, lit, explode

spark = SparkSession.builder \
    .appName("ELTE_OpenSource_SparkLab") \
    .master("local[4]") \
    .config("spark.driver.memory", "4g") \
    .config("spark.sql.adaptive.enabled", "false") \
    .config("spark.sql.autoBroadcastJoinThreshold", -1) \
    .getOrCreate()

# -------------------------------------------------------------
# STEP 2: Generate Datasets (Transactions & Categories)
# -------------------------------------------------------------
# small_df: Dimension lookup table (10 categories)
categories = [
    (0, "Electronics", 0.27),
    (1, "Books", 0.05),
    (2, "Home & Kitchen", 0.27),
    (3, "Clothing", 0.27),
    (4, "Sports", 0.27),
    (5, "Automotive", 0.27),
    (6, "Health", 0.05),
    (7, "Toys", 0.27),
    (8, "Garden", 0.27),
    (9, "Groceries", 0.05)
]
small_df = spark.createDataFrame(categories, ["category_id", "category_name", "vat_rate"])

# large_df: Fact table (1,000,000 transactions across 4 partitions)
# Keys 0 to 9 are distributed uniformly
large_df = spark.range(0, 1_000_000, numPartitions=4) \
    .withColumnRenamed("id", "transaction_id") \
    .withColumn("category_id", floor(rand(seed=42) * 10).cast("int")) \
    .withColumn("amount", (rand(seed=7) * 450 + 50).cast("decimal(10,2)"))

# -------------------------------------------------------------
# STEP 3: Inspect Data & Partitions (What are we working with?)
# -------------------------------------------------------------
print("=== 1. Schema Inspection ===")
large_df.printSchema()
small_df.printSchema()

print("=== 2. Row Preview ===")
large_df.show(5)
small_df.show(10, truncate=False)

print("=== 3. Partition Diagnostics ===")
print(f"Number of partitions in large_df: {large_df.rdd.getNumPartitions()}")
print(f"Total transactions: {large_df.count():,}")
print(f"Total categories:   {small_df.count():,}")

# -------------------------------------------------------------
# STEP 4: Demonstrating Sort-Merge Join vs Broadcast Join
# -------------------------------------------------------------
# Standard Join: Catalyst defaults to Sort-Merge Join (Heavy Shuffle)
smj_df = large_df.join(small_df, on="category_id")

# Broadcast Join: Driver replicates small_df to all 4 executor cores (Zero Shuffle)
from pyspark.sql.functions import broadcast
bhj_df = large_df.join(broadcast(small_df), on="category_id")

# -------------------------------------------------------------
# STEP 5: Simulating Severe Data Skew & Key Salting
# -------------------------------------------------------------
# 80% of transactions are assigned to category_id = 0 (Straggler bottleneck)
skewed_df = large_df.withColumn(
    "category_id",
    when(rand(seed=99) < 0.80, lit(0)).otherwise(col("category_id"))
)

# Apply Salting across 4 sub-partitions
SALT_FACTOR = 4
salted_large = skewed_df.withColumn(
    "salted_key",
    concat(col("category_id"), lit("_"), floor(rand() * SALT_FACTOR))
)

# Replicate the dimension table entries 4 times to preserve join completeness
salted_small = small_df.withColumn("salt_array", lit(list(range(SALT_FACTOR)))) \
    .withColumn("salt", explode("salt_array")) \
    .withColumn("salted_key", concat(col("category_id"), lit("_"), col("salt"))) \
    .drop("salt_array", "salt")

print("=== Salted Data Preview ===")
salted_large.select("transaction_id", "category_id", "salted_key").show(5)
salted_small.select("category_id", "category_name", "salted_key").show(8)