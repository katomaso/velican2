# Developer notes

General structure of AWS client response

```json
{
  "ResponseMetadata": {
    "RequestId": "3D1EM6VFSPXK68V7",
    "HostId": "p4U+vHZLAIi5BSakkFbnItR6YoBAUncwsfCoV43uzUcqVX67shVoMn1Ld4AFd0ATj9WQXljVP8k=",
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "x-amz-id-2": "p4U+vHZLAIi5BSakkFbnItR6YoBAUncwsfCoV43uzUcqVX67shVoMn1Ld4AFd0ATj9WQXljVP8k=",
      "x-amz-request-id": "3D1EM6VFSPXK68V7",
      "date": "Mon, 24 Apr 2023 15:14:52 GMT",
      "x-amz-bucket-region": "eu-central-1",
      "x-amz-access-point-alias": "false",
      "content-type": "application/xml",
      "server": "AmazonS3"
    },
    "RetryAttempts": 1
  }
}
```

Failure throws `botocore.exceptions.ClientError`

Response of Client.create_bucket is not indempotent. When a bucket already exists
it throws an exception `botocore.errorfactory.BucketAlreadyOwnedByYou`. Otherwise
it gives a successfull response

```json
{
  "ResponseMetadata": {
    "RequestId": "83GY1WC437C6ZGJ8",
    "HostId": "qrj9HeO+uxbFXnkXNC8XNptlxJZOJciJp1+OicmeM7sVkK7gwbi9c1D1OOG7Wh8JaM+KpyfsUCQ=",
    "HTTPStatusCode": 200,
    "HTTPHeaders": {
      "x-amz-id-2": "qrj9HeO+uxbFXnkXNC8XNptlxJZOJciJp1+OicmeM7sVkK7gwbi9c1D1OOG7Wh8JaM+KpyfsUCQ=",
      "x-amz-request-id": "83GY1WC437C6ZGJ8",
      "date": "Mon, 24 Apr 2023 15:20:50 GMT",
      "location": "/drahymaslo.cz",
      "server": "AmazonS3",
      "content-length": "0"
    },
    "RetryAttempts": 0
  },
  "Location": "/drahymaslo.cz"
}
```
