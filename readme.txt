Berikut tata cara menjalankan dan menggunakan program

AKSES MENJALANKAN PROGRAM DENGAN LOCAL HOST

STEP 1
Mengetahui lokasi folder
- Setelah Anda mengunduh folder Project PVSIM
- Buka File Manager, lalu masuk ke folder Downloads
- Arahkan ke folder Project PVSIM, kemudian klik kanan pada folder tersebut
- Akan muncul pop-up, pilih menu Properties
- Perhatikan bagian Location, lalu salin atau catat lokasi folder tersebut


STEP 2
Cara menjalankan program
- Buka aplikasi Spyder, kemudian klik Open File di pojok kiri atas
- Masuk ke folder Project PVSIM yang berada di Downloads
- Buka file bernama app.py
- Setelah file terbuka, klik Run File (ikon segitiga di kiri atas) atau tekan F5 pada keyboard


STEP 3
Mengakses website Local Host
- Biarkan program tetap berjalan
- Tekan tombol Windows atau klik Search pada taskbar, lalu ketik Anaconda Prompt dan buka aplikasinya
- Setelah terbuka, ketik perintah berikut lalu tekan Enter:
  conda activate base
- Masuk ke lokasi folder Project PVSIM dengan perintah:
  cd /d lokasi_folder
  Contoh:
  cd /d C:\Users\Nama_PC_Anda\Downloads\Project PVSIM
- Setelah itu, jalankan perintah:
  streamlit run app.py
- Browser akan terbuka otomatis dan mengarahkan Anda ke website Local Host


AKSES MENJALANKAN PROGRAM DENGAN WEBSITE (MEMBUTUHKAN INTERNET TANPA HARUS BUKA SPYDER)
- Pastikan laptop Anda terhubung dengan koneksi internet
- Buka browser, lalu akses:
  https://projectpvsim.streamlit.app/


CARA MENGGUNAKAN PROGRAM
- Unduh data dari NASA POWER Data Access Viewer:
  https://power.larc.nasa.gov/data-access-viewer/
- Pada bagian User Community, pilih Renewable Energy
- Pada bagian Temporal Level, pilih Hourly
- Tentukan rentang tanggal (disarankan 1 tahun penuh)
- Pilih format file CSV
- Parameter wajib:
  - All Sky Surface Shortwave Downward Irradiance
  - Temperature at 2 Meters
- Klik Submit untuk mengunduh data
- Unggah file CSV melalui sidebar kiri aplikasi
- Atur kapasitas dan spesifikasi PV System pada sidebar
- Atau gunakan data sampel yang tersedia di website
