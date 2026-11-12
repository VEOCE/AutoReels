
# AutuFB

AutuFB adalah script otomatis untuk membuat video Facebook Reels dari foto dan membantu menjadwalkan publikasi ke Facebook Page.

## Fitur

- Mengubah foto menjadi video vertikal 9:16.
- Resolusi video 1080 x 1920.
- Durasi video dapat diatur.
- Efek zoom otomatis.
- Membuat caption menggunakan Gemini AI.
- Upload Reels melalui Meta Graph API.
- Jadwal otomatis 6 kali sehari.
- Mencatat foto yang sudah diproses.

## Jadwal Default

- 07:00
- 10:00
- 13:00
- 16:00
- 19:00
- 21:00

Zona waktu: Asia/Jakarta.

## Instalasi Termux

Perbarui Termux:

```bash
pkg update && pkg upgrade -y
```

Pasang kebutuhan:

```bash
pkg install python ffmpeg git -y
```

Clone repository:

```bash
git clone https://github.com/USERNAME/AutuFB.git
```

Masuk folder:

```bash
cd AutuFB
```

Pasang library:

```bash
pip install -r requirements.txt
```

Buat konfigurasi:

```bash
cp .env.example .env
```

Edit konfigurasi:

```bash
nano .env
```

Masukkan konfigurasi Facebook Page dan Gemini API secara pribadi di file `.env`.

## Folder Foto

Masukkan foto JPG, JPEG, PNG, atau WEBP ke folder:

```text
foto/
```

## Pengujian

Jalankan mode pengujian:

```bash
python main.py --once --dry-run
```

Mode ini tidak mengunggah video ke Facebook.

## Menjalankan Jadwal

```bash
python main.py
```

## Catatan Keamanan

- Jangan membagikan PAGE_ACCESS_TOKEN.
- Jangan membagikan GEMINI_API_KEY.
- Jangan mengunggah file `.env` ke GitHub.
- Gunakan Facebook Page dan izin API Meta yang sesuai.
- Uji terlebih dahulu sebelum mengaktifkan publikasi sungguhan.

## Penting

Publikasi otomatis memerlukan konfigurasi Meta Graph API yang valid. Keberhasilan upload harus diuji dengan akun dan Page yang digunakan.
