import boto3
from botocore.exceptions import ClientError

# ======================================
# Koneksi ke DynamoDB LocalStack
# ======================================
client = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)


# ======================================
# Fungsi membuat tabel (sudah diperbaiki)
# ======================================
def create_table(table_name, primary_key, key_type="S"):
    """
    key_type: 
      - 'S' = String (untuk NIK, username)
      - 'N' = Number (untuk ID angka)
    """
    try:
        client.create_table(
            TableName=table_name,
            AttributeDefinitions=[
                {
                    "AttributeName": primary_key,
                    "AttributeType": key_type
                }
            ],
            KeySchema=[
                {
                    "AttributeName": primary_key,
                    "KeyType": "HASH"  # Kunci utama
                }
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        print(f"✅ Tabel '{table_name}' berhasil dibuat")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"ℹ️ Tabel '{table_name}' sudah ada, dilewati")
        else:
            print(f"❌ Gagal buat tabel '{table_name}': {e.response['Error']['Message']}")


# ======================================
# Membuat seluruh tabel (sesuai kebutuhan sistem E-Penduduk)
# ======================================

# 1. Tabel Penduduk: Kunci utama NIK (tipe String)
create_table("penduduk", "nik", "S")

# 2. Tabel User: Kunci utama username (tipe String)
create_table("users", "username", "S")

# 3. Tabel Jenis Dokumen: Kunci utama id (tipe Angka)
create_table("jenis_dokumen", "id", "N")

# 4. Tabel Dokumen: Kunci utama id (tipe Angka)
create_table("dokumen", "id", "N")

# 5. Tabel Log Aktivitas: Kunci utama id (tipe Angka)
create_table("logs", "id", "N")


# ======================================
# Menampilkan seluruh tabel yang tersedia
# ======================================
print("\n📋 Daftar tabel di DynamoDB LocalStack:")
response = client.list_tables()

if "TableNames" in response and response["TableNames"]:
    for nama_tabel in response["TableNames"]:
        print(f" - {nama_tabel}")
else:
    print(" - Belum ada tabel")