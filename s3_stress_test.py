#!/usr/bin/env python3

"""
s3 Stress Test

This script uploads a specified number of objects to an S3 bucket, with each object being larger than the previous one
by a specified ratio. The uploads are done in parallel using a ThreadPoolExecutor and the transfer rates of each
upload are calculated and plotted.

Usage:
    s3_stress_test.py [-h] [-n NUM_OBJECTS] [-b BUCKET_NAME] [-r RATIO]

Options:
    -h, --help            show this help message and exit
    -n NUM_OBJECTS, --num_objects NUM_OBJECTS
                        Number of objects to upload (default: 50)
    -b BUCKET_NAME, --bucket_name BUCKET_NAME
                        Name of the S3 bucket (default: testnmg)
    -r RATIO, --ratio RATIO
                        Ratio by which the object size will be multiplied with each iteration (default: 1)
"""
# Author: Lucas Dousse
# Created on: 2023-02-13

import argparse
import boto3
import os
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Create an S3 client
#aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
#aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
#boto3.setup_default_session(profile_name='mgl1-prod')
s3 = boto3.resource('s3')
#, endpoint_url='https://br-ne-1.magaluobjects.com',
#                    aws_access_key_id=aws_access_key_id,
#                    aws_secret_access_key=aws_secret_access_key)


class ProgressPercentage(object):

    def __init__(self, filename, size, index):
        self._filename = filename
        self._size = size
        self._index = index
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\033[%d;0f%s  %s / %s  (%.2f%%)" % (
                    self._index + 1, self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

TRANSFER_CONFIG = boto3.s3.transfer.TransferConfig(
    use_threads=True,
    max_concurrency=5,
    multipart_threshold=16*1024*1024)

# Upload object to S3
def upload_object(bucket, object_key, size, index):
    start = time.time()

    with tempfile.TemporaryFile() as fp:
        fp.truncate(size)
        fp.seek(0)
        bucket.upload_fileobj(
            fp,
            object_key,
            Config=TRANSFER_CONFIG,
            Callback=ProgressPercentage(object_key, size, index))

    end = time.time()
    duration = end - start
    return index, size, duration


def main():
    # Parse the command-line arguments
    parser = argparse.ArgumentParser(description='s3 Stress Test')
    parser.add_argument('-n', '--num_objects', type=int, default=50, help='Number of objects to upload')
    parser.add_argument('-b', '--bucket_name', type=str, default='testnmg', help='Name of the S3 bucket')
    parser.add_argument('-r', '--ratio', type=int, default=1, help='Ratio by which the object size will be multiplied with each iteration')
    parser.add_argument('-s', '--size', type=int, default=2, help='Object size in MB')
    parser.add_argument('-p', '--plot', type=bool, default=False, help='Plot results')
    parser.add_argument('-z', '--preffix', type=str, default='', help='File prefix')
    args = parser.parse_args()

    # Get the specified S3 bucket
    bucket = s3.Bucket(args.bucket_name)

    # Lists to store the sizes and upload times of the objects
    sizes = []
    times = []

    # Initialize the object size according to the command-line argument
    object_size = 1024 * 1024 * args.size

    # Create a ThreadPoolExecutor with a maximum of 100 workers
    executor = ThreadPoolExecutor(max_workers=100)

    # List to store the futures for the uploaded objects
    futures = []

    # Define the object prefix
    object_prefix = f'{args.preffix}stress-test/'

    # Upload the objects in parallel
    for i in range(args.num_objects):
        object_key = f'{object_prefix}{i:02}'
        futures.append(executor.submit(upload_object, bucket, object_key, object_size, i))
        sizes.append(object_size)
        object_size *= args.ratio

    # clear screen
    sys.stdout.write('\033[2J\033[H')
    sys.stdout.flush()

    _start = time.time()
    # Wait for all the futures to complete and track the progress with tqdm
    for future, size in zip(futures, sizes):
        index, size, duration = future.result()
        sys.stdout.write("\033[%d;0f" % (index + 1) )
        transfer_rate = (size * 8) / (duration * 1024 * 1024)
        times.append(duration)
        print(f"Uploaded object of size {size / 1024 / 1024:.2f} MB in {duration:.2f} seconds with transfer rate {transfer_rate:.2f} MiB/s")
    _stop = time.time()

    _duration = _stop - _start
    _size_mb = sum(sizes) / 1024 / 1024
    print(f"Uploaded a total of {_size_mb:.2f} MB in {_duration:.2f} seconds with total transfer rate {(_size_mb * 8)/_duration:.2f} MiB/s")

    if not args.plot:
        return

    import matplotlib.pyplot as plt
    import numpy as np

    # Calculate transfer rates in MiB/s
    transfer_rates = [(size * 8) / (time * 1024 * 1024) for size, time in zip(sizes, times)]

    # Calculate average transfer rate
    avg_transfer_rate = np.mean(transfer_rates)

    # Plot the results
    plt.plot(transfer_rates)
    plt.axhline(y=avg_transfer_rate, color='r', linestyle='--')
    plt.xlabel('Object Index')
    plt.ylabel('Transfer Rate (MiB/s)')
    plt.title('s3 Stress Test Results')
    plt.savefig("transfer_rates.png")


if __name__ == '__main__':
    main()
