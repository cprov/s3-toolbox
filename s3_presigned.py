#!/usr/bin/env python3
"""
Use this to generate presigned URLs for S3

Hint: use `AWS_PROFILE=<.aws/config profile>` to check internal and external errors.
"""
import argparse
import boto3
import botocore


S3_CONFIG = botocore.client.Config(retries={"max_attempts": 0})

def main():
    parser = argparse.ArgumentParser(description="s3 Presigned")
    parser.add_argument(
        "key", nargs="?", default="test.txt",
        help="Key (object) name, default to 'test.txt'")
    args = parser.parse_args()
    s3 = boto3.resource('s3', config=S3_CONFIG)
    info = s3.meta.client.generate_presigned_url(
        ClientMethod="put_object", HttpMethod="PUT",
        Params={"Bucket": "iot-demo", "Key": args.key})
    print(info)


if __name__ == '__main__':
    main()
