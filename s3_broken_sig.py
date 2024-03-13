#!/usr/bin/env python3
"""
Use this to emulate "broken or malicious client" errors on S3

Hint: use `AWS_PROFILE=<.aws/config profile>` to check internal and external errors.
"""
import boto3
import botocore


S3_CONFIG = botocore.client.Config(retries={'max_attempts': 0})


def main():

    s3 = boto3.resource('s3', config=S3_CONFIG)

    def _taint_request(request, **kwargs):
        # Internal -> RequestTimeTooSkewed
        # External -> Forbidden
        #request.headers['X-Amz-Date'] = b'20240312T211314Z'
        # Internal -> SignatureDoesNotMatch
        # External -> Forbidden
        request.headers['Authorization'] += b'x'

    _events = s3.meta.client.meta.events
    _events.register_first('before-send.*.*', _taint_request)

    boto3.set_stream_logger(name='botocore')

    buckets = s3.buckets.all()
    print([b.name for b in buckets])


if __name__ == '__main__':
    main()
