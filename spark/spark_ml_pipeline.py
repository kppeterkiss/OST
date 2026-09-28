# 1. Install pyspark if in Colab: !pip install pyspark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when
from pyspark.ml.feature import VectorAssembler, StandardScaler, StringIndexer
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline
from pyspark.ml.evaluation import BinaryClassificationEvaluator

# Initialize local SparkSession
spark = SparkSession.builder \
    .appName("ML_Master_Spark_Lab") \
    .master("local[*]") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

# Create synthetic tabular dataset
data = [
    (25, 50000.0, "Private", 0),
    (38, 110000.0, "Public", 1),
    (42, 85000.0, "Private", 1),
    (19, 22000.0, "Self-Emp", 0),
    (55, 140000.0, "Public", 1),
    (31, 62000.0, "Private", 0),
    (48, 92000.0, "Self-Emp", 1),
    (22, 29000.0, "Private", 0)
]
columns = ["age", "income", "sector", "default"]
df = spark.createDataFrame(data, schema=columns)

# 2. Inspect Lazy Execution: Transformations vs Actions
filtered_df = df.filter(col("age") > 20)  # Transformation (instant, no execution)
print("Physical Plan for Filter:")
filtered_df.explain()  # Shows execution DAG without pulling data

# 3. Build a reproducible ML Pipeline
# Step A: Index categorical strings to numeric indexes
sector_indexer = StringIndexer(inputCol="sector", outputCol="sector_idx")

# Step B: Assemble all features into a single dense vector column
assembler = VectorAssembler(
    inputCols=["age", "income", "sector_idx"],
    outputCol="raw_features"
)

# Step C: Scale the features
scaler = StandardScaler(inputCol="raw_features", outputCol="features")

# Step D: Classifier
lr = LogisticRegression(featuresCol="features", labelCol="default")

# Package into a Pipeline
pipeline = Pipeline(stages=[sector_indexer, assembler, scaler, lr])

# 4. Train-Test Split & Fit
train_df, test_df = df.randomSplit([0.7, 0.3], seed=42)
model = pipeline.fit(train_df)

# 5. Evaluate Predictions
predictions = model.transform(test_df)
predictions.select("age", "income", "probability", "prediction", "default").show()

evaluator = BinaryClassificationEvaluator(labelCol="default", metricName="areaUnderROC")
auc = evaluator.evaluate(predictions)
print(f"Test AUC: {auc:.3f}")

# Stop the session
spark.stop()