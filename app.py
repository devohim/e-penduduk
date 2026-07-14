import boto3
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    flash,
    jsonify
)
from config import s3, BUCKET_NAME
from flask import send_file
from io import BytesIO


app = Flask(__name__)
app.secret_key = "ependuduk123"

# Koneksi ke DynamoDB
dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

# Tabel
table = dynamodb.Table("penduduk")
user_table = dynamodb.Table("users")
response = user_table.get_item(Key={"username": "admin"})

if "Item" not in response:
    user_table.put_item(
        Item={
            "username": "admin",
            "password": "admin123",
            "nama": "Administrator",
            "role": "Administrator",
            "status": "Aktif"
        }
    )

dokumen_table = dynamodb.Table("dokumen")
jenis_table = dynamodb.Table("jenis_dokumen")
client = boto3.client(
    "dynamodb",
    endpoint_url="http://localhost:4566",
    region_name="us-east-1",
    aws_access_key_id="test",
    aws_secret_access_key="test"
)

print("=================================")
print(client.list_tables())
print("=================================")

# Buat bucket S3 jika belum ada
try:
    buckets = s3.list_buckets()["Buckets"]
    names = [b["Name"] for b in buckets]
    if BUCKET_NAME not in names:
        s3.create_bucket(Bucket=BUCKET_NAME)
except Exception as e:
    print(e)


from boto3.dynamodb.conditions import Attr

# ------------------------------
# RUTE UTAMA
# ------------------------------
@app.route("/")
def home():
    if "login" not in session:
        return redirect("/login")

    keyword = request.args.get("keyword", "")
    if keyword:
        response = table.scan(
            FilterExpression=Attr("nik").contains(keyword) | Attr("nama").contains(keyword)
        )
    else:
        response = table.scan()

    penduduk = sorted(response["Items"], key=lambda x: x["nik"], reverse=True)
    laki = sum(1 for p in penduduk if p.get("jenis_kelamin") == "Laki-laki")
    perempuan = sum(1 for p in penduduk if p.get("jenis_kelamin") == "Perempuan")

    data_s3 = s3.list_objects_v2(Bucket=BUCKET_NAME)
    files = data_s3.get("Contents", [])

    return render_template(
        "index.html",
        penduduk=penduduk,
        files=files,
        bucket=BUCKET_NAME,
        keyword=keyword,
        jumlah_penduduk=len(penduduk),
        jumlah_dokumen=len(files),
        laki=laki,
        perempuan=perempuan
    )

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        role = request.form["role"]

        if user_table.get_item(Key={"username": username}).get("Item"):
            flash("Username sudah digunakan")
            return redirect("/register")

        user_table.put_item(
            Item={
                "username": username,
                "password": password,
                "nama": nama,
                "role": role,
                "status": "Pending"
            }
        )
        flash("Registrasi berhasil. Silakan tunggu persetujuan.")
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = user_table.get_item(Key={"username": username}).get("Item")

        if user and user["password"] == password:
            status = user.get("status", "Aktif")
            if status == "Pending":
                flash("Akun menunggu persetujuan.")
            elif status == "Ditolak":
                flash("Akun ditolak.")
            elif status == "Nonaktif":
                flash("Akun dinonaktifkan.")
            else:
                session["login"] = True
                session["username"] = user["username"]
                session["nama"] = user["nama"]
                session["role"] = user["role"]
                return redirect("/")
        else:
            flash("Username atau Password salah")

    return render_template("login.html")

@app.route("/users")
def users():
    if "login" not in session:
        return redirect("/login")
    if session["role"] != "Administrator":
        flash("Akses ditolak.")
        return redirect("/")

    users = sorted(user_table.scan().get("Items", []), key=lambda x: x["nama"])
    return render_template("users/index.html", users=users)

@app.route("/users/approve/<username>")
def approve_user(username):
    user_table.update_item(
        Key={"username": username},
        UpdateExpression="SET #r=:r, #s=:s",
        ExpressionAttributeNames={"#r":"role", "#s":"status"},
        ExpressionAttributeValues={":r":"Operator Desa", ":s":"Aktif"}
    )
    flash("User disetujui")
    return redirect("/users")

@app.route("/users/reject/<username>")
def reject_user(username):
    user_table.update_item(
        Key={"username": username},
        UpdateExpression="SET #s=:s",
        ExpressionAttributeNames={"#s":"status"},
        ExpressionAttributeValues={":s":"Ditolak"}
    )
    flash("User ditolak")
    return redirect("/users")

@app.route("/users/nonaktif/<username>")
def nonaktif(username):
    user_table.update_item(
        Key={"username": username},
        UpdateExpression="SET #s=:s",
        ExpressionAttributeNames={"#s":"status"},
        ExpressionAttributeValues={":s":"Nonaktif"}
    )
    flash("User dinonaktifkan")
    return redirect("/users")

@app.route("/users/aktif/<username>")
def aktif(username):
    user_table.update_item(
        Key={"username": username},
        UpdateExpression="SET #s=:s",
        ExpressionAttributeNames={"#s":"status"},
        ExpressionAttributeValues={":s":"Aktif"}
    )
    flash("User diaktifkan")
    return redirect("/users")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/tambah")
def tambah():
    if "login" not in session:
        return redirect("/login")
    return render_template("tambah.html")

@app.route("/simpan", methods=["POST"])
def simpan():
    nik = request.form["nik"]
    nama = request.form["nama"]
    alamat = request.form["alamat"]
    jenis_kelamin = request.form["jenis_kelamin"]
    file = request.files["ktp"]
    filename = secure_filename(file.filename)

    s3.upload_fileobj(file, BUCKET_NAME, filename)
    table.put_item(
        Item={
            "nik": nik,
            "nama": nama,
            "alamat": alamat,
            "jenis_kelamin": jenis_kelamin,
            "ktp": filename
        }
    )
    return redirect("/")

@app.route("/edit/<nik>")
def edit(nik):
    penduduk = table.get_item(Key={"nik": nik}).get("Item")
    return render_template("edit.html", p=penduduk)

@app.route("/update/<nik>", methods=["POST"])
def update(nik):
    table.update_item(
        Key={"nik": nik},
        UpdateExpression="SET nama=:n, alamat=:a, jenis_kelamin=:j",
        ExpressionAttributeValues={
            ":n": request.form["nama"],
            ":a": request.form["alamat"],
            ":j": request.form["jenis_kelamin"]
        }
    )
    return redirect("/")

@app.route("/hapus/<nik>")
def hapus(nik):
    data = table.get_item(Key={"nik": nik}).get("Item")
    if data and data.get("ktp"):
        s3.delete_object(Bucket=BUCKET_NAME, Key=data["ktp"])
    table.delete_item(Key={"nik": nik})
    return redirect("/")

@app.route("/download/<filename>")
def download(filename):
    file_obj = BytesIO()
    s3.download_fileobj(BUCKET_NAME, filename, file_obj)
    file_obj.seek(0)
    return send_file(file_obj, download_name=filename, as_attachment=False)

@app.route("/dokumen")
def dokumen():
    if "login" not in session:
        return redirect("/login")
    
    # Ambil semua data dokumen
    response = dokumen_table.scan()
    daftar_dokumen = response.get("Items", [])
    
    # Ambil data pendukung untuk mencocokkan nama
    data_penduduk = table.scan().get("Items", [])
    data_jenis = jenis_table.scan().get("Items", [])
    
    # Susun data lengkap untuk halaman
    dokumen_lengkap = []
    for d in daftar_dokumen:
        # Cari nama penduduk berdasarkan NIK
        nama_penduduk = "-"
        for p in data_penduduk:
            if p.get("nik") == d.get("nik_penduduk"):
                nama_penduduk = p.get("nama", "-")
                break
        
        # Cari nama jenis dokumen berdasarkan id
        nama_jenis = "-"
        for j in data_jenis:
            if j.get("id") == d.get("jenis_id"):
                nama_jenis = j.get("nama", "-")
                break
        
        # Masukkan ke daftar lengkap
        dokumen_lengkap.append({
            "id": d.get("id"),
            "nama_penduduk": nama_penduduk,
            "jenis_dokumen": nama_jenis,
            "filename": d.get("filename", "-"),
            "tanggal_upload": d.get("tanggal_upload", "-")
        })
    
    # Hitung statistik
    total_pdf = sum(1 for d in daftar_dokumen if str(d.get("filename", "")).lower().endswith(".pdf"))
    total_image = sum(1 for d in daftar_dokumen if str(d.get("filename", "")).lower().endswith((".jpg", ".jpeg", ".png")))
    
    return render_template(
        "dokumen/index.html",
        dokumen=dokumen_lengkap,  # ✅ Kirim data lengkap, bukan data mentah
        jumlah_dokumen=len(daftar_dokumen),
        total_pdf=total_pdf,
        total_image=total_image
    )

@app.route("/dokumen/hapus/<int:id>", methods=["GET"])
def hapus_dokumen(id):
    if "login" not in session:
        return redirect("/login")
    try:
        # Ambil nama file untuk dihapus dari S3
        data = dokumen_table.get_item(Key={"id": id}).get("Item")
        if data and data.get("filename"):
            s3.delete_object(Bucket=BUCKET_NAME, Key=data["filename"])
        
        # Hapus data dari tabel
        dokumen_table.delete_item(Key={"id": id})
        flash("Dokumen berhasil dihapus")
    except Exception as e:
        flash(f"Gagal hapus: {str(e)}")
    return redirect("/dokumen")

@app.route("/dokumen/upload", methods=["GET", "POST"])
def upload_dokumen():
    if "login" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        try:
            # Ambil data dari form upload
            nik_penduduk = request.form.get("nik_penduduk")
            jenis_id = request.form.get("jenis_id")
            file = request.files["file_dokumen"]

            # Cek kolom tidak boleh kosong
            if not nik_penduduk or not jenis_id or not file or file.filename == "":
                flash("Semua kolom dan file harus diisi!")
                return redirect("/dokumen/upload")

            # Ambil nama file aman dan upload ke Stockport/S3
            filename = secure_filename(file.filename)
            s3.upload_fileobj(file, BUCKET_NAME, filename)

            # Simpan data dokumen ke tabel DynamoDB
            id_dokumen = int(uuid.uuid4().int % 1000000)
            dokumen_table.put_item(Item={
                "id": id_dokumen,
                "nik_penduduk": nik_penduduk,
                "jenis_id": int(jenis_id),
                "filename": filename,
                "tanggal_upload": datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            })

            flash("✅ Dokumen berhasil diunggah!")
            return redirect("/dokumen")

        except Exception as e:
            flash(f"❌ Gagal upload: {str(e)}")
            return redirect("/dokumen/upload")

    # Tampilkan halaman form jika hanya buka halaman
    penduduk = table.scan().get("Items", [])
    jenis = jenis_table.scan().get("Items", [])
    return render_template("dokumen/upload.html", penduduk=penduduk, jenis=jenis)

# ------------------------------
# RUTE JENIS DOKUMEN (LENGKAP & TIDAK GANDA)
# ------------------------------
@app.route("/dokumen/jenis")
def jenis_dokumen():
    if "login" not in session:
        return redirect("/login")
    data = jenis_table.scan().get("Items", [])
    return render_template("dokumen/jenis.html", jenis=data)

@app.route("/dokumen/jenis/data")
def data_jenis_json():
    if "login" not in session:
        return jsonify({"sukses": False, "pesan": "Login dulu"}), 401
    try:
        items = jenis_table.scan().get("Items", [])
        hasil = []
        for item in items:
            hasil.append({
                "id": item.get("id"),
                "nama": item.get("nama", "")
            })
        return jsonify(hasil)
    except Exception as e:
        return jsonify({"sukses": False, "pesan": str(e)}), 500

@app.route("/dokumen/jenis/simpan", methods=["POST"])
def simpan_jenis():
    if "login" not in session:
        return jsonify({"sukses": False, "pesan": "Akses ditolak"}), 403
    try:
        nama = request.form.get("nama", "").strip()
        if not nama:
            return jsonify({"sukses": False, "pesan": "Nama tidak boleh kosong"})
        if jenis_table.scan(FilterExpression=Attr("nama").eq(nama)).get("Items"):
            return jsonify({"sukses": False, "pesan": "Nama sudah ada"})
        
        import uuid
        id_baru = int(uuid.uuid4().int % 1000000)
        jenis_table.put_item(Item={"id": id_baru, "nama": nama})
        return jsonify({"sukses": True})
    except Exception as e:
        return jsonify({"sukses": False, "pesan": str(e)}), 500

@app.route("/dokumen/jenis/ubah/<int:id>", methods=["POST"])
def ubah_jenis(id):
    if "login" not in session:
        return jsonify({"sukses": False, "pesan": "Akses ditolak"}), 403
    try:
        nama = request.form.get("nama", "").strip()
        if not nama:
            return jsonify({"sukses": False, "pesan": "Nama tidak boleh kosong"})
        jenis_table.update_item(
            Key={"id": id},
            UpdateExpression="SET nama = :n",
            ExpressionAttributeValues={":n": nama}
        )
        return jsonify({"sukses": True})
    except Exception as e:
        return jsonify({"sukses": False, "pesan": str(e)}), 500

@app.route("/dokumen/jenis/hapus/<int:id>", methods=["POST"])
def hapus_jenis(id):
    if "login" not in session:
        return jsonify({"sukses": False, "pesan": "Akses ditolak"}), 403
    try:
        jenis_table.delete_item(Key={"id": id})
        return jsonify({"sukses": True})
    except Exception as e:
        return jsonify({"sukses": False, "pesan": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)