# Pertanyaan dan jawaban presentasi

**1. Mengapa memilih ACO?**
ACO cocok untuk pencarian kombinatorial berupa urutan kunjungan. Semut membuat
kandidat secara acak berbobot dan berbagi informasi melalui feromon. Proyek ini
menguji kekuatan serta biaya pendekatan itu dibanding heuristik sederhana; ACO
tidak otomatis lebih unggul.

**2. Apa yang dioptimalkan?**
Total jarak Euclidean satu putaran depot–pelanggan–depot. Setiap pelanggan dikunjungi
sekali, seluruh pesanan dibawa sekaligus. Bukan waktu tempuh, biaya bahan bakar,
atau ketepatan waktu yang belum dimodelkan.

**3. Mengapa ACO bisa sama dengan nearest neighbor?**
Pada contoh lima pelanggan, NN kebetulan sudah mencapai optimum yang dibuktikan
brute force 120 urutan. ACO tidak dapat memperbaiki optimum tersebut. Rute terbalik
juga setara karena jarak simetris. Kasus kecil ini tidak cukup untuk menggeneralisasi.

**4. Apa pengaruh alpha, beta, dan rho?**
Alpha memperkuat pilihan mengikuti feromon, beta memperkuat preferensi jarak dekat,
rho mengatur seberapa cepat jejak lama menguap. Nilai besar dapat mengubah keseimbangan
eksplorasi dan eksploitasi; tidak ada nilai terbaik universal. Grafik sensitivitas
menampilkan OFAT pada tiga instance 20 pelanggan, dengan parameter lain tetap.
Lihat LAPORAN.md untuk angka aktual, termasuk hasil yang lebih buruk.

**5. Mengapa perlu beberapa seed?**
Satu seed bisa beruntung. Dua puluh seed ACO menunjukkan rata-rata, sebaran, dan
hasil terburuk pada data yang sama. Tiga seed data menguji pengaruh susunan lokasi.
Variasi data dan variasi pencarian dilaporkan terpisah.

**6. Apakah hasilnya optimum?**
Ya untuk demo dan hasil yang cocok dengan brute force pada kasus kecil, dalam
toleransi numerik. Untuk 10, 20, 50 pelanggan optimum tidak dihitung; hasil hanya
dibandingkan terhadap baseline. Solusi terbaik di antara metode bukan bukti optimum.

**7. Mengapa membandingkan NN + 2-opt?**
NN cepat tetapi greedy dan tidak memperbaiki keputusan sebelumnya. 2-opt membalik
segmen pelanggan jika memperpendek dua sambungan batas. Ini pembanding yang lebih
kuat dengan biaya relatif kecil. 2-opt tidak ditambahkan ke ACO agar Ant System
yang dievaluasi tetap jelas.

**8. Apakah jarak minimum selalu berarti waktu minimum?**
Tidak. Kemacetan, kecepatan ruas, waktu layanan, dan jam kedatangan memengaruhi
waktu tempuh. Waktu komputasi dalam CSV adalah waktu komputer mencari rute, bukan
lama kurir mengirim barang. Proyek hanya menyimpulkan pengurangan jarak simulasi.

**9. Apa perbedaan Ant System dengan ACO secara umum?**
ACO adalah keluarga metode. Varian di sini memakai evaporasi lalu deposit `Q/L`
oleh semua semut, pada sisi dua arah. Tidak ada deposit hanya oleh semut terbaik,
batas feromon teroptimasi, atau local search pada solusi ACO.

**10. Mengapa anggaran 2.000 kandidat belum tentu sama cepat?**
10x200 melakukan dua kali jumlah pembaruan generasi dibanding 20x100, sedangkan
40x50 hanya setengahnya. Overhead iterasi, perhitungan bobot, dan beban komputer
memengaruhi waktu aktual. Seed yang sama membantu perbandingan, tetapi tidak
menjamin keputusan acak identik setelah feromon berkembang berbeda.

**11. Bagaimana menangani lokasi berimpit dan angka pecahan?**
Jarak asli tetap nol. Epsilon dipakai hanya dalam heuristik, deposit, dan lantai
feromon agar tidak membagi atau mengambil log nol. Log-bobot dinormalisasi sebelum
eksponensiasi. Perbandingan jarak memakai toleransi, tidak mengunci arah rute.

**12. Apa keterbatasan dan pengembangan berikutnya?**
Hanya data uniform simulasi dan tiga instance per ukuran; belum mewakili jalan nyata.
Parameter diuji pada data yang sama sehingga temuan eksploratif, bukan bukti
generalisasi. Selanjutnya gunakan instance lebih banyak, data pengujian terpisah,
waktu ruas nyata, kapasitas kendaraan, banyak kurir, dan batas waktu pengiriman.

**13. Dari mana data masuk ke program?**
Ada tiga sumber: data awal dalam LOKASI_DEMO, koordinat yang diketik pada menu 2,
dan data simulasi uniform dari buat_data() untuk eksperimen. Nama dan koordinat
depot juga dapat diketik. Argumen terminal hanya mengatur mode, folder, dan
pembukaan grafik. Seed data menentukan lokasi, seed ACO menentukan pilihan semut.

**14. Jelaskan alur dengan contoh nyata.**
Toko (0,0) dan A (2,3) menghasilkan jarak sqrt(13)=3,605551 km. Semua pasangan
lokasi dihitung menjadi matriks simetris. Semut dari depot memilih pelanggan
belum dikunjungi secara acak berbobot feromon dan jarak. Setelah semua pelanggan,
semut kembali ke toko. Panjang rute dibandingkan dengan terbaik sebelumnya.
Feromon menguap lalu semua semut deposit Q/L pada sisi dua arah. Sesudah 100
iterasi, ACO seed 42 menghasilkan Toko-B-E-C-D-A-Toko, 23,399846 km.
Brute force 120 urutan membuktikan optimum untuk lima pelanggan pada data ini.

**15. Bagian kode mana yang perlu saya baca pertama?**
Di main.py, baca menu() untuk pilihan pengguna, jalankan_demo() untuk alur utama,
jalankan_aco() untuk tiga langkah Ant System, lalu _buat_rute() untuk roulette
wheel. Bagian eksperimen hanya memanggil algoritma yang sama dengan data,
parameter, dan seed berbeda, lalu menghitung statistik dan menyimpan CSV.
