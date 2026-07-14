import boto3
from botocore.exceptions import ClientError

# Koneksi ke LocalStack
client = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Daftar tabel yang ingin dihapus
tabel_hapus = ["jenis_dokumen", "dokumen", "logs"]

for nama in tabel_hapus:
    try:
        client.delete_table(TableName=nama)
        print(f"✅ Tabel '{nama}' berhasil dihapus")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"ℹ️ Tabel '{nama}' tidak ada, dilewati")
        else:
            print(f"❌ Gagal hapus '{nama}': {e.response['Error']['Message']}")