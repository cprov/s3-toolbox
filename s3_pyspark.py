#
# Follow https://spark.apache.org/docs/latest/api/python/getting_started/install.html
#
# $ pip install pyspark boto3
# $ aws --profile <profile> s3 mb s3://pyspark-sandbox
# $ AWS_PROFILE=<profile> python s3_pyspark.py
#

import boto3
from datetime import datetime, date

import pyspark
from pyspark.sql import SparkSession, Row


def setupSpark():
    # Retrieve pre-configured credentials from the aws CLI (~/.aws/{config, credentials})
    session = boto3.session.Session()
    credentials = session.get_credentials().get_frozen_credentials()
    # Eew!
    endpoint_url = session._session.full_config['profiles'][session._session.profile]['endpoint_url']

    # Connect to local spark setting the correct __ and exoteric __ configuration to access MGC OBJS using 's3a:'
    spark = SparkSession.builder\
        .appName("Demo MGC OBJS") \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk-pom:1.12.365") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
        .config('spark.hadoop.fs.s3a.impl', 'org.apache.hadoop.fs.s3a.S3AFileSystem') \
        .config('spark.hadoop.fs.s3a.access.key', credentials.access_key) \
        .config('spark.hadoop.fs.s3a.secret.key', credentials.secret_key) \
        .config('spark.hadoop.fs.s3a.endpoint',  endpoint_url) \
        .enableHiveSupport() \
        .getOrCreate()

    return spark


def main():
    spark = setupSpark()

    # Create a sample data frame
    df = spark.createDataFrame([
        Row(a=1, b=2., c='string1', d=date(2000, 1, 1), e=datetime(2000, 1, 1, 12, 0)),
        Row(a=2, b=3., c='string2', d=date(2000, 2, 1), e=datetime(2000, 1, 2, 12, 0)),
        Row(a=4, b=5., c='string3', d=date(2000, 3, 1), e=datetime(2000, 1, 3, 12, 0))
    ])

    # Write the data frame to MGC OBJS ... XXX currently taking ages
    df.write.parquet("s3a://pyspark-sandbox/test.parquet", mode="overwrite")

    # Recover the data frame from MGC OBJS
    df = spark.read.parquet("s3a://pyspark-sandbox/test.parquet")
    df.show()


if __name__ == '__main__':
    main()
