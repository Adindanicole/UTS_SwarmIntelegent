"""Antarmuka Streamlit lokal; seluruh algoritma dipakai ulang dari main.py."""
import csv
import io
import json
import math
from time import perf_counter

import streamlit as st
from matplotlib.figure import Figure
import main as algoritma


NAMA_METODE = {
    "Awal": "Rute Awal",
    "NN": "Pelanggan Terdekat",
    "NN_2opt": "Pelanggan Terdekat + Perbaikan Rute",
    "ACO": "Rute Hasil ACO",
}
KUNCI_INPUT = ["sumber", "nama_toko", "x_toko", "y_toko", "pelanggan",
               "jumlah_semut", "jumlah_iterasi", "alpha", "beta", "rho", "seed",
               "hasil", "metode_grafik"]


def reset_input():
    """Callback dijalankan sebelum widget dibuat ulang, sehingga aman di-reset."""
    for kunci in KUNCI_INPUT:
        st.session_state.pop(kunci, None)


def angka(nilai, label):
    """Validasi juga di sisi Python, termasuk sel kosong, NaN dan infinity."""
    if nilai is None or isinstance(nilai, bool) or not str(nilai).strip():
        raise ValueError(f"{label} harus diisi dengan angka.")
    try:
        hasil = float(str(nilai).strip().replace(",", "."))
    except (ValueError, OverflowError):
        raise ValueError(f"{label} harus berupa angka yang valid.") from None
    if not math.isfinite(hasil):
        raise ValueError(f"{label} harus berupa angka berhingga, bukan NaN atau infinity.")
    return hasil


def validasi_lokasi(toko, pelanggan):
    """Terima toko dan tabel pelanggan; lokasi berimpit tetap diperbolehkan."""
    if not pelanggan:
        raise ValueError("Isi minimal satu pelanggan pada tabel.")
    lokasi = []
    for i, row in enumerate([toko, *pelanggan]):
        label = "toko" if i == 0 else f"pelanggan baris {i}"
        nama = row.get("Nama")
        if not isinstance(nama, str) or not nama.strip():
            raise ValueError(f"Nama {label} tidak boleh kosong.")
        lokasi.append((nama.strip(), angka(row.get("X"), f"X {label}"),
                       angka(row.get("Y"), f"Y {label}")))
    return lokasi


def csv_bytes(rows):
    """CSV dibuat di memori; UTF-8 BOM membantu nama terbaca di Excel Windows."""
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8-sig")


def cari_rute(lokasi, parameter):
    """Hanya dipanggil saat tombol pencarian ditekan, tanpa brute force/file I/O."""
    d = algoritma.buat_matriks_jarak(lokasi)
    algoritma.validasi_matriks(d)
    hasil = {}
    for metode in NAMA_METODE:
        mulai = perf_counter()
        if metode == "Awal":
            rute = [*range(len(lokasi)), 0]
        elif metode == "NN":
            rute = algoritma.nearest_neighbor(d)
        elif metode == "NN_2opt":
            rute = algoritma.dua_opt(algoritma.nearest_neighbor(d), d)
        else:
            rute, _, riwayat = algoritma.jalankan_aco(d, **parameter)
        panjang = algoritma.hitung_total_jarak(rute, d)
        durasi = perf_counter() - mulai
        hasil[metode] = dict(rute=rute, jarak=panjang, waktu=durasi)
    return dict(lokasi=lokasi, parameter=parameter.copy(), metode=hasil, riwayat=riwayat)


def perbaikan(jarak, pembanding):
    """Persentase terhadap baseline nol tidak didefinisikan; jangan membagi nol."""
    if pembanding == 0:
        return "Tidak dihitung (jarak pembanding 0 km)"
    persen = (pembanding - jarak) / pembanding * 100
    if math.isclose(persen, 0, abs_tol=1e-9):
        return "0,00% (sama dalam toleransi numerik)"
    arah = "lebih pendek" if persen > 0 else "lebih panjang"
    return f"{abs(persen):.2f}% {arah}"


def grafik_rute(lokasi, rute, judul):
    """Grafik khusus web: nama lokasi, panah, depot berbeda, skala X/Y sama."""
    fig = Figure(figsize=(8, 6), layout="constrained")
    ax = fig.subplots()
    ax.plot([lokasi[i][1] for i in rute], [lokasi[i][2] for i in rute],
            "o-", color="#16856b", linewidth=1.7, label="Pelanggan / perjalanan")
    ax.scatter(lokasi[0][1], lokasi[0][2], marker="s", s=110, color="#1c4b82",
               zorder=5, label="Toko (awal dan akhir)")
    for a, b in zip(rute, rute[1:]):
        ax.annotate("", xy=lokasi[b][1:], xytext=lokasi[a][1:],
                    arrowprops=dict(arrowstyle="->", color="#16856b", lw=1.5))
    for i, (nama, x, y) in enumerate(lokasi):
        ax.annotate(f"{i}. {nama}", (x, y), xytext=(7, 9 + (i % 3)*10),
                    textcoords="offset points", fontsize=9)
    ax.set(title=judul, xlabel="X (km)", ylabel="Y (km)")
    ax.set_aspect("equal", adjustable="box")
    ax.margins(.25)
    ax.grid(alpha=.2)
    ax.legend(fontsize=8)
    return fig


def tampilkan_hasil(hasil, perlu_diperbarui):
    lokasi, metode = hasil["lokasi"], hasil["metode"]
    if perlu_diperbarui:
        st.warning("Input atau pengaturan berubah. Hasil di bawah berasal dari pencarian sebelumnya. Klik Cari Rute Pengiriman untuk memperbarui.")
    st.subheader("4. Rute Hasil ACO")
    cols = st.columns(3)
    cols[0].metric("Total jarak ACO", f"{metode['ACO']['jarak']:.6f} km")
    cols[1].metric("Jumlah pelanggan", len(lokasi)-1)
    cols[2].metric("Waktu pencarian ACO", f"{metode['ACO']['waktu']:.6f} detik")
    st.caption("Waktu pencarian adalah lama komputer mencari rute ACO, bukan waktu perjalanan kurir. Hasil ini adalah satu percobaan, bukan ringkasan banyak seed.")
    st.write("**Urutan kunjungan ACO**")
    st.dataframe([{"Kunjungan": urut, "Lokasi": lokasi[i][0],
                   "Keterangan": "Kembali ke toko" if urut == len(metode["ACO"]["rute"]) else ("Berangkat dari toko" if urut == 1 else "Pelanggan")}
                  for urut, i in enumerate(metode["ACO"]["rute"], 1)], hide_index=True, width="stretch")
    st.write("**Perbandingan hasil pada lokasi yang sama**")
    ringkasan = [{"Metode": NAMA_METODE[k], "Total jarak (km)": v["jarak"],
                  "Waktu komputer (detik)": v["waktu"]} for k, v in metode.items()]
    st.dataframe(ringkasan, hide_index=True, width="stretch",
                 column_config={"Total jarak (km)": st.column_config.NumberColumn(format="%.6f"),
                                "Waktu komputer (detik)": st.column_config.NumberColumn(format="%.6f")})
    for key in ("NN", "NN_2opt"):
        st.write(f"ACO dibanding {NAMA_METODE[key]}: {perbaikan(metode['ACO']['jarak'], metode[key]['jarak'])}.")
    st.caption("Semua metode memakai data yang sama, tetapi biaya pencariannya berbeda. Hasil ACO tidak dijamin optimum; tidak ada brute force yang dijalankan pada halaman ini.")
    pilihan = st.selectbox("Lihat grafik rute metode", ["ACO", "Awal", "NN", "NN_2opt"],
                          format_func=NAMA_METODE.get, key="metode_grafik")
    st.pyplot(grafik_rute(lokasi, metode[pilihan]["rute"], NAMA_METODE[pilihan]), width="stretch")
    if len({(x, y) for _, x, y in lokasi}) < len(lokasi):
        st.caption("Beberapa lokasi memiliki koordinat sama sehingga titik dapat bertumpuk. Semua kunjungan tetap tercantum dalam urutan rute.")
    with st.expander("Perkembangan Pencarian ACO"):
        fig = Figure(figsize=(8, 3.5), layout="constrained")
        ax = fig.subplots()
        ax.plot(range(1, len(hasil["riwayat"])+1), hasil["riwayat"], color="#16856b", label="Jarak terbaik sampai putaran ini")
        ax.set(xlabel="Putaran", ylabel="Jarak (km)", xlim=(1, max(2, len(hasil["riwayat"]))))
        ax.legend()
        ax.grid(alpha=.2)
        st.pyplot(fig, width="stretch")
        st.caption("Kurva datar berarti jarak terbaik tidak berubah. Kurva tidak menunjukkan waktu pengiriman.")
    # Unduhan hanya mengirim byte dari memori; tidak menulis folder output.
    export = []
    for k, v in metode.items():
        export.append(dict(metode=NAMA_METODE[k], jarak_km=v["jarak"], waktu_s=v["waktu"],
                           jumlah_pelanggan=len(lokasi)-1,
                           **{p: hasil["parameter"][p] if k == "ACO" else "" for p in hasil["parameter"]}))
    urutan = [dict(kunjungan=urut, metode=NAMA_METODE[pilihan], lokasi=lokasi[i][0],
                   x_km=lokasi[i][1], y_km=lokasi[i][2]) for urut, i in enumerate(metode[pilihan]["rute"], 1)]
    left, right = st.columns(2)
    left.download_button("Unduh Ringkasan CSV", csv_bytes(export), "ringkasan_rute.csv", "text/csv", on_click="ignore")
    right.download_button("Unduh Urutan Rute CSV", csv_bytes(urutan), "urutan_rute.csv", "text/csv", on_click="ignore",
                          help="Mengunduh urutan untuk metode yang dipilih pada grafik.")


def main():
    st.set_page_config(page_title="Optimasi Rute Pengiriman", page_icon="📍", layout="centered")
    st.title("Optimasi Rute Pengiriman")
    st.write("Cari urutan kunjungan pelanggan dengan total jarak yang lebih pendek.")
    st.caption("Simulasi satu kurir menggunakan jarak garis lurus. Belum memperhitungkan jalan, kemacetan, kapasitas kendaraan, atau batas waktu pengiriman.")
    st.subheader("1. Pilih sumber data")
    sumber = st.radio("Sumber lokasi", ["Gunakan Data Contoh", "Masukkan Lokasi Sendiri"], horizontal=True, key="sumber")
    st.subheader("2. Isi atau periksa lokasi")
    st.info("Gunakan koordinat simulasi dalam kilometer. Kolom ini bukan alamat atau koordinat GPS.")
    if sumber == "Gunakan Data Contoh":
        toko = dict(zip(("Nama", "X", "Y"), algoritma.LOKASI_DEMO[0]))
        pelanggan = [dict(zip(("Nama", "X", "Y"), p)) for p in algoritma.LOKASI_DEMO[1:]]
        st.dataframe([toko, *pelanggan], hide_index=True, width="stretch")
        st.caption("Baris pertama adalah toko; lima baris berikutnya adalah pelanggan.")
    else:
        c1, c2, c3 = st.columns([2, 1, 1])
        toko = {"Nama": c1.text_input("Nama toko", "Toko", key="nama_toko"),
                "X": c2.text_input("X toko (km)", "0", key="x_toko"),
                "Y": c3.text_input("Y toko (km)", "0", key="y_toko")}
        st.write("**Daftar pelanggan**")
        pelanggan = st.data_editor([{"Nama": "", "X": None, "Y": None}], key="pelanggan", num_rows="dynamic",
                                   hide_index=True, width="stretch", column_config={
                                       "Nama": st.column_config.TextColumn("Nama pelanggan", required=True),
                                       "X": st.column_config.NumberColumn("X (km)", required=True),
                                       "Y": st.column_config.NumberColumn("Y (km)", required=True)})
        st.caption("Klik sel untuk mengisi. Tambah baris melalui baris kosong di bawah tabel. Pilih baris lalu gunakan ikon hapus untuk menghapus pelanggan. Isi minimal satu pelanggan.")
    with st.expander("Pengaturan Pencarian"):
        c1, c2 = st.columns(2)
        parameter = dict(algoritma.DEFAULT, seed=42)
        parameter["jumlah_semut"] = c1.number_input("Jumlah semut", min_value=1, value=20, step=1, key="jumlah_semut", help="Banyak kandidat rute per putaran.")
        parameter["jumlah_iterasi"] = c2.number_input("Jumlah putaran", min_value=1, value=100, step=1, key="jumlah_iterasi", help="Banyak pengulangan pencarian.")
        parameter["alpha"] = c1.number_input("Alpha", min_value=0., value=1., key="alpha", help="Pengaruh jejak pencarian sebelumnya.")
        parameter["beta"] = c2.number_input("Beta", min_value=0., value=2., key="beta", help="Pengaruh kedekatan lokasi.")
        parameter["rho"] = c1.number_input("Penguapan", min_value=0., max_value=1., value=.5, step=.05, key="rho", help="Seberapa cepat jejak lama berkurang; harus lebih besar dari 0 dan kurang dari 1.")
        parameter["seed"] = c2.number_input("Seed", min_value=0, value=42, step=1, key="seed", help="Angka untuk mengulang percobaan yang sama.")
        st.caption("Q tetap 1. Pengaturan ini hanya untuk satu pencarian, bukan eksperimen utama.")
    signature = json.dumps([sumber, toko, pelanggan, parameter], sort_keys=True, ensure_ascii=False, default=str)
    st.subheader("3. Jalankan pencarian")
    cari, reset = st.columns([2, 1])
    diklik = cari.button("Cari Rute Pengiriman", type="primary", width="stretch", key="cari")
    reset.button("Reset Input dan Hasil", on_click=reset_input, width="stretch", key="reset")
    if diklik:
        try:
            lokasi = validasi_lokasi(toko, pelanggan)
            with st.spinner("Mencari rute dan membandingkan hasil..."):
                hasil = cari_rute(lokasi, parameter)
            hasil["signature"] = signature
            st.session_state["hasil"] = hasil
            st.success("Pencarian selesai. Lihat rute dan perbandingan di bawah.")
        except (ValueError, OverflowError) as error:
            st.error(f"Pencarian belum dapat dijalankan: {error}")
    if "hasil" in st.session_state:
        hasil = st.session_state["hasil"]
        tampilkan_hasil(hasil, signature != hasil["signature"])
    else:
        st.caption("Hasil akan muncul setelah Anda menekan Cari Rute Pengiriman.")


if __name__ == "__main__":
    main()
