import boto3
import os

resource = boto3.resource('s3',
    aws_access_key_id=os.getenv("AWS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET"),
)

client = boto3.client('s3',
    aws_access_key_id=os.getenv("AWS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET"),
)

print("-- prohlizecstaci.cz --")
print(client.head_bucket(Bucket="prohlizecstaci.cz"))

print("-- drahymaslo.cz --")
bucket = resource.Bucket("drahymaslo.cz")
print("Bucket: " + str(bucket))
print(client.create_bucket(Bucket="drahymaslo.cz", ACL='private', CreateBucketConfiguration={'LocationConstraint': 'eu-central-1'}))
