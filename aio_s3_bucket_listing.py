import aioboto3
import asyncio
import botocore
from contextlib import ContextDecorator
from fastapi import FastAPI
from time import perf_counter


app = FastAPI()
PUBLIC_URI = 'http://acs.amazonaws.com/groups/global/AllUsers'
S3_CONFIG = botocore.client.Config(connect_timeout=10, read_timeout=10, retries={'max_attempts': 0})


@app.get("/")
async def root():
    return {"Hello": "World"}


async def get_bucket_info(bucket):
    async def _get_sizes(b):
        return [await obj.size async for obj in b.objects.all()]
    async def _get_public(b):
        acl = await bucket.Acl()
        return any(grantee["Grantee"].get("URI") == PUBLIC_URI for grantee in await acl.grants)
    public, sizes = await asyncio.gather(_get_public(bucket), _get_sizes(bucket))
    return {"name": bucket.name, "n_objects": len(sizes), "bytes": sum(sizes), "public": public}


@app.get("/sync")
async def list_buckets_sync(begin=0, end=-1):
    results = []
    async with aioboto3.Session().resource("s3", config=S3_CONFIG) as s3:
        buckets = list([b async for b in s3.buckets.all()])
        for b in buckets[begin:end]:
            info = await get_bucket_info(b)
            results.append(info)
    return results


@app.get("/async")
async def list_buckets_async(begin=0, end=-1):
    async with aioboto3.Session().resource("s3", config=S3_CONFIG) as s3:
        tasks = [
            asyncio.ensure_future(get_bucket_info(b)) async for b in s3.buckets.all()
        ][begin:end]
        return await asyncio.gather(*tasks)


class timeit(ContextDecorator):
    def __init__(self, msg):
        self.msg = msg

    def __enter__(self):
        self.t = perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        elapsed = perf_counter() - self.t
        print(f'{self.msg} took {elapsed:.6f} seconds')


async def main():
    import argparse

    parser = argparse.ArgumentParser(description='AIO S3 list buckets')
    parser.add_argument('-p', '--page', type=int, default=1, help='Result page, starting on 1')
    parser.add_argument('-s', '--size', type=int, default=50, help='Page size')
    parser.add_argument('--sync', default=False, action='store_true', help='Run sync version too')
    args = parser.parse_args()

    begin = (args.page - 1) * args.size
    end = begin + args.size

    if args.sync:
        with timeit("SYNC ") as t:
            sync_buckets = await list_buckets_sync(begin, end)

    with timeit("ASYNC") as t:
        async_buckets = await list_buckets_async(begin, end)
    if args.sync:
        assert sync_buckets == async_buckets, "Oops, mismatch info"

    for b in async_buckets:
        print(b)

    size = sum(b["bytes"] for b in async_buckets)
    print (f"Total account size: {size} bytes")


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
