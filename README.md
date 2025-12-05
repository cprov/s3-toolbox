# S3-toolbox

Assorted S3-related tooling

Currently all the scripts rely on your `~/.aws` configuration.

One may select different profiles by setting `AWS_PROFILE=<profile_name>` before calling the tools.

## Setting things up

```
$ python -m virtualenv venv
...
$ . ./venv/bin/activate
(venv) $ pip install -r requirements.txt
...
```

## "Stress" testing

It runs multiple parallel multipart uploads with a given size into an existing S3 bucket.

```
python s3_stress_test.py -n 10 -b <bucket_name>
[be aware! rapidly refreshing terminal screen]
...
```


## Concurrent bucket listing

It performs a complete scanning of the current S3 account, listing buckets and getting their corresponding ACL and object sizes.

```
 python aio_s3_bucket_listing.py
SYNC  took 32.045184 seconds
ASYNC took 4.626138 seconds
{'name': 'bazinga', 'n_objects': 32, 'bytes': 2147483648, 'public': False}
{'name': 'biscoito-publico-123', 'n_objects': 5, 'bytes': 190160265, 'public': True}
{'name': 'biscuit', 'n_objects': 32, 'bytes': 2147483648, 'public': False}
{'name': 'boing-new', 'n_objects': 1106, 'bytes': 37250570771, 'public': False}
{'name': 'boing-pre-prod', 'n_objects': 32, 'bytes': 2147483648, 'public': False}
{'name': 'mgc-tester', 'n_objects': 32, 'bytes': 2147483648, 'public': False}
{'name': 'obsidian', 'n_objects': 32, 'bytes': 2147483648, 'public': False}
{'name': 'pingo', 'n_objects': 12, 'bytes': 10759346707, 'public': True}
{'name': 's3drive-cprov', 'n_objects': 1, 'bytes': 1048576, 'public': False}
{'name': 'test-mountpoint-s3', 'n_objects': 2, 'bytes': 406851392, 'public': False}
{'name': 'versioned', 'n_objects': 2, 'bytes': 3146898, 'public': False}
```

Bonus (or not), it includes a comparison with the same task done synchronously.

The same tool is also an awsgi handler (thanks FastAPI):

```
python -m granian aio_s3_bucket_listing:app --interface asgi --access-log
[INFO] Starting granian (main PID: 139160)
[INFO] Listening at: http://127.0.0.1:8000
[INFO] Spawning worker-1 with PID: 139161
[INFO] Started worker-1
[INFO] Started worker-1 runtime-1
[2025-12-05 00:09:51 -0300] 127.0.0.1 - "GET /async HTTP/1.1" 200 12892.647
[2025-12-05 00:11:03 -0300] 127.0.0.1 - "GET /sync HTTP/1.1" 200 51322.781
```

Then `curl` is your friend ...

```
$ curl -s http://localhost:8000/async | jq -c
[{"name":"bazinga", ...]

$ curl -s http://localhost:8000/sync | jq -c
[{"name":"bazinga", ...]
```


## Broken or malicious clients

It triggers errors related with broken or malicious clients generating bad S3 signatures.

```
AWS_PROFILE=prod-below python s3_broken_sig.py
[lots of DEBUG messages]
...
2024-03-12 22:14:29,479 botocore.parsers [DEBUG] Response body:
b"<?xml version='1.0' encoding='UTF-8'?>\n<Error><Code>SignatureDoesNotMatch</Code>...
...
```

Use this for message error validation. One should never leak more information than necessary ...
