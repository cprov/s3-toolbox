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
uvicorn aio_s3_bucket_listing:app --reload
INFO:     Will watch for changes in these directories: ['/home/cprov/Development/Cloud/s3-toolbox']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [757232] using StatReload
INFO:     Started server process [757234]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:39756 - "GET /async HTTP/1.1" 200 OK
INFO:     127.0.0.1:58470 - "GET /sync HTTP/1.1" 200 OK
```

Then `curl` is your friend ...

```
$ curl -s http://localhost:8000/async | jq -c
[{"name":"bazinga", ...]

$ curl -s http://localhost:8000/sync | jq -c
[{"name":"bazinga", ...]
```
