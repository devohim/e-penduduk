# PANDUAN INSTALASI DAN PENGGUNAAN APLIKASI E-PENDUDUK

## 1. Deskripsi Aplikasi

E-Penduduk adalah aplikasi berbasis web untuk mengelola data kependudukan (skala desa/kelurahan) yang dibangun menggunakan **Python Flask**. Aplikasi ini menyimpan data ke **DynamoDB** dan berkas (foto KTP, dokumen) ke **Amazon S3**, yang keduanya dijalankan secara lokal melalui **LocalStack** (simulator layanan AWS) dan **Docker**.

**Fitur utama:**
- Login & registrasi pengguna dengan status persetujuan (Pending/Aktif/Ditolak/Nonaktif)
- Manajemen hak akses (Administrator & Operator Desa)
- Data induk penduduk: tambah, edit, hapus, cari (berdasarkan NIK/nama)
- Statistik ringkas (jumlah penduduk, jumlah laki-laki/perempuan, jumlah dokumen)
- Upload dan kelola dokumen pendukung (KTP, foto, dsb.) yang terhubung ke data penduduk
- Manajemen jenis dokumen (tambah/ubah/hapus kategori dokumen)
- Manajemen pengguna (approve, tolak, aktifkan, nonaktifkan akun)

## 2. Kebutuhan Sistem (Prasyarat)

Sebelum instalasi, pastikan perangkat sudah memiliki:

| Komponen | Keterangan |
|---|---|
| Python | Versi 3.10 ke atas |
| Docker & Docker Compose | Untuk menjalankan LocalStack |
| pip | Untuk instalasi pustaka Python |
| Browser | Untuk mengakses aplikasi web |

## 3. Struktur Folder Penting

```
e-penduduk/
├── app.py              # File utama aplikasi Flask (seluruh routing)
├── config.py            # Konfigurasi koneksi S3 (LocalStack)
├── create_table.py      # Skrip membuat tabel DynamoDB
├── seed_admin.py        # Skrip membuat akun admin awal
├── hapus_tabel.py       # Skrip menghapus tabel tertentu
├── docker-compose.yml   # Konfigurasi container LocalStack
├── requirements.txt     # Daftar pustaka Python yang dibutuhkan
└── templates/           # Seluruh tampilan (HTML) aplikasi
```

## 4. Langkah-Langkah Instalasi

### Langkah 1 — Jalankan LocalStack (Docker)
Buka terminal di folder proyek, lalu jalankan:
```
docker compose up -d
```
Perintah ini akan menjalankan container LocalStack yang mensimulasikan layanan **S3** di `http://localhost:4566`.

### Langkah 2 — Buat Virtual Environment (opsional tapi disarankan)
```
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # Mac/Linux
```

### Langkah 3 — Instal Pustaka Python
```
pip install -r requirements.txt
```
Pustaka utama yang digunakan: **Flask**, **boto3**, **botocore**, **Werkzeug**, **awscli-local**.

> Catatan: file `requirements.txt` pada proyek ini rusak formatnya (berspasi antar-huruf). Sebaiknya dibuat ulang secara manual dengan daftar pustaka: `Flask`, `boto3`, `botocore`, `Werkzeug`, `python-dateutil`, `awscli-local`.

### Langkah 4 — Buat Tabel Basis Data
Jalankan skrip berikut untuk membuat tabel di DynamoDB (penduduk, users, jenis_dokumen, dokumen, logs):
```
python create_table.py
```

### Langkah 5 — Buat Akun Admin Awal
```
python seed_admin.py
```
Akun admin default:
- **Username:** admin
- **Password:** admin123
- **Role:** Administrator

> Catatan: akun admin default juga otomatis dibuat oleh `app.py` saat aplikasi pertama kali dijalankan jika belum ada.

### Langkah 6 — Jalankan Aplikasi
```
python app.py
```
Aplikasi akan berjalan di:
```
http://127.0.0.1:5000
```

## 5. Cara Menggunakan Aplikasi

### 5.1 Login
- Buka `http://127.0.0.1:5000/login`
- Masuk dengan akun admin (admin / admin123), atau daftar akun baru melalui menu **Register** (akun baru berstatus "Pending" dan harus disetujui admin terlebih dahulu).

### 5.2 Kelola Data Penduduk
- Menu **Tambah** untuk menambahkan data penduduk baru (NIK, nama, alamat, jenis kelamin, foto KTP).
- Data dapat dicari melalui kolom pencarian di halaman utama (berdasarkan NIK atau nama).
- Setiap data dapat **diedit** atau **dihapus**; saat dihapus, berkas KTP terkait juga otomatis dihapus dari penyimpanan.

### 5.3 Kelola Dokumen
- Menu **Dokumen** menampilkan seluruh dokumen yang sudah diunggah beserta nama pemilik dan jenis dokumennya.
- Menu **Upload Dokumen** untuk mengunggah dokumen baru: pilih penduduk, pilih jenis dokumen, lalu unggah berkas.
- Menu **Jenis Dokumen** untuk menambah, mengubah, atau menghapus kategori dokumen (misalnya: KTP, KK, Akta Lahir, dsb.).

### 5.4 Kelola Pengguna (khusus Administrator)
- Menu **Users** menampilkan daftar seluruh pengguna terdaftar.
- Admin dapat **menyetujui**, **menolak**, **mengaktifkan**, atau **menonaktifkan** akun pengguna lain.

### 5.5 Logout
- Klik menu **Logout** untuk keluar dari sesi.

## 6. Struktur Tabel DynamoDB

| Nama Tabel | Kunci Utama | Fungsi |
|---|---|---|
| penduduk | nik (String) | Menyimpan data induk penduduk |
| users | username (String) | Menyimpan akun pengguna |
| jenis_dokumen | id (Number) | Menyimpan kategori/jenis dokumen |
| dokumen | id (Number) | Menyimpan metadata dokumen yang diunggah |
| logs | id (Number) | Menyimpan log aktivitas (disediakan, belum digunakan aktif) |

## 7. Catatan Keamanan & Perbaikan yang Disarankan

- Password pengguna saat ini disimpan dalam bentuk teks biasa (belum di-hash) — sebaiknya gunakan hashing seperti `werkzeug.security.generate_password_hash` sebelum digunakan secara nyata.
- `app.secret_key` masih berupa teks tetap ("ependuduk123") — sebaiknya diganti dengan nilai acak/rahasia melalui variabel lingkungan (environment variable).
- Kredensial AWS (`test`/`test`) hanya berlaku untuk LocalStack (simulasi lokal), bukan untuk lingkungan produksi nyata di AWS.

## 8. Pemecahan Masalah (Troubleshooting)

| Masalah | Kemungkinan Penyebab & Solusi |
|---|---|
| Aplikasi gagal konek ke DynamoDB/S3 | Pastikan container LocalStack sudah berjalan (`docker ps`) dan port 4566 tidak diblokir |
| Tabel belum ada | Jalankan ulang `python create_table.py` |
| Tidak bisa login dengan admin | Jalankan ulang `python seed_admin.py` untuk membuat ulang akun admin |
| Ingin mengulang dari awal | Jalankan `python hapus_tabel.py` untuk menghapus tabel jenis_dokumen, dokumen, dan logs, lalu buat ulang dengan `create_table.py` |
| Gagal instal pustaka | Perbaiki dahulu isi `requirements.txt`, karena formatnya saat ini rusak (berspasi antar-karakter) |
