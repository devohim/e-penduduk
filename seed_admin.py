import boto3


db=boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)


users=db.Table("users")


users.put_item(
    Item={
        "username":"admin",
        "nama":"Administrator Desa",
        "password":"admin123",
        "role":"Administrator",
        "status":"Aktif"
    }
)


print("Admin berhasil dibuat")