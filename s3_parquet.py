import argparse
import pandas as pd
import boto3
import pyarrow.parquet as pq
import pyarrow as pa
from io import BytesIO
from typing import List, Union, Optional
import datetime


class S3ParquetProcessor:
    def __init__(
        self,
        bucket_name: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        """
        Initialize S3 Parquet processor

        Parameters:
        -----------
        bucket_name: str
            S3 bucket name
        aws_access_key_id: str
            AWS access key
        aws_secret_access_key: str
            AWS secret key
        endpoint_url: str
            MGC endpoint_url
        """
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url,
        )
        self.bucket_name = bucket_name

    def list_parquet_files(self, prefix: str) -> List[str]:
        """List all parquet files in the specified S3 prefix"""
        parquet_files = []
        paginator = self.s3_client.get_paginator('list_objects_v2')

        for page in paginator.paginate(Bucket=self.bucket_name, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    if obj['Key'].endswith('.parquet'):
                        parquet_files.append(obj['Key'])

        return parquet_files

    def read_parquet_file(self, s3_key: str) -> pd.DataFrame:
        """Read a single parquet file from S3"""
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
        parquet_buffer = BytesIO(response['Body'].read())
        return pd.read_parquet(parquet_buffer)

    def read_multiple_parquet_files(
        self,
        s3_keys: List[str],
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Read and concatenate multiple parquet files"""
        dfs = []
        for key in s3_keys:
            df = self.read_parquet_file(key)
            if columns:
                df = df[columns].dropna()
            if not df.empty:
                dfs.append(df)
        return pd.concat(dfs, ignore_index=True)



def main():
    parser = argparse.ArgumentParser(description='Process parquet files ...')
    parser.add_argument('bucket_name', type=str, default='zoing', help='Name of the S3 bucket')
    parser.add_argument('-p', '--preffix', type=str, default='raw_data/', help='File prefix')
    args = parser.parse_args()

    aws_params = {
        "bucket_name": args.bucket_name
        # Use `AWS_PROFILE` env_var to select an existing configuration or
        # knock yourself out with local overrides.
        #"aws_access_key_id": "your_aws_access_key",
        #"aws_secret_access_key": "your_aws_secret_key",
        #"endpoint_url": "https://br-se1.magaluobjects.com"
    }
    processor = S3ParquetProcessor(**aws_params)

    print("Branches summary:")
    df = processor.read_parquet_file('branches')
    print(df)

    print("\nCatalog summary:")
    df = processor.read_parquet_file('catalog')
    print(df)
    print()

    parquet_files = processor.list_parquet_files(args.preffix)
    print(f"Found {len(parquet_files)} weeks of sales.")

    if parquet_files:
        df = processor.read_multiple_parquet_files(parquet_files)
        #print("\nData summary:")
        #print(df.columns)
        #print(df.describe())

        daily_summary = df.groupby([
            df['acronym'],
            df['confirm_date'].dt.date,
            df['code']
        ]).agg({
            'price': ['sum', 'mean'],
            'quantity': ['sum', 'mean']
        }).sort_values(
            by=['confirm_date', 'acronym']
        )
        print("\nDaily SaleItem summary:")
        print(daily_summary)





if __name__ == "__main__":
    main()
