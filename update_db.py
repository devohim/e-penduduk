import sqlite3

conn = sqlite3.connect("penduduk.db")
cursor = conn.cursor()

try:
    cursor.execute("""
        ALTER TABLE penduduk
        ADD COLUMN jenis_kelamin TEXT
    """)
    conn.commit()
    print("Kolom jenis_kelamin berhasil ditambahkan.")
except Exception as e:
    print(e)

conn.close()