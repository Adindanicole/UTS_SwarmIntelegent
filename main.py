"""Optimasi rute satu kurir: menu -> data -> ACO -> pembanding -> hasil.

Urutan belajar: baca menu(), jalankan_demo(), jalankan_aco(), lalu _buat_rute().
Bagian eksperimen dan grafik di bawahnya dipakai untuk bukti evaluasi tugas.
"""
import argparse
import csv
import json
import math
import platform
import random
import statistics as st
from collections import defaultdict
from itertools import permutations
from pathlib import Path
from time import perf_counter


# 1. DATA DAN ALGORITMA

EPS = 1e-12

TOL = 1e-9

LOKASI_DEMO = [("Toko", 0, 0), ("Pelanggan A", 2, 3),
               ("Pelanggan B", 5, 1), ("Pelanggan C", 6, 5),
               ("Pelanggan D", 1, 6), ("Pelanggan E", 8, 3)]

def buat_data(jumlah_pelanggan, seed_data):
    """Depot (0,0); pelanggan uniform pada persegi [0,20] km."""
    if type(jumlah_pelanggan) is not int or jumlah_pelanggan < 1:
        raise ValueError("Jumlah pelanggan harus bilangan bulat positif.")
    rng = random.Random(seed_data)
    return [("Toko", 0, 0)] + [(f"P{i}", rng.uniform(0, 20), rng.uniform(0, 20))
                              for i in range(1, jumlah_pelanggan + 1)]

def buat_matriks_jarak(lokasi):
    """Menghitung jarak Euclidean dari koordinat finite dalam km."""
    if len(lokasi) < 2 or any(not math.isfinite(v) for _, x, y in lokasi for v in (x, y)):
        raise ValueError("Minimal dua lokasi dengan koordinat finite.")
    return [[math.hypot(a[1]-b[1], a[2]-b[2]) for b in lokasi] for a in lokasi]

def validasi_matriks(d):
    """Memastikan matriks persegi, finite, nonnegatif, dan simetris."""
    n = len(d)
    if n < 2 or any(len(row) != n for row in d):
        raise ValueError("Matriks harus persegi, minimal 2 lokasi.")
    for i in range(n):
        for j in range(n):
            if not math.isfinite(d[i][j]) or d[i][j] < 0:
                raise ValueError("Jarak harus finite dan nonnegatif.")
            if not math.isclose(d[i][j], d[j][i], rel_tol=1e-12, abs_tol=EPS):
                raise ValueError("Matriks harus simetris.")
        if d[i][i] != 0:
            raise ValueError("Diagonal matriks harus nol.")

def validasi_rute(rute, jumlah_lokasi):
    """Depot pada kedua ujung; pelanggan tepat satu kali."""
    if (len(rute) != jumlah_lokasi + 1 or rute[0] != 0 or rute[-1] != 0
            or any(type(i) is not int for i in rute)
            or sorted(rute[1:-1]) != list(range(1, jumlah_lokasi))):
        raise ValueError("Rute harus depot -> seluruh pelanggan tepat sekali -> depot.")

def _panjang(rute, d):
    return math.fsum(d[a][b] for a, b in zip(rute, rute[1:]))

def hitung_total_jarak(rute, matriks_jarak):
    """Mengukur panjang rute yang valid dalam kilometer."""
    validasi_rute(rute, len(matriks_jarak))
    return _panjang(rute, matriks_jarak)

def nearest_neighbor(d):
    """Greedy dari depot, tie-break berdasarkan indeks terkecil."""
    validasi_matriks(d)
    sisa, rute = set(range(1, len(d))), [0]
    while sisa:
        pilih = min(sisa, key=lambda j: (d[rute[-1]][j], j))
        rute.append(pilih)
        sisa.remove(pilih)
    return rute + [0]

def dua_opt(rute, d, toleransi=TOL):
    """First improvement: balik segmen pelanggan sampai tidak membaik > tol km."""
    validasi_matriks(d)
    validasi_rute(rute, len(d))
    if not math.isfinite(toleransi) or toleransi <= 0:
        raise ValueError("Toleransi harus finite dan positif.")
    rute, panjang = list(rute), _panjang(rute, d)
    while True:
        membaik = False
        for i in range(1, len(rute)-2):
            for k in range(i+1, len(rute)-1):
                a, b, c, e = rute[i-1], rute[i], rute[k], rute[k+1]
                if d[a][c]+d[b][e]-d[a][b]-d[c][e] < -toleransi:
                    calon = rute[:i]+rute[i:k+1][::-1]+rute[k+1:]
                    baru = _panjang(calon, d)
                    if baru < panjang-toleransi:
                        rute, panjang, membaik = calon, baru, True
                        break
            if membaik:
                break
        if not membaik:
            return rute

def buat_feromon(n, nilai_awal=1.0):
    """Feromon awal seragam; diagonal tidak dipakai."""
    return [[0.0 if i == j else nilai_awal for j in range(n)] for i in range(n)]

def _buat_rute(logs, rng):
    """Normalisasi log-bobot per kandidat mencegah overflow/semua bobot nol."""
    # Mulai dari depot. Daftar sisa selalu berurutan agar seed dapat diulang.
    sisa, rute = list(range(1, len(logs))), [0]
    while sisa:
        row = logs[rute[-1]]
        maksimum = max(row[j] for j in sisa)
        weights = [math.exp(row[j]-maksimum) for j in sisa]
        # Roulette wheel: peluang terpilih = bobot / jumlah seluruh bobot.
        ambang = rng.random()*sum(weights)
        akumulasi, pilih = 0.0, len(sisa)-1
        for indeks, w in enumerate(weights):
            akumulasi += w
            if ambang < akumulasi:
                pilih = indeks
                break
        rute.append(sisa.pop(pilih))
    return rute + [0]

def jalankan_aco(d, jumlah_semut=20, jumlah_iterasi=100, alpha=1.0,
                 beta=2.0, rho=0.5, q=1.0, seed=42):
    """Ant System: seluruh semut deposit, tanpa elitisme atau local search.

    Bobot proporsional tau**alpha * (1/max(d,EPS))**beta.
    EPS hanya untuk heuristik/deposit/feromon; jarak rute tetap asli.
    """
    validasi_matriks(d)
    if any(type(v) is not int or v < 1 for v in (jumlah_semut, jumlah_iterasi)):
        raise ValueError("Jumlah semut dan iterasi harus bilangan bulat positif.")
    if (any(not math.isfinite(v) for v in (alpha, beta, rho, q))
            or alpha < 0 or beta < 0 or not 0 < rho < 1 or q <= 0):
        raise ValueError("Parameter finite: alpha,beta >=0; 0<rho<1; Q>0.")
    rng, n = random.Random(seed), len(d)
    tau = buat_feromon(n)
    heuristik = [[-beta*math.log(max(v, EPS)) for v in row] for row in d]
    terbaik, jarak_terbaik, riwayat = None, math.inf, []
    for _ in range(jumlah_iterasi):
        # Feromon tetap selama seluruh semut membangun rute satu generasi.
        logs = [[alpha*math.log(max(tau[i][j], EPS))+heuristik[i][j]
                 if i != j else -math.inf for j in range(n)] for i in range(n)]
        if any(not math.isfinite(logs[i][j]) for i in range(n) for j in range(n) if i != j):
            raise ValueError("Log-bobot overflow; gunakan parameter moderat.")
        hasil = []
        # Langkah 1: semua semut membuat rute, kemudian ukur jaraknya.
        for _ in range(jumlah_semut):
            rute = _buat_rute(logs, rng)
            panjang = _panjang(rute, d)
            hasil.append((rute, panjang))
            if panjang < jarak_terbaik:
                # Simpan yang terbaik dari seluruh iterasi, bukan hanya saat ini.
                terbaik, jarak_terbaik = rute.copy(), panjang
        # Langkah 2: penguapan; tiap sisi tak berarah diproses sekali.
        for i in range(n):
            for j in range(i+1, n):
                tau[i][j] = tau[j][i] = max(EPS, (1-rho)*tau[i][j])
        # Langkah 3: semua semut deposit Q/L, termasuk sisi kembali ke depot.
        for rute, panjang in hasil:
            deposit = q/max(panjang, EPS)
            for i, j in zip(rute, rute[1:]):
                tau[i][j] += deposit
                tau[j][i] += deposit
        if any(not math.isfinite(v) for row in tau for v in row):
            raise ValueError("Feromon overflow; gunakan Q moderat.")
        riwayat.append(jarak_terbaik)
    validasi_rute(terbaik, n)
    return terbaik, jarak_terbaik, riwayat

def cari_rute_optimum(d):
    """Enumerasi semua n! urutan, hanya untuk maksimal 9 pelanggan."""
    validasi_matriks(d)
    if len(d)-1 > 9:
        raise ValueError("Brute force maksimal 9 pelanggan.")
    terbaik, jarak, jumlah = None, math.inf, 0
    for urutan in permutations(range(1, len(d))):
        rute = [0, *urutan, 0]
        panjang = _panjang(rute, d)
        jumlah += 1
        if panjang < jarak:
            terbaik, jarak = rute, panjang
    return terbaik, jarak, jumlah

# 2. EKSPERIMEN DAN RINGKASAN HASIL

DEFAULT = dict(jumlah_semut=20, jumlah_iterasi=100, alpha=1., beta=2., rho=.5, q=1.)

SEED_DATA = [101, 202, 303]

SEED_ACO = list(range(20))

def konfigurasi(n):
    """OFAT pada 20 pelanggan; konfigurasi awal tidak dijalankan berulang."""
    hasil = {"dasar": DEFAULT.copy()}
    if n == 20:
        for parameter, nilai in [("alpha", [.5, 2]), ("beta", [1, 5]), ("rho", [.1, .9])]:
            for v in nilai:
                hasil[f"{parameter}_{v}"] = dict(DEFAULT, **{parameter: v})
        for m, t in [(10, 200), (40, 50)]:
            hasil[f"anggaran_{m}x{t}"] = dict(DEFAULT, jumlah_semut=m, jumlah_iterasi=t)
    return hasil

def tulis_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def relatif(jarak, baseline):
    """Positif berarti jarak lebih pendek; tak terdefinisi jika baseline nol."""
    return (baseline-jarak)/baseline*100 if baseline else None

def ringkas(rows, output):
    kelompok = defaultdict(list)
    for r in rows:
        kelompok[r["instance_id"], r["metode"], r["konfigurasi"]].append(r)
    summary = []
    for (iid, metode, config), group in kelompok.items():
        jarak = [r["jarak_km"] for r in group]
        r = group[0]
        optimum = r["optimum_km"]
        hits = sum(math.isclose(v, optimum, rel_tol=1e-9, abs_tol=1e-9) for v in jarak) if optimum != "" else ""
        summary.append(dict(instance_id=iid, seed_data=r["seed_data"], pelanggan=r["pelanggan"],
                            metode=metode, konfigurasi=config, runs=len(group),
                            terbaik_km=min(jarak), terburuk_km=max(jarak), rata_km=st.mean(jarak),
                            std_seed_km=st.stdev(jarak) if len(jarak)>1 else 0.,
                            waktu_rata_s=st.mean(x["waktu_s"] for x in group),
                            perbaikan_nn_pct=relatif(st.mean(jarak), r["nn_km"]),
                            perbaikan_2opt_pct=relatif(st.mean(jarak), r["nn_2opt_km"]),
                            optimum_km=optimum, optimum_hits=hits,
                            optimum_freq_pct=hits/len(group)*100 if hits != "" else ""))
    tulis_csv(output/"ringkasan_instance.csv", summary)
    antar = defaultdict(list)
    for r in summary:
        antar[r["pelanggan"], r["metode"], r["konfigurasi"]].append(r)
    agregat = []
    for (n, metode, config), group in antar.items():
        pnn = [r["perbaikan_nn_pct"] for r in group]
        p2 = [r["perbaikan_2opt_pct"] for r in group]
        agregat.append(dict(pelanggan=n, metode=metode, konfigurasi=config, instances=len(group),
                            perbaikan_nn_pct=st.mean(pnn),
                            std_instance_nn_pct=st.stdev(pnn) if len(group)>1 else 0.,
                            perbaikan_2opt_pct=st.mean(p2),
                            std_instance_2opt_pct=st.stdev(p2) if len(group)>1 else 0.,
                            waktu_rata_s=st.mean(r["waktu_rata_s"] for r in group)))
    tulis_csv(output/"ringkasan_ukuran.csv", agregat)
    return summary, agregat

def jalankan_eksperimen(output, cepat=False):
    """Waktu hanya mencakup pencarian; validasi, CSV, data, grafik di luar timer."""
    output.mkdir(parents=True, exist_ok=True)
    rows, instances = [], []
    ukuran = [5, 10, 20, 50]
    seeds_data = SEED_DATA[:1] if cepat else SEED_DATA
    seeds_aco = SEED_ACO[:1] if cepat else SEED_ACO
    total = sum(len(konfigurasi(n))*len(seeds_data)*len(seeds_aco) for n in ukuran)
    selesai = 0
    mulai_total = perf_counter()
    for n in ukuran:
        for sd in seeds_data:
            iid = f"n{n}_d{sd}"
            lokasi = buat_data(n, sd)
            instances.append(dict(instance_id=iid, seed_data=sd, lokasi=lokasi))
            d = buat_matriks_jarak(lokasi)
            optimum, exact_route, exact_time = "", None, None
            if n <= 9:
                start = perf_counter()
                exact_route, optimum, _ = cari_rute_optimum(d)
                exact_time = perf_counter()-start
            baselines = {}
            for metode in ("Awal", "NN", "NN_2opt"):
                start = perf_counter()
                if metode == "Awal":
                    rute = [*range(n+1), 0]
                elif metode == "NN":
                    rute = nearest_neighbor(d)
                else:
                    # Sertakan biaya NN: pembanding ini menjalankan NN + 2-opt.
                    rute = dua_opt(nearest_neighbor(d), d)
                jarak = hitung_total_jarak(rute, d)
                durasi = perf_counter()-start
                baselines[metode] = (rute, jarak, durasi)
            if exact_route is not None:
                baselines["Brute_force"] = (exact_route, optimum, exact_time)

            def record(metode, config, seed, params, rute, jarak, durasi):
                validasi_rute(rute, n+1)
                if not math.isclose(jarak, hitung_total_jarak(rute, d), rel_tol=1e-9, abs_tol=1e-9):
                    raise AssertionError("Jarak tidak sesuai rute")
                row = dict(instance_id=iid, seed_data=sd, pelanggan=n, metode=metode,
                           konfigurasi=config, seed_algoritma=seed, **{k: params.get(k, "") for k in DEFAULT},
                           kandidat=params.get("jumlah_semut", 0)*params.get("jumlah_iterasi", 0),
                           jarak_km=jarak, waktu_s=durasi, optimum_km=optimum,
                           gap_optimum_pct=(jarak/optimum-1)*100 if optimum != "" and optimum else (0 if optimum == 0 else ""),
                           nn_km=baselines["NN"][1], nn_2opt_km=baselines["NN_2opt"][1],
                           rute=json.dumps(rute))
                rows.append(row)

            for metode, (rute, jarak, durasi) in baselines.items():
                record(metode, "deterministik", "", {}, rute, jarak, durasi)
            for config, params in konfigurasi(n).items():
                for seed in seeds_aco:
                    start = perf_counter()
                    rute, jarak, history = jalankan_aco(d, seed=seed, **params)
                    durasi = perf_counter()-start
                    assert all(b <= a+1e-9 for a, b in zip(history, history[1:]))
                    record("ACO", config, seed, params, rute, jarak, durasi)
                    selesai += 1
                    if seed == seeds_aco[-1] or cepat:
                        print(f"[{selesai}/{total}] {iid} {config}; waktu run terakhir {durasi:.3f} s", flush=True)
                    if config == "dasar" and seed == seeds_aco[0]:
                        tulis_csv(output/f"riwayat_{iid}.csv", [dict(iterasi=i, terbaik_km=v) for i, v in enumerate(history, 1)])
                        if n == 20 and sd == seeds_data[0]:
                            routes = {k: v[0] for k, v in baselines.items() if k != "Brute_force"}
                            routes["ACO"] = rute
                            gambar_demo(lokasi, routes, d, history, output, prefix="ilustrasi_n20")
                # Checkpoint per konfigurasi supaya hasil selesai tetap tersedia.
                tulis_csv(output/"hasil_mentah.csv", rows)
    summary, agregat = ringkas(rows, output)
    gambar_ringkasan(summary, agregat, output)
    metadata = dict(python=platform.python_version(), platform=platform.platform(),
                    seed_data=seeds_data, seed_aco=seeds_aco, ukuran=ukuran,
                    konfigurasi={str(n): konfigurasi(n) for n in ukuran}, cepat=cepat,
                    runs_aco=selesai, baris_csv=len(rows), durasi_total_s=perf_counter()-mulai_total)
    (output/"metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    (output/"instances.json").write_text(json.dumps(instances, indent=2), encoding="utf-8")
    print(f"Selesai: {selesai} run ACO, {len(rows)} baris CSV, {metadata['durasi_total_s']:.1f} s", flush=True)

# 3. GRAFIK

def pyplot(show=False):
    import matplotlib
    if not show:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt

def gambar_demo(lokasi, routes, d, history, output, show=False, prefix="demo"):
    """Empat rute pada instance identik dan kurva ilustrasi satu run ACO."""
    plt = pyplot(show)
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), layout="constrained")
    warna = dict(Awal="tab:red", NN="tab:blue", NN_2opt="tab:orange", ACO="tab:green")
    label = dict(Awal="Rute awal", NN="NN", NN_2opt="NN + 2-opt", ACO="ACO - Ant System")
    for ax, (nama, rute) in zip(axes.flat, routes.items()):
        x, y = [lokasi[i][1] for i in rute], [lokasi[i][2] for i in rute]
        ax.plot(x, y, "o-", color=warna[nama], markersize=4, label="Urutan perjalanan")
        ax.scatter(*lokasi[0][1:], marker="s", color="red", s=70, label="Depot", zorder=4)
        for a, b in zip(rute, rute[1:]):
            ax.annotate("", xy=lokasi[b][1:], xytext=lokasi[a][1:],
                        arrowprops=dict(arrowstyle="->", color=warna[nama], alpha=.6))
        for i, (_, xx, yy) in enumerate(lokasi):
            ax.annotate(str(i), (xx, yy), xytext=(4, 4), textcoords="offset points", fontsize=8)
        ax.set(title=f"{label[nama]}: {hitung_total_jarak(rute, d):.3f} km", xlabel="X (km)", ylabel="Y (km)")
        ax.set_aspect("equal", adjustable="box")
        ax.margins(.15)
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle("Ilustrasi satu instance dan satu run ACO (bukan ringkasan eksperimen)")
    fig.savefig(output/f"{prefix}_rute.png", dpi=150)
    fig2, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    ax.plot(range(1, len(history)+1), history, color=warna["ACO"], linewidth=2.5, label="ACO terbaik sepanjang pencarian")
    for nama in ("NN", "NN_2opt"):
        ax.axhline(hitung_total_jarak(routes[nama], d), color=warna[nama],
                   linestyle="--" if nama == "NN" else ":", label=label[nama])
    ax.set(xlabel="Iterasi", ylabel="Jarak (km)", title="Ilustrasi satu run: kurva konvergensi")
    ax.legend()
    ax.set_xlim(1, max(2, len(history)))
    if max(history)-min(history) < 1e-9:
        ax.text(.03, .08, "Kurva datar: nilai terbaik sudah tercapai pada iterasi pertama.\nGaris dapat berimpit dengan baseline.",
                transform=ax.transAxes, fontsize=9)
    ax.grid(alpha=.3)
    fig2.savefig(output/f"{prefix}_konvergensi.png", dpi=150)
    if show:
        plt.show()
    plt.close("all")

def gambar_ringkasan(summary, agregat, output):
    """Rata-rata relatif per instance, kemudian rata-rata antar-instance."""
    plt = pyplot()
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), layout="constrained")
    warna = dict(Awal="tab:red", NN="tab:blue", NN_2opt="tab:orange", ACO="tab:green")
    for metode in ("Awal", "NN", "NN_2opt", "ACO"):
        data = sorted((r for r in agregat if r["metode"] == metode and r["konfigurasi"] in ("dasar", "deterministik")), key=lambda r: r["pelanggan"])
        axes[0].plot([r["pelanggan"] for r in data], [r["perbaikan_nn_pct"] for r in data], "o-", color=warna[metode], label=metode)
        if metode != "Awal":
            axes[1].plot([r["pelanggan"] for r in data], [r["perbaikan_nn_pct"] for r in data], "o-", color=warna[metode], label=metode)
        axes[2].plot([r["pelanggan"] for r in data], [r["waktu_rata_s"] for r in data], "o-", color=warna[metode], label=metode)
    axes[0].set(xlabel="Jumlah pelanggan", ylabel="Perbaikan terhadap NN (%)", title="Kualitas: rata-rata relatif antar-instance")
    axes[1].set(xlabel="Jumlah pelanggan", ylabel="Perbaikan terhadap NN (%)", title="Detail metode pencarian")
    axes[2].set(xlabel="Jumlah pelanggan", ylabel="Waktu pencarian rata-rata (detik)", title="Waktu aktual (skala log)", yscale="log")
    for ax in axes:
        ax.grid(alpha=.3)
        ax.legend()
    fig.savefig(output/"kualitas_waktu.png", dpi=150)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4), layout="constrained")
    for ax, parameter, values in zip(axes, ("alpha", "beta", "rho"), ([.5, 1, 2], [1, 2, 5], [.1, .5, .9])):
        default_value = dict(alpha=1, beta=2, rho=.5)[parameter]
        for sd in sorted({r["seed_data"] for r in summary}):
            points, errors = [], []
            for v in values:
                config = "dasar" if v == default_value else f"{parameter}_{v}"
                r = next(r for r in summary if r["pelanggan"] == 20 and r["seed_data"] == sd and r["konfigurasi"] == config)
                points.append(r["rata_km"])
                errors.append(r["std_seed_km"])
            ax.errorbar(values, points, yerr=errors, marker="o", capsize=3, label=f"Data {sd}")
        ax.set(xlabel=parameter, ylabel="Jarak (km)", title=f"Pengaruh {parameter} (OFAT)")
        ax.grid(alpha=.3)
        ax.legend(fontsize=8)
    fig.suptitle("20 pelanggan: mean dan simpangan baku antar-seed ACO per instance")
    fig.savefig(output/"sensitivitas.png", dpi=150)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    configs = ["anggaran_10x200", "dasar", "anggaran_40x50"]
    records = [next(r for r in agregat if r["pelanggan"] == 20 and r["konfigurasi"] == c) for c in configs]
    labels = ["10 x 200", "20 x 100", "40 x 50"]
    axes[0].bar(labels, [r["perbaikan_2opt_pct"] for r in records])
    axes[0].set(ylabel="Perbaikan terhadap NN + 2-opt (%)", title="Anggaran sama: 2.000 kandidat")
    axes[1].bar(labels, [r["waktu_rata_s"] for r in records])
    axes[1].set(ylabel="Waktu rata-rata (detik)", title="Waktu aktual dapat berbeda")
    fig.savefig(output/"anggaran.png", dpi=150)
    plt.close("all")


# 4. DEMO, INPUT MANUAL, DAN MENU TERMINAL

def baca_angka(label, jenis=float, default=None, minimum=None, maksimum=None):
    """Ulangi pertanyaan sampai angka valid; batas maksimum bersifat eksklusif."""
    while True:
        petunjuk = f" [{default}]" if default is not None else ""
        teks = input(f"{label}{petunjuk}: ").strip()
        if not teks and default is not None:
            return default
        try:
            nilai = jenis(teks.replace(",", "."))
            if not math.isfinite(nilai):
                raise ValueError
            if minimum is not None and nilai < minimum:
                raise ValueError
            if maksimum is not None and nilai >= maksimum:
                raise ValueError
            return nilai
        except (ValueError, OverflowError):
            aturan = "bilangan bulat" if jenis is int else "angka berhingga"
            if minimum is not None:
                aturan += f", minimal {minimum}"
            if maksimum is not None:
                aturan += f", kurang dari {maksimum}"
            print(f"Input tidak valid. Masukkan {aturan}.")


def baca_lokasi():
    """Nama kosong ditolak; koordinat depot bebas, bukan harus (0,0)."""
    jumlah = baca_angka("Jumlah pelanggan", int, minimum=1)
    lokasi = []
    for indeks in range(jumlah + 1):
        label = "depot" if indeks == 0 else f"pelanggan {indeks}"
        nama = ""
        while not nama:
            nama = input(f"Nama {label}: ").strip()
            if not nama:
                print("Nama tidak boleh kosong.")
        x = baca_angka(f"X {nama} (km)")
        y = baca_angka(f"Y {nama} (km)")
        lokasi.append((nama, x, y))
    return lokasi


def baca_parameter():
    """Enter menggunakan nilai awal. Q tetap 1 sesuai rancangan tugas."""
    print("Parameter ACO: tekan Enter untuk memakai default. Q tetap 1.")
    parameter = DEFAULT.copy()
    parameter["jumlah_semut"] = baca_angka("Jumlah semut", int, 20, minimum=1)
    parameter["jumlah_iterasi"] = baca_angka("Jumlah iterasi", int, 100, minimum=1)
    parameter["alpha"] = baca_angka("Alpha", float, 1.0, minimum=0)
    parameter["beta"] = baca_angka("Beta", float, 2.0, minimum=0)
    # Untuk rho, nol juga dilarang (berbeda dari alpha/beta).
    while True:
        parameter["rho"] = baca_angka("Rho (0 < rho < 1)", float, .5, minimum=0, maksimum=1)
        if parameter["rho"] > 0:
            break
        print("Rho harus lebih besar dari 0 dan kurang dari 1.")
    parameter["seed"] = baca_angka("Seed ACO", int, 42, minimum=0)
    return parameter


def folder_baru(induk, nama):
    """Pisahkan hasil baru dari bukti eksperimen lama, tanpa menimpa berkas."""
    induk.mkdir(parents=True, exist_ok=True)
    nomor = 1
    while True:
        folder = induk / f"{nama}_{nomor:03d}"
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            nomor += 1


def jalankan_demo(lokasi, output, parameter=None, show=False, prefix="demo"):
    """Bandingkan empat metode pada data yang sama, lalu simpan satu run."""
    output.mkdir(parents=True, exist_ok=True)
    if parameter is None:
        parameter = dict(DEFAULT, seed=42)
    jarak = buat_matriks_jarak(lokasi)
    validasi_matriks(jarak)
    print("\nDATA (koordinat simulasi dalam km)")
    for i, (nama, x, y) in enumerate(lokasi):
        print(f"{i}: {nama} ({x:g}, {y:g})")
    if len(lokasi) <= 10:
        print("\nMATRIKS JARAK (km; nomor kolom sesuai indeks lokasi)")
        print("     " + " ".join(f"{i:7}" for i in range(len(lokasi))))
        for i, baris in enumerate(jarak):
            print(f"{i:3}: " + " ".join(f"{v:7.2f}" for v in baris))
    hasil = []
    routes = {}
    for metode in ("Awal", "NN", "NN_2opt", "ACO"):
        mulai = perf_counter()
        if metode == "Awal":
            rute = [*range(len(lokasi)), 0]
        elif metode == "NN":
            rute = nearest_neighbor(jarak)
        elif metode == "NN_2opt":
            rute = dua_opt(nearest_neighbor(jarak), jarak)
        else:
            rute, _, riwayat = jalankan_aco(jarak, **parameter)
        panjang = hitung_total_jarak(rute, jarak)
        waktu = perf_counter() - mulai
        routes[metode] = rute
        hasil.append(dict(metode=metode, jarak_km=panjang, waktu_s=waktu,
                          rute=json.dumps(rute, ensure_ascii=False)))
        print(f"\n{metode}: {panjang:.6f} km; waktu komputasi {waktu:.6f} detik")
        print(" -> ".join(lokasi[i][0] for i in rute))
    optimum = None
    if len(lokasi) - 1 <= 9:
        _, optimum, jumlah = cari_rute_optimum(jarak)
        print(f"\nOptimum terbukti: {optimum:.6f} km ({jumlah} urutan diperiksa).")
    else:
        print("\nOptimum tidak diketahui: brute force dibatasi maksimal 9 pelanggan.")
    for row in hasil:
        row["optimum_km"] = optimum if optimum is not None else ""
        row["gap_optimum_pct"] = -relatif(row["jarak_km"], optimum) if optimum else (0 if optimum == 0 else "")
    print(f"ACO: terbaik pada iterasi pertama {riwayat[0]:.6f} km; akhir {riwayat[-1]:.6f} km.")
    print("Waktu komputasi adalah waktu komputer mencari rute, bukan waktu pengiriman.")
    tulis_csv(output/f"{prefix}_hasil.csv", hasil)
    tulis_csv(output/f"{prefix}_riwayat.csv", [dict(iterasi=i, terbaik_km=v) for i, v in enumerate(riwayat, 1)])
    (output/f"{prefix}_input.json").write_text(
        json.dumps(dict(lokasi=lokasi, parameter_aco=parameter), indent=2, ensure_ascii=False), encoding="utf-8")
    gambar_demo(lokasi, routes, jarak, riwayat, output, show, prefix)
    print(f"CSV, input, dan grafik disimpan di: {output.resolve()}")
    return hasil


def menu(output, show=False):
    """Menu berulang sampai keluar; kesalahan input tidak menutup program."""
    while True:
        print("\nOPTIMASI RUTE SATU KURIR - ANT SYSTEM")
        print("1. Demo data awal\n2. Masukkan koordinat sendiri\n3. Jalankan eksperimen\n4. Keluar")
        pilihan = input("Pilihan: ").strip()
        try:
            if pilihan == "1":
                jalankan_demo(LOKASI_DEMO, folder_baru(output, "demo"), show=show)
            elif pilihan == "2":
                lokasi = baca_lokasi()
                parameter = baca_parameter()
                jalankan_demo(lokasi, folder_baru(output, "manual"), parameter, show, "manual")
            elif pilihan == "3":
                print("Rancangan tetap: 720 run ACO; parameter eksperimen tidak mengikuti input manual.")
                jalankan_eksperimen(folder_baru(output, "eksperimen"))
            elif pilihan == "4":
                print("Program selesai.")
                return
            else:
                print("Pilihan tidak valid. Masukkan 1, 2, 3, atau 4.")
        except ValueError as error:
            print(f"Data/parameter tidak dapat diproses: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["demo", "manual", "eksperimen", "cepat"], nargs="?")
    parser.add_argument("--output", type=Path, help="Folder hasil baru; default subfolder bernomor di output/")
    parser.add_argument("--show", action="store_true", help="Buka grafik demo/manual sesudah menyimpan")
    args = parser.parse_args()
    try:
        if args.mode is None:
            menu(args.output or Path("output"), args.show)
            return
        output = args.output or folder_baru(Path("output"), args.mode)
        if args.mode == "demo":
            jalankan_demo(LOKASI_DEMO, output, show=args.show)
        elif args.mode == "manual":
            lokasi = baca_lokasi()
            jalankan_demo(lokasi, output, baca_parameter(), args.show, "manual")
        else:
            if (output/"hasil_mentah.csv").exists():
                parser.error("Folder sudah berisi hasil eksperimen. Pilih --output yang baru agar hasil lama terjaga.")
            jalankan_eksperimen(output, cepat=args.mode == "cepat")
    except (EOFError, KeyboardInterrupt):
        print("\nInput dihentikan; program selesai.")
    except ValueError as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
