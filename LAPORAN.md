# Laporan ringkas UTS Swarm Intelligence

Tanggal pelaksanaan: 12 Oktober 2026. Seluruh angka di bawah dibaca dari CSV aktual, bukan hasil perkiraan.

## Masalah dan metode

Tujuan: meminimumkan jarak satu kurir dari depot, mengunjungi setiap pelanggan sekali, dan kembali ke depot. Jarak Euclidean simetris dalam km; seluruh pesanan diasumsikan dapat dibawa sekaligus. Model tidak memasukkan waktu tempuh, kemacetan, kapasitas, atau batas waktu.

Ant System menggunakan pemilihan proporsional tau^alpha × (1/jarak)^beta, evaporasi (1-rho)tau, dan deposit Q/L oleh seluruh semut di sisi rutenya dengan pembaruan simetris. Feromon awal 1; konfigurasi awal 20 semut, 100 iterasi, alpha=1, beta=2, rho=0.5, Q=1. Solusi terbaik disimpan sepanjang pencarian. NN + 2-opt adalah pembanding tersendiri, tanpa diterapkan ke ACO.

Pembanding: urutan data, NN dari depot, NN + 2-opt first improvement sampai tidak ada perbaikan >1e-9 km, dan brute force maksimal 9 pelanggan. Log-bobot ternormalisasi menghindari overflow; epsilon 1e-12 melindungi heuristik/deposit/feromon, sedangkan jarak rute tetap asli.

## Pelaksanaan eksperimen

Pemeriksaan cepat: 12 run ACO, satu seed data dan satu seed ACO per konfigurasi, selesai sekitar 4,1 detik termasuk grafik. Waktu ACO satu run sekitar 0,014 detik pada 5 pelanggan sampai 0,433 detik pada 50 pelanggan. Hasil cepat berada di output/pemeriksaan_awal dan tidak digabung ke evaluasi utama.

Eksperimen utama selesai: **720 run ACO, 759 baris mentah**, durasi pipeline 92.91 detik. Python 3.14.4, Windows-11-10.0.26200-SP0. Ukuran 5/10/20/50 pelanggan, seed data 101/202/303, seed ACO 0–19. Pelanggan uniform pada persegi 20 × 20 km, depot (0,0). Seluruh metode memakai instance yang sama. Koordinat lengkap dan konfigurasi tersimpan dalam JSON.

Alokasi run: 240 konfigurasi awal (4 ukuran × 3 instance × 20 seed), 360 konfigurasi tambahan sensitivitas (6 × 3 × 20), dan 120 tambahan anggaran (2 × 3 × 20). Baseline deterministik dijalankan sekali per instance; brute force dijalankan pada tiga instance 5 pelanggan.

Waktu pencarian memakai perf_counter pada pemanggilan algoritma beserta validasi internal dan perhitungan jarak hasil; pembuatan data, pencetakan, grafik, dan penulisan file berada di luar timer. Waktu NN + 2-opt mencakup NN. Waktu baseline yang singkat dan sekali ukur bersifat indikatif, bukan benchmark presisi. Beban sistem dan aktivitas verifikasi dapat memengaruhi pengukuran.

## Demo data awal

Rute awal 32,593005 km. NN, NN + 2-opt, dan ACO seed 42 menghasilkan 23,399846 km, sama dengan optimum brute force dari 120 urutan. Pengurangan terhadap rute awal sekitar 28,21%. ACO sudah mencapai optimum pada iterasi pertama. Rute ACO berlawanan arah dengan NN dan ekuivalen pada jarak simetris.

## Perbandingan menurut ukuran

Angka kualitas adalah mean persentase relatif per instance, kemudian dirata-ratakan atas tiga instance dengan bobot sama. Positif berarti lebih pendek dari baseline; negatif berarti lebih panjang.

| Pelanggan | ACO vs NN (%) | ACO vs NN + 2-opt (%) | NN + 2-opt vs NN (%) | Waktu ACO (s) | Waktu NN (s) | Waktu NN + 2-opt (s) |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | 12.047 | 0.000 | 12.047 | 0.016031 | 0.000022 | 0.000032 |
| 10 | 9.836 | -0.094 | 9.920 | 0.037461 | 0.000047 | 0.000097 |
| 20 | 9.304 | 2.026 | 7.395 | 0.101101 | 0.000102 | 0.000230 |
| 50 | 13.318 | -0.251 | 13.481 | 0.449689 | 0.000486 | 0.002535 |

ACO awal lebih baik dari NN pada mean semua ukuran, tetapi **tidak selalu lebih baik dari NN + 2-opt**. Pada 10 dan 50 pelanggan, mean jarak ACO sedikit lebih panjang; pada 20 pelanggan ACO lebih pendek sekitar 2,026%. NN + 2-opt jauh lebih cepat pada seluruh ukuran yang diukur. Biaya pencarian memang berbeda: ACO membuat 2.000 kandidat, NN satu konstruksi greedy.

## Variasi antar-seed pada masing-masing instance

Setiap baris berikut memuat 20 seed ACO konfigurasi awal. Std adalah simpangan baku sampel **antar-seed**, bukan antar-instance. Tidak ada optimum terverifikasi untuk ukuran di atas 9 pelanggan.

| Instance | Terbaik (km) | Terburuk (km) | Mean (km) | Std seed (km) | Mencapai optimum |
|---|---:|---:|---:|---:|---|
| n5_d101 | 59.3036 | 59.3036 | 59.3036 | 0.0000 | 20/20 |
| n5_d202 | 53.4702 | 53.4702 | 53.4702 | 0.0000 | 20/20 |
| n5_d303 | 65.4189 | 65.4189 | 65.4189 | 0.0000 | 20/20 |
| n10_d101 | 74.2712 | 74.6261 | 74.2890 | 0.0793 | Tidak diketahui |
| n10_d202 | 57.2960 | 59.8760 | 57.4439 | 0.5786 | Tidak diketahui |
| n10_d303 | 80.0059 | 80.0059 | 80.0059 | 0.0000 | Tidak diketahui |
| n20_d101 | 84.4809 | 89.8927 | 88.0408 | 1.8588 | Tidak diketahui |
| n20_d202 | 78.3415 | 78.3415 | 78.3415 | 0.0000 | Tidak diketahui |
| n20_d303 | 91.1765 | 93.5165 | 91.5644 | 0.6195 | Tidak diketahui |
| n50_d101 | 122.9578 | 133.7012 | 127.2449 | 2.7484 | Tidak diketahui |
| n50_d202 | 124.3919 | 137.6228 | 131.2255 | 3.2928 | Tidak diketahui |
| n50_d303 | 118.4176 | 125.5412 | 121.9166 | 2.1041 | Tidak diketahui |

Seluruh 60 run ACO pada tiga instance lima pelanggan mencapai optimum (100%). NN + 2-opt juga mencapai optimum pada ketiga instance tersebut. NN belum mencapai optimum pada ketiganya. Std nol pada suatu instance berarti seluruh seed menghasilkan jarak sama; ini tidak membuktikan optimum pada ukuran yang tidak diperiksa secara exact.

## Sensitivitas OFAT pada 20 pelanggan

Satu parameter diubah setiap kali; parameter lain tetap konfigurasi awal. Semua konfigurasi memakai tiga instance dan 20 seed yang sama. Nilai tengah memakai ulang run awal. Tabel memuat mean relatif antar-instance.

| Konfigurasi | Perbaikan vs NN (%) | Perbaikan vs NN + 2-opt (%) | Waktu mean (s) |
|---|---:|---:|---:|
| dasar | 9.304 | 2.026 | 0.101101 |
| alpha_0.5 | 7.795 | 0.311 | 0.105116 |
| alpha_2 | 8.000 | 0.588 | 0.103869 |
| beta_1 | 10.343 | 3.069 | 0.101217 |
| beta_5 | 8.092 | 0.704 | 0.098892 |
| rho_0.1 | 10.395 | 3.136 | 0.112749 |
| rho_0.9 | 8.892 | 1.578 | 0.106259 |

Di antara konfigurasi OFAT yang diuji, rho=0,1 memberikan mean relatif terbaik terhadap NN + 2-opt (sekitar 3,136%), diikuti beta=1 (3,069%). Alpha awal 1 lebih baik secara agregat daripada 0,5 atau 2. Beta lebih besar tidak otomatis lebih baik. Grafik menunjukkan respons berbeda antar-instance, misalnya beta=1 tidak menjadi mean terbaik pada data 303. Ini hasil eksploratif pada data yang diuji, bukan parameter terbaik universal; interaksi parameter belum diuji.

## Anggaran jumlah kandidat yang sama

| Semut × iterasi | Kandidat per run | Perbaikan vs NN + 2-opt (%) | Waktu mean (s) |
|---|---:|---:|---:|
| 10 × 200 | 2.000 | 1.553 | 0.117688 |
| 20 × 100 | 2.000 | 2.026 | 0.101101 |
| 40 × 50 | 2.000 | 2.446 | 0.099999 |

Pada sampel ini 40 × 50 memberi mean kualitas lebih baik dan waktu sedikit lebih rendah daripada 20 × 100; 10 × 200 lebih lama dan mean perbaikannya lebih kecil. Banyaknya pembaruan generasi berbeda walaupun kandidat sama. Hasil ini tidak menetapkan aturan universal.

## Verifikasi dan keluaran

Mode cepat, demo, dan eksperimen utama berhasil. Tujuh pengujian unittest lulus: optimum demo dan reproduksi seed, riwayat tidak meningkat, 2-opt valid/tidak memburuk/berhenti lokal, validitas seluruh rute semut pada run uji, deposit seluruh semut dan evaporasi simetris, kasus jarak nol/parameter invalid, import tanpa eksekusi, serta artefak lengkap. Beberapa sifat digabung dalam satu metode pengujian. Seluruh 759 rute hasil diperiksa lagi beserta kecocokan jaraknya; semua riwayat run diperiksa saat eksperimen. Kompilasi dan eksekusi program dengan warning default tidak mengeluarkan warning. Ruff/pyflakes tidak tersedia; tidak ada klaim pemeriksaan linter yang tidak dijalankan.

Catatan verifikasi awal: ResourceWarning pada perintah bantu pembacaan CSV diperbaiki dengan menutup file melalui context manager. Warning tidak disembunyikan. Generator laporan pada versi awal telah dihapus saat konsolidasi; laporan hasil aktual ini dipertahankan.

Grafik: [rute demo](output/demo_rute.png), [konvergensi demo](output/demo_konvergensi.png), [rute n20](output/ilustrasi_n20_rute.png), [konvergensi n20](output/ilustrasi_n20_konvergensi.png), [kualitas dan waktu](output/kualitas_waktu.png), [sensitivitas](output/sensitivitas.png), [anggaran](output/anggaran.png). Ilustrasi satu run dipisahkan dari ringkasan banyak run. CSV mentah, ringkasan instance/ukuran, koordinat JSON, metadata, dan riwayat tersedia di output.

## Keterbatasan dan kesimpulan

Tiga instance per ukuran belum mewakili seluruh TSP. Data bersifat uniform simulasi; ukuran dengan seed data sama memakai prefix koordinat yang sama sehingga ukuran tidak sepenuhnya independen. Pemilihan parameter dan evaluasi masih pada data yang sama, tanpa test set terpisah atau uji signifikansi. Timing dapat berubah menurut mesin dan beban proses. Brute force dibatasi sesuai rancangan, sehingga tidak tersedia bukti optimum untuk 10, 20, dan 50 pelanggan.

Ant System berhasil menurunkan jarak relatif terhadap NN pada mean semua ukuran, tetapi NN + 2-opt merupakan pembanding kuat dan jauh lebih murah secara komputasi pada eksperimen ini. Keuntungan ACO bergantung instance dan parameter. Pengurangan jarak tidak membuktikan pengiriman lebih cepat atau tepat waktu. Pengembangan selanjutnya: data jalan nyata, waktu tempuh, kapasitas/VRP, banyak kurir, time windows, lebih banyak instance, serta evaluasi parameter pada test set terpisah. Tidak ada eksperimen yang masih tertunda.

## Referensi primer yang diverifikasi

1. Dorigo, M., Maniezzo, V., & Colorni, A. (1996). Ant System: Optimization by a Colony of Cooperating Agents. IEEE Transactions on Systems, Man, and Cybernetics, Part B, 26(1), 29–41. [DOI](https://doi.org/10.1109/3477.484436). Metadata diperiksa melalui [daftar publikasi penulis](https://iridia.ulb.ac.be/~mdorigo/HomePageDorigo/publicationsbyyear.php) yang terindeks; pengambilan teks PDF penuh terhalang redirect.
2. Croes, G. A. (1958). A Method for Solving Traveling-Salesman Problems. Operations Research, 6(6), 791–812. [Halaman penerbit](https://pubsonline.informs.org/doi/10.1287/opre.6.6.791), metadata dan abstrak diverifikasi. Tidak mengklaim akses teks penuh.

Untuk instalasi, rumus lengkap, definisi kolom, dan langkah menjalankan lihat README.md. Untuk latihan sidang lihat PRESENTASI.md.

## Penyederhanaan 14 Oktober 2026

Seluruh fungsi program digabung dalam main.py dengan empat bagian bernomor.
Menu terminal dan input manual nama/koordinat serta parameter ACO ditambahkan;
test_proyek.py tetap terpisah khusus pengujian. Tidak ada class dalam program.
Data, fungsi algoritma, konfigurasi dan seed eksperimen tidak berubah: AST
fungsi lama/baru dibandingkan sebelum file lama dihapus. Pemeriksaan cepat
menghasilkan rute dan jarak identik pada 25 baris yang bersesuaian dengan hasil
utama. Karena itu 720 run lama digunakan kembali; waktu di tabel tetap merupakan
pengukuran 12 Oktober 2026, bukan pengukuran kinerja baru setelah konsolidasi.
Input manual hanya menghasilkan ilustrasi satu run, bukan pengganti evaluasi
banyak seed. Hasil baru disimpan terpisah dalam subfolder output.

Verifikasi setelah penyederhanaan mencakup menu demo/manual/keluar, input salah,
parameter default dan kustom, depot bebas, jarak nol, satu iterasi, reproduksi
seed, riwayat tidak meningkat, 2-opt, rancangan lama, seluruh 759 rute hasil,
serta eksperimen cepat dengan CSV dan grafik. Cara menjalankan dan penjelasan
input -> proses -> output ada di README.md.

Hasil akhir: **13 pengujian lulus** dengan warning dijadikan error pada pengujian CLI. Seluruh **24 file hasil utama lama memiliki SHA-256 yang sama** sebelum dan sesudah konsolidasi. Log: `output/verifikasi_penyederhanaan.txt`. Contoh input manual dan grafik: `output/contoh_manual/`. Tidak ada eksperimen ulang utama yang diperlukan.
