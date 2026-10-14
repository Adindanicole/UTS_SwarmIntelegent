# Optimasi rute pengiriman satu kurir dengan Ant System

Program mencari **total jarak minimum**, berangkat dari depot, mengunjungi semua
pelanggan tepat satu kali, lalu kembali ke depot (TSP simetris). Semua pesanan
dianggap bisa dibawa sekaligus. Jarak Euclidean dalam km adalah simulasi; belum
memodelkan jalan nyata, kemacetan, kapasitas, banyak kurir, atau batas waktu.

## Menjalankan

### Web lokal (semua input melalui browser)

```powershell
py -3.14 -m pip install -r requirements.txt
py -3.14 -m streamlit run app.py
```

Buka alamat yang tampil, biasanya **http://127.0.0.1:8501**. Pilih **Gunakan Data
Contoh** atau **Masukkan Lokasi Sendiri**, isi nama/X/Y toko dan tabel pelanggan,
lalu klik **Cari Rute Pengiriman**. Tambah pelanggan lewat baris kosong di bawah
tabel; pilih baris dan ikon hapus untuk menghapusnya. Nama dan koordinat wajib
diisi, minimal satu pelanggan. Koordinat simulasi dalam km, bukan alamat/GPS.
Lokasi berimpit diperbolehkan. Jangan menafsirkan simulasi sebagai waktu pengiriman.

**Pengaturan Pencarian** dapat dibuka untuk mengubah semut, putaran, alpha, beta,
penguapan, dan seed. Default sama dengan program terminal; Q tetap 1. Hasil memuat
jarak ACO, jumlah pelanggan, waktu **komputer mencari rute ACO**, urutan kunjungan,
tabel pembanding, grafik metode pilihan, dan perkembangan ACO. Grafik X/Y memakai
skala yang sama. NN ditampilkan sebagai **Pelanggan Terdekat**, NN + 2-opt sebagai
**Pelanggan Terdekat + Perbaikan Rute**. Hasil lebih buruk tetap ditampilkan;
persentase terhadap pembanding 0 km ditandai tidak dihitung, tanpa pembagian nol.

Unduh **Ringkasan CSV** untuk perbandingan dan parameter; **Urutan Rute CSV**
mengikuti metode yang dipilih pada grafik. Unduhan menggunakan UTF-8 BOM agar
nama terbaca di Excel. Hasil dan input aktif berada di session state browser,
bukan ditulis ke output. Mengubah grafik atau mengunduh tidak mengulang algoritma.
Perubahan input/pengaturan memberi peringatan bahwa hasil perlu diperbarui.
**Reset Input dan Hasil** mengembalikan sumber contoh, default parameter, dan
menghapus hasil sesi. Memuat ulang halaman/koneksi baru dapat menghapus hasil sesi;
unduh CSV jika ingin menyimpannya. Hentikan server dengan Ctrl+C di terminal.

`app.py` hanya memanggil fungsi `main.py`; tidak menduplikasi algoritma, menjalankan
brute force, atau mengulang eksperimen utama. `.streamlit/config.toml` mengatur
tema terang dengan aksen hijau dan server yang terikat ke komputer lokal.
Streamlit 1.57.0 dan Matplotlib 3.10.9 diverifikasi pada Python 3.14.4.
Komponen tabel memakai [data editor resmi Streamlit](https://docs.streamlit.io/develop/concepts/design/dataframes).

Verifikasi integrasi web (14 Oktober 2026): **19 pengujian lulus**, terdiri dari
13 pengujian sebelumnya dan 6 pengujian web. Data contoh tetap 23.399846 km.
Pengujian memeriksa validasi, lokasi berimpit/0 km, parameter, reset, penanda hasil
lama, pemilihan grafik tanpa menghitung ulang, serta byte CSV pada tombol unduh.
Server lokal dan endpoint kesehatan merespons HTTP 200. Seluruh 77 file yang
sudah ada di output tetap memiliki hash identik; tidak ada hasil baru ditulis
oleh halaman web. Eksperimen utama tidak diulang.

Browser automation tidak menemukan browser/tab tersedia pada sesi verifikasi;
belum ada pemeriksaan tampilan langsung atau klik unduhan dalam browser nyata.
Alur widget diuji memakai **Streamlit AppTest**; edit/tambah/hapus tabel dikirim
melalui payload state editor karena AppTest belum menyediakan pengendali sel.
Pesan `missing ScriptRunContext` pada thread pengujian berasal dari penggunaan
AppTest di luar server, bukan error halaman. TemporaryDirectory milik AppTest
ditutup eksplisit saat pengujian selesai; tidak ada filter warning tambahan.

### Mode terminal tetap tersedia

Di VS Code, buka folder proyek dan pilih interpreter Python 3.14.4 melalui
**Python: Select Interpreter**. Matplotlib 3.10.9 sudah tersedia pada interpreter
yang digunakan; tidak ada perubahan versi Python atau pengaturan global.

```powershell
cd C:\Tugas_nicole_smt7\UTS_SwarmIntelegent_Nicole
py -3.14 -m pip install -r requirements.txt
py -3.14 main.py
```

Menu: **1 Demo**, **2 Input koordinat sendiri**, **3 Eksperimen**, **4 Keluar**.
Menu kembali muncul setelah pekerjaan selesai. Ctrl+C menghentikan program.
Grafik otomatis disimpan; tambahkan `--show` jika ingin membuka grafik demo/manual.

Alternatif argumen terminal (melewati pilihan menu):

```powershell
py -3.14 main.py demo
py -3.14 main.py manual
py -3.14 main.py cepat
py -3.14 main.py eksperimen
py -3.14 main.py demo --output output\contoh_demo --show
py -3.14 -B -W default -m unittest -v
```

Tanpa `--output`, hasil baru masuk subfolder bernomor, misalnya `output/manual_001/`.
Hasil utama lama di akar `output/` tetap disimpan. `--output` menentukan folder
tujuan langsung; gunakan folder baru. Eksperimen menolak folder yang sudah berisi
`hasil_mentah.csv`. Menu 3 menjalankan ulang 720 run dengan rancangan tetap;
untuk mempelajari hasil yang sudah ada, cukup buka LAPORAN.md.

## Input yang tersedia

| Jenis | Cara memasukkan | Yang dapat diubah |
|---|---|---|
| Browser lokal | `streamlit run app.py` | Sumber data, tabel lokasi, parameter, grafik metode, unduh CSV dan reset |
| Interaktif terminal | Menu 2 atau `main.py manual` | Jumlah pelanggan, nama dan X/Y depot/pelanggan; semut, iterasi, alpha, beta, rho, seed ACO |
| Argumen terminal | Teks sesudah `main.py` | Mode, `--output`, `--show`; bukan daftar koordinat atau parameter ACO |
| Nilai di kode | Konstanta `LOKASI_DEMO`, `DEFAULT`, `SEED_DATA`, `SEED_ACO`, fungsi `konfigurasi()` | Data demo, Q=1, rancangan eksperimen dan seed data |

Sebelum penyederhanaan, hanya argumen terminal dan nilai di kode yang tersedia;
belum ada input interaktif. Demo selalu memakai parameter awal dan seed ACO 42.
Input manual meminta parameter; Enter memakai default. Eksperimen memakai rancangan
tetap sehingga tidak terpengaruh parameter yang dimasukkan pada menu 2.

Contoh aktual: pilih **2**, masukkan **5** pelanggan, lalu isi setiap nama, X, Y
secara berurutan sesuai tabel berikut (satu jawaban setiap pertanyaan):

| Urutan | Nama | X (km) | Y (km) |
|---:|---|---:|---:|
| 0, depot | Toko | 0 | 0 |
| 1 | Pelanggan A | 2 | 3 |
| 2 | Pelanggan B | 5 | 1 |
| 3 | Pelanggan C | 6 | 5 |
| 4 | Pelanggan D | 1 | 6 |
| 5 | Pelanggan E | 8 | 3 |

Tekan Enter pada enam pertanyaan parameter untuk memakai **20 semut, 100 iterasi,
alpha=1, beta=2, rho=0.5, seed=42**. Q tetap 1. Input ini menghasilkan contoh yang
sama dengan demo. Depot boleh berada di koordinat lain. Koordinat negatif dan
lokasi berimpit diperbolehkan. Desimal boleh memakai titik atau koma.
Jumlah pelanggan/semut/iterasi harus bilangan bulat positif; alpha/beta >=0,
0<rho<1, seed bilangan bulat >=0. Nama tidak boleh kosong, NaN/infinity ditolak.
Jumlah sangat besar membuat pencarian dan grafik mahal; tidak ada batas kapasitas
kendaraan yang disisipkan ke model.

## Alur yang perlu dijelaskan saat presentasi

1. **Input lokasi.** Setiap lokasi berupa `(nama, x, y)`, indeks 0 selalu depot.
   Demo memakai tabel di atas; manual memakai jawaban pengguna. Eksperimen membuat
   pelanggan acak uniform pada persegi 20 × 20 km dengan seed data terpisah.
2. **Matriks jarak.** `buat_matriks_jarak()` memakai
   `d(i,j)=sqrt((xi-xj)^2+(yi-yj)^2)`. Contoh Toko ke A:
   `sqrt((2-0)^2+(3-0)^2)=sqrt(13)=3.605551 km`. Diagonal nol;
   jarak Toko–A sama dengan A–Toko.
3. **Semut membangun rute.** Mulai di depot, pilih hanya pelanggan yang belum
   dikunjungi dengan bobot `tau^alpha * (1/jarak)^beta`. Peluang = bobot dibagi
   total bobot kandidat. Pilihan acak berbobot, bukan selalu pelanggan terdekat.
   Feromon awal 1. Dengan beta=2, bobot awal Toko–A adalah `1/13`; peluangnya
   sekitar **44,6%** setelah dibandingkan dengan seluruh lima pelanggan.
   Pelanggan terpilih dihapus dari daftar sisa; setelah habis, semut kembali ke depot.
4. **Ukur dan simpan terbaik.** Panjang rute = jumlah jarak semua sisi, termasuk
   kembali ke depot. Ganti solusi terbaik hanya jika kandidat lebih pendek.
5. **Perbarui feromon.** Setelah semua semut membuat rute, evaporasi
   `tau <- (1-rho)*tau`. Dengan rho=0.5, feromon awal 1 menjadi 0.5.
   Lalu **setiap semut** menambah `Q/L` ke semua sisi yang dipakainya, dua arah.
   Untuk L=23.399846 dan Q=1, tambahan sekitar 0.042735 per sisi dari semut itu.
   Tidak ada deposit elit atau 2-opt di dalam ACO: ini tetap varian **Ant System**.
6. **Ulangi dan bandingkan.** Ulangi 100 iterasi, masing-masing 20 semut (2.000
   kandidat). Bandingkan solusi terbaik dengan urutan data, NN, dan NN + 2-opt.
   Brute force hanya untuk <=9 pelanggan; lebih besar tidak diklaim optimum.

Contoh output aktual: rute awal **32.593005 km**. ACO seed 42 memperoleh
**Toko → B → E → C → D → A → Toko**, panjang **23.399846 km**.
NN memperoleh arah sebaliknya dengan panjang sama. Brute force memeriksa
**120 urutan (5!)** dan membuktikan panjang tersebut optimum untuk data ini.
ACO sudah mencapai optimum di iterasi pertama, sehingga kurva demo datar.

**Waktu komputasi** dalam detik berasal dari `perf_counter()`: lama komputer
mencari rute. Bukan lama kurir mengantar barang. Pengurangan jarak tidak membuktikan
pengiriman lebih cepat atau tepat waktu. Timer tidak memasukkan pembuatan data,
pencetakan, penulisan file, atau plotting. NN + 2-opt mencakup biaya NN.

## Parameter dan pembanding

| Parameter | Makna |
|---|---|
| Semut / iterasi | Kandidat per generasi / jumlah generasi pencarian |
| alpha | Pengaruh feromon; nol berarti mengabaikan feromon |
| beta | Pengaruh preferensi jarak pendek; nol mengabaikan heuristik jarak |
| rho | Bagian feromon yang menguap setiap iterasi |
| Q | Skala deposit, tetap 1 |
| Seed ACO | Membuat pilihan acak dapat diulang; bukan seed pembuat data |

NN memilih pelanggan terdekat dari depot. NN + 2-opt membalik segmen pelanggan
jika jarak turun lebih dari 1e-9 km, sampai tidak ada perbaikan lagi. Depot tetap
di kedua ujung. Hasilnya optimum lokal 2-opt, bukan jaminan optimum global.
ACO memakai log-bobot ternormalisasi agar tidak overflow; rumus probabilitas tetap
sama. Epsilon 1e-12 melindungi pembagian/log nol dan menjadi lantai feromon;
jarak asli rute tidak diubah. Parameter ekstrem yang overflow ditolak.

## Eksperimen dan arti keluarannya

Hasil utama 12 Oktober 2026 dipertahankan: ukuran **5, 10, 20, 50**, seed data
**101, 202, 303**, seed ACO **0–19** per instance/config. Sensitivitas pada 20
pelanggan mengubah satu parameter setiap kali: alpha `{0.5,1,2}`, beta `{1,2,5}`,
rho `{0.1,0.5,0.9}`. Konfigurasi dasar dipakai ulang. Uji anggaran: **10×200,
20×100, 40×50**, masing-masing 2.000 kandidat. Total **720 run ACO, 759 baris CSV**.

| Output | Artinya |
|---|---|
| `hasil_mentah.csv` | Satu baris per run: instance, seed data/algoritma, parameter, rute, km, waktu, optimum/gap jika tersedia |
| `ringkasan_instance.csv` | Min/max/mean/std antar-seed pada data yang sama, waktu mean, perbaikan relatif, frekuensi optimum |
| `ringkasan_ukuran.csv` | Mean persentase relatif antar-instance, berbobot sama; std antar-instance dipisah dari std antar-seed |
| `riwayat_*.csv` | Best-so-far satu run ACO seed 0 per instance |
| `instances.json`, `metadata.json` | Koordinat persis, rancangan, seed, interpreter, jumlah run, durasi pipeline |
| `demo_*` / `manual_*` | Empat rute dan kurva satu run; input JSON, hasil dan riwayat CSV untuk input baru |
| `ilustrasi_n20_*` | Empat rute dan kurva satu run: data 101, seed ACO 0, 20 pelanggan |
| `kualitas_waktu.png` | Kualitas relatif dan waktu rata-rata menurut ukuran; waktu berskala log |
| `sensitivitas.png` | Mean +/- std antar-seed per instance, untuk alpha/beta/rho |
| `anggaran.png` | Kualitas dan waktu tiga konfigurasi 2.000 kandidat |

Pada peta, nomor titik mengikuti indeks lokasi, kotak merah adalah depot, panah
adalah arah kunjungan; X/Y dalam km dengan skala yang sama. Kurva menunjukkan
jarak **terbaik sampai iterasi tersebut**, sehingga tidak naik; garis NN dan
NN + 2-opt menjadi pembanding. Ilustrasi satu run bukan ringkasan banyak run.

Perbaikan = `(baseline - metode)/baseline * 100%`: positif lebih pendek,
negatif lebih panjang. Gap = `(metode - optimum)/optimum * 100%`; kosong jika
optimum tidak diketahui. Std baseline nol berasal dari satu hasil deterministik.

Bukti utama: ACO vs NN + 2-opt rata-rata **0%, -0.094%, +2.026%, -0.251%** untuk
5/10/20/50 pelanggan. NN + 2-opt jauh lebih cepat. ACO tidak selalu menang.
Semua 60 run ACO lima pelanggan mencapai optimum. Lihat [laporan](LAPORAN.md) untuk
angka lengkap dan [tanya jawab](PRESENTASI.md) untuk latihan presentasi.

## Struktur sederhana dan audit

`main.py` berisi empat bagian bernomor: (1) data/algoritma, (2) eksperimen/CSV,
(3) grafik, (4) input/menu. Mulai belajar dari `menu()` → `jalankan_demo()` →
`jalankan_aco()` → `_buat_rute()`. Bagian eksperimen mengulang fungsi yang sama.
`app.py` adalah antarmuka web lokal yang memakai ulang main.py.
`test_proyek.py` khusus pembuktian; class hanya dipakai oleh unittest, bukan desain
program. `requirements.txt` memuat Matplotlib dan Streamlit beserta dependensi
transitif yang dipasang pip. Laporan serta hasil penelitian lama tetap dipertahankan.

| File/folder lama | Keputusan dan alasan |
|---|---|
| `main.py` | Dipertahankan; seluruh fungsi program disatukan |
| `algoritma.py`, `eksperimen.py`, `visualisasi.py` | Digabung ke main; import antarfile dihilangkan |
| `buat_laporan.py` | Dihapus; generator panjang tidak diperlukan untuk menjalankan penelitian; LAPORAN.md tetap ada |
| `main_original.py.bak` | Dihapus; salinan kode rusak, data demo telah diperiksa sama, fungsi relevan sudah digabung |
| `__pycache__/` | Cache otomatis dihapus; dapat dibuat lagi oleh Python |
| `output_cepat/` | Dipindah utuh ke `output/pemeriksaan_awal/`, tanpa membuang bukti lama |
| `test_proyek.py` | Dipertahankan, import diperbarui dan uji menu/manual ditambah |
| README / LAPORAN / PRESENTASI | Dipertahankan; panduan dan referensi struktur diperbarui |
| `output/`, requirements, `.gitignore` | Dipertahankan; hasil utama tidak diubah |

Algoritma, data, konfigurasi dan seed tidak berubah. Pemeriksaan AST sebelum
penghapusan membandingkan fungsi lama/baru; uji cepat membandingkan 25 baris baru
dengan hasil utama lama (rute dan jarak, tidak waktu). Karena identik, eksperimen
utama digunakan kembali; waktu lama tetap disebut pengukuran 12 Oktober, bukan
benchmark baru. Pengujian juga memeriksa seluruh 759 rute lama.

## Keterbatasan dan referensi

Tiga instance per ukuran belum cukup untuk generalisasi. Seed data sama antarukuran
memakai prefix lokasi sama; bukan 12 instance sepenuhnya independen. Belum ada
test set parameter terpisah atau uji signifikansi. Waktu baseline hanya sekali ukur
dan sangat singkat. Kandidat sama tidak menjamin waktu komputasi sama. NN satu
konstruksi greedy; ACO 2.000 kandidat, sehingga biaya pencariannya berbeda.
Brute force faktorial, dibatasi 9 pelanggan; ACO tidak menjamin optimum pada kasus
besar. Referensi primer yang sudah diverifikasi tercatat di laporan:
[Dorigo dkk., 1996](https://doi.org/10.1109/3477.484436) dan
[Croes, 1958](https://pubsonline.informs.org/doi/10.1287/opre.6.6.791).
