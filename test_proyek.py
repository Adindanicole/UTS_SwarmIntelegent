"""Verifikasi perilaku, bukan arah rute tertentu. Jalankan: python -m unittest -v."""
import contextlib
import csv
import io
import json
import math
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import main as a


class TestAlgoritma(unittest.TestCase):
    def setUp(self):
        self.d = a.buat_matriks_jarak(a.LOKASI_DEMO)

    def test_demo_optimum_dan_reproduksi(self):
        _, optimum, count = a.cari_rute_optimum(self.d)
        self.assertEqual(count, 120)
        x = a.jalankan_aco(self.d, seed=42)
        self.assertEqual(x, a.jalankan_aco(self.d, seed=42))
        self.assertTrue(math.isclose(x[1], optimum, rel_tol=1e-9, abs_tol=1e-9))
        self.assertTrue(math.isclose(a.hitung_total_jarak(a.nearest_neighbor(self.d), self.d), optimum, abs_tol=1e-9))
        self.assertTrue(all(b <= c+1e-9 for c, b in zip(x[2], x[2][1:])))

    def test_dua_opt_valid_tidak_memburuk_dan_lokal(self):
        for seed in range(10):
            d = a.buat_matriks_jarak(a.buat_data(12, seed))
            tengah = list(range(1, 13))
            random.Random(seed).shuffle(tengah)
            awal = [0, *tengah, 0]
            r = a.dua_opt(awal, d)
            a.validasi_rute(r, len(d))
            panjang = a.hitung_total_jarak(r, d)
            self.assertLessEqual(panjang, a.hitung_total_jarak(awal, d)+1e-9)
            for i in range(1, len(r)-2):
                for k in range(i+1, len(r)-1):
                    calon = r[:i]+r[i:k+1][::-1]+r[k+1:]
                    self.assertGreaterEqual(a.hitung_total_jarak(calon, d), panjang-1e-9)

    def test_seluruh_rute_semut_valid(self):
        asli = a._buat_rute
        jumlah = 0

        def periksa(logs, rng):
            nonlocal jumlah
            r = asli(logs, rng)
            a.validasi_rute(r, len(logs))
            jumlah += 1
            return r

        with patch.object(a, "_buat_rute", side_effect=periksa):
            a.jalankan_aco(self.d, jumlah_semut=7, jumlah_iterasi=11)
        self.assertEqual(jumlah, 77)

    def test_deposit_seluruh_semut_simetris_evaporasi(self):
        # Dua rute yang berbeda; log-bobot generasi kedua mengungkap tau.
        routes = [[0, 1, 2, 3, 4, 5, 0], [0, 2, 4, 1, 3, 5, 0]]
        logs_seen = []

        def tetap(logs, rng):
            logs_seen.append(logs)
            return routes[(len(logs_seen)-1) % 2].copy()

        with patch.object(a, "_buat_rute", side_effect=tetap):
            a.jalankan_aco(self.d, jumlah_semut=2, jumlah_iterasi=2, beta=0, rho=.5)
        expected = a.buat_feromon(6, .5)
        for r in routes:
            deposit = 1/a.hitung_total_jarak(r, self.d)
            for i, j in zip(r, r[1:]):
                expected[i][j] += deposit
                expected[j][i] += deposit
        for i in range(6):
            for j in range(6):
                if i != j:
                    self.assertAlmostEqual(math.exp(logs_seen[2][i][j]), expected[i][j])

    def test_nol_dan_parameter_invalid(self):
        d = a.buat_matriks_jarak([("D", 0, 0), ("A", 0, 0), ("B", 0, 0)])
        r, jarak, _ = a.jalankan_aco(d, jumlah_iterasi=3)
        a.validasi_rute(r, 3)
        self.assertEqual(jarak, 0)
        for params in ({"jumlah_semut": 1.2}, {"jumlah_iterasi": 0}, {"rho": 1},
                       {"alpha": math.nan}, {"beta": -1}, {"q": 0}, {"q": math.inf}):
            with self.assertRaises(ValueError):
                a.jalankan_aco(self.d, **params)
        with self.assertRaises(ValueError):
            a.validasi_rute([0, 1, 1, 0], 3)
        with self.assertRaises(ValueError):
            a.nearest_neighbor([[0, 1], [2, 0]])
        with self.assertRaises(ValueError):
            a.cari_rute_optimum(a.buat_matriks_jarak(a.buat_data(10, 1)))

    def test_import_tanpa_eksekusi(self):
        hasil = subprocess.run([sys.executable, "-B", "-c",
                                "import main, sys; assert 'matplotlib.pyplot' not in sys.modules"],
                               capture_output=True, text=True, check=True)
        self.assertEqual(hasil.stdout, "")
        self.assertEqual(hasil.stderr, "")

    def test_data_dan_rancangan_lama_tetap_sama(self):
        output = Path("output")
        instances = json.loads((output/"instances.json").read_text(encoding="utf-8"))
        metadata = json.loads((output/"metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(a.SEED_DATA, metadata["seed_data"])
        self.assertEqual(a.SEED_ACO, metadata["seed_aco"])
        for x in instances:
            self.assertEqual([list(p) for p in a.buat_data(len(x["lokasi"])-1, x["seed_data"])], x["lokasi"])
        self.assertEqual({str(n): a.konfigurasi(n) for n in (5, 10, 20, 50)}, metadata["konfigurasi"])


class TestInputDanProgram(unittest.TestCase):
    def test_parameter_salah_diulang_dan_default(self):
        # Salah tipe, nol, NaN, batas rho, dan seed negatif harus ditolak.
        jawaban = ["abc", "0", "1.2", "", "-1", "", "nan", "-2", "", "inf", "",
                   "0", "1", ".5", "-1", ""]
        output = io.StringIO()
        with patch("builtins.input", side_effect=jawaban), contextlib.redirect_stdout(output):
            parameter = a.baca_parameter()
        self.assertEqual(parameter, dict(a.DEFAULT, seed=42))
        self.assertIn("Input tidak valid", output.getvalue())
        self.assertIn("Rho harus lebih besar", output.getvalue())

    def test_lokasi_salah_diulang(self):
        jawaban = ["0", "1.5", "salah", "1", "", "Depot", "nan", "0", "0", "A", "x", "2,5", "3"]
        with patch("builtins.input", side_effect=jawaban), contextlib.redirect_stdout(io.StringIO()):
            lokasi = a.baca_lokasi()
        self.assertEqual(lokasi, [("Depot", 0., 0.), ("A", 2.5, 3.)])

    def test_manual_parameter_kustom_depot_bebas_jarak_nol_satu_iterasi(self):
        with tempfile.TemporaryDirectory() as tmp:
            jawaban = ["2", "Depot", "3", "-2", "A", "3", "-2", "B", "6", "2",
                       "1", "1", "0", "0", ".1", "7"]
            hasil = subprocess.run([sys.executable, "-B", "-W", "error", "main.py", "manual", "--output", tmp],
                                   input="\n".join(jawaban)+"\n", capture_output=True, text=True, check=True)
            self.assertEqual(hasil.stderr, "")
            with (Path(tmp)/"manual_hasil.csv").open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
            for r in rows:
                self.assertTrue(math.isclose(float(r["jarak_km"]), 10., abs_tol=1e-9))
                a.validasi_rute(json.loads(r["rute"]), 3)
            data = json.loads((Path(tmp)/"manual_input.json").read_text(encoding="utf-8"))
            self.assertEqual(data["parameter_aco"], dict(jumlah_semut=1, jumlah_iterasi=1, alpha=0., beta=0., rho=.1, q=1., seed=7))

    def test_menu_demo_manual_dan_keluar(self):
        with tempfile.TemporaryDirectory() as tmp:
            # Demo, pilihan salah, manual dengan parameter default, lalu keluar.
            jawaban = ["9", "1", "2", "1", "Depot", "0", "0", "A", "2", "3"] + [""]*6 + ["4"]
            hasil = subprocess.run([sys.executable, "-B", "-W", "error", "main.py", "--output", tmp],
                                   input="\n".join(jawaban)+"\n", capture_output=True, text=True, check=True)
            self.assertEqual(hasil.stderr, "")
            self.assertIn("Pilihan tidak valid", hasil.stdout)
            self.assertIn("23.399846", hasil.stdout)
            self.assertIn("Program selesai", hasil.stdout)
            for folder, prefix in [("demo_001", "demo"), ("manual_001", "manual")]:
                with (Path(tmp)/folder/f"{prefix}_hasil.csv").open(encoding="utf-8", newline="") as f:
                    rows = list(csv.DictReader(f))
                self.assertEqual(len(rows), 4)
                for r in rows:
                    a.validasi_rute(json.loads(r["rute"]), 6 if prefix == "demo" else 2)
                self.assertGreater((Path(tmp)/folder/f"{prefix}_rute.png").stat().st_size, 1000)

    def test_cli_cepat_csv_grafik_dan_kecocokan_hasil_lama(self):
        with tempfile.TemporaryDirectory() as tmp:
            hasil = subprocess.run([sys.executable, "-B", "-W", "error", "main.py", "cepat", "--output", tmp],
                                   capture_output=True, text=True, check=True)
            self.assertEqual(hasil.stderr, "")
            self.assertIn("12 run ACO", hasil.stdout)
            with (Path(tmp)/"hasil_mentah.csv").open(encoding="utf-8", newline="") as f:
                baru = list(csv.DictReader(f))
            with Path("output/hasil_mentah.csv").open(encoding="utf-8", newline="") as f:
                lama = {(r["instance_id"], r["metode"], r["konfigurasi"], r["seed_algoritma"]): r for r in csv.DictReader(f)}
            self.assertEqual(len(baru), 25)
            for r in baru:
                dulu = lama[r["instance_id"], r["metode"], r["konfigurasi"], r["seed_algoritma"]]
                self.assertEqual(r["rute"], dulu["rute"])
                self.assertTrue(math.isclose(float(r["jarak_km"]), float(dulu["jarak_km"]), abs_tol=1e-9))
            for nama in ("kualitas_waktu.png", "sensitivitas.png", "anggaran.png"):
                self.assertGreater((Path(tmp)/nama).stat().st_size, 1000)


class TestArtefak(unittest.TestCase):
    def test_hasil_utama_lengkap(self):
        output = Path("output")
        metadata = json.loads((output/"metadata.json").read_text())
        self.assertEqual(metadata["runs_aco"], 720)
        with (output/"hasil_mentah.csv").open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 759)
        self.assertEqual(sum(r["metode"] == "ACO" for r in rows), 720)
        instances = json.loads((output/"instances.json").read_text())
        matrices = {x["instance_id"]: a.buat_matriks_jarak(x["lokasi"]) for x in instances}
        for row in rows:
            d = matrices[row["instance_id"]]
            r = json.loads(row["rute"])
            a.validasi_rute(r, len(d))
            self.assertTrue(math.isclose(float(row["jarak_km"]), a.hitung_total_jarak(r, d), abs_tol=1e-9))
            self.assertGreaterEqual(float(row["waktu_s"]), 0)
            if int(row["pelanggan"]) > 9:
                self.assertEqual(row["optimum_km"], "")
        for png in ("demo_rute", "demo_konvergensi", "ilustrasi_n20_rute", "ilustrasi_n20_konvergensi", "kualitas_waktu", "sensitivitas", "anggaran"):
            self.assertGreater((output/f"{png}.png").stat().st_size, 1000)


class TestWeb(unittest.TestCase):
    """AppTest menjalankan widget Streamlit; tidak memerlukan eksperimen ulang."""

    @classmethod
    def setUpClass(cls):
        # Streamlit 1.57 membuat TemporaryDirectory saat modul pengujian
        # di-import. Tutup sumber daya pengujian itu secara eksplisit.
        from streamlit.testing.v1.app_test import TMP_DIR
        cls.addClassCleanup(TMP_DIR.cleanup)

    def buka(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file("app.py", default_timeout=30).run()

    def test_validasi_input_web(self):
        import app
        toko = dict(Nama="Toko", X=0, Y=0)
        for pelanggan in ([], [dict(Nama="", X=1, Y=2)], [dict(Nama="A", X=None, Y=2)],
                          [dict(Nama="A", X="abc", Y=2)], [dict(Nama="A", X=math.nan, Y=2)],
                          [dict(Nama="A", X=1, Y=math.inf)]):
            with self.assertRaises(ValueError):
                app.validasi_lokasi(toko, pelanggan)
        self.assertEqual(app.validasi_lokasi(toko, [dict(Nama=" A ", X="2,5", Y="-3")]),
                         [("Toko", 0., 0.), ("A", 2.5, -3.)])
        self.assertIn("Tidak dihitung", app.perbaikan(0, 0))
        self.assertIn("Tidak dihitung", app.perbaikan(1, 0))
        self.assertIn("lebih panjang", app.perbaikan(12, 10))
        self.assertIn("lebih pendek", app.perbaikan(8, 10))

    def test_engine_web_memakai_algoritma_lama(self):
        import app
        params = dict(a.DEFAULT, seed=42)
        with patch.object(a, "cari_rute_optimum", side_effect=AssertionError("Brute force tidak boleh dipanggil")), \
                patch.object(a, "jalankan_eksperimen", side_effect=AssertionError("Eksperimen tidak boleh dipanggil")):
            hasil = app.cari_rute(a.LOKASI_DEMO, params)
        self.assertTrue(math.isclose(hasil["metode"]["ACO"]["jarak"], 23.399846363, abs_tol=1e-9))
        for metode in hasil["metode"].values():
            a.validasi_rute(metode["rute"], 6)
            self.assertGreaterEqual(metode["waktu"], 0)
        rute, jarak, history = a.jalankan_aco(a.buat_matriks_jarak(a.LOKASI_DEMO), **params)
        self.assertEqual(rute, hasil["metode"]["ACO"]["rute"])
        self.assertEqual(history, hasil["riwayat"])

    def test_widget_contoh_rerun_perubahan_dan_reset(self):
        from streamlit.elements.widgets.button import ButtonMixin
        unduhan = []
        asli = ButtonMixin._download_button

        def rekam(widget, label, data, *args, **kwargs):
            unduhan.append((label, data))
            return asli(widget, label, data, *args, **kwargs)

        with patch.object(a, "jalankan_aco", wraps=a.jalankan_aco) as panggil, \
                patch.object(ButtonMixin, "_download_button", rekam):
            at = self.buka()
            self.assertEqual(panggil.call_count, 0)
            self.assertEqual(len(at.exception), 0)
            at.button(key="cari").click().run()
            self.assertEqual(len(at.exception), 0)
            self.assertEqual(at.metric[0].value, "23.399846 km")
            self.assertEqual(panggil.call_count, 1)
            waktu_awal = at.session_state["hasil"]["metode"]["ACO"]["waktu"]
            for metode in ("NN", "NN_2opt", "Awal", "ACO"):
                at.selectbox(key="metode_grafik").set_value(metode).run()
                self.assertEqual(len(at.exception), 0)
            self.assertEqual(panggil.call_count, 1)
            self.assertEqual(waktu_awal, at.session_state["hasil"]["metode"]["ACO"]["waktu"])
            self.assertEqual(len(at.get("download_button")), 2)
            self.assertTrue(all(x.proto.url.endswith(".csv") for x in at.get("download_button")))
            # Periksa byte yang benar-benar diberikan ke tombol unduh.
            label, raw = unduhan[-2]
            self.assertEqual(label, "Unduh Ringkasan CSV")
            rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
            self.assertEqual(len(rows), 4)
            self.assertEqual(rows[-1]["seed"], "42")
            self.assertTrue(math.isclose(float(rows[-1]["jarak_km"]), 23.399846363, abs_tol=1e-9))
            urutan = list(csv.DictReader(io.StringIO(unduhan[-1][1].decode("utf-8-sig"))))
            self.assertEqual(len(urutan), 7)
            self.assertEqual(urutan[0]["lokasi"], urutan[-1]["lokasi"])
            self.assertEqual(len(at.get("imgs")), 2)
            at.number_input(key="seed").set_value(43).run()
            self.assertTrue(any("berubah" in x.value for x in at.warning))
            self.assertEqual(panggil.call_count, 1)
            at.button(key="reset").click().run()
            self.assertEqual(at.radio[0].value, "Gunakan Data Contoh")
            self.assertEqual(at.number_input(key="seed").value, 42)
            self.assertNotIn("hasil", at.session_state.filtered_state)
            self.assertEqual(len(at.metric), 0)

    def test_widget_manual_validasi_koordinat_sama_nol(self):
        at = self.buka()
        at.radio[0].set_value("Masukkan Lokasi Sendiri").run()
        at.button(key="cari").click().run()
        self.assertTrue(any("Nama pelanggan" in x.value for x in at.error))
        at.text_input(key="x_toko").set_value("abc").run()
        at.button(key="cari").click().run()
        self.assertTrue(any("X toko" in x.value for x in at.error))
        at.text_input(key="x_toko").set_value("0").run()
        # AppTest belum punya pengendali sel data_editor. Kirim edit tabel
        # melalui state tepat sebelum event tombol, seperti payload editor.
        at.session_state["pelanggan"] = dict(edited_rows={0: dict(Nama="A", X=0., Y=0.)}, added_rows=[], deleted_rows=[])
        at.button(key="cari").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.metric[0].value, "0.000000 km")
        self.assertTrue(any("Tidak dihitung" in x.value for x in at.markdown))
        at.session_state["pelanggan"] = dict(edited_rows={}, added_rows=[], deleted_rows=[0])
        at.button(key="cari").click().run()
        self.assertTrue(any("minimal satu pelanggan" in x.value for x in at.error))
        self.assertTrue(any("berubah" in x.value for x in at.warning))

    def test_widget_tambah_hapus_pelanggan_parameter_kustom(self):
        at = self.buka()
        at.radio[0].set_value("Masukkan Lokasi Sendiri").run()
        at.text_input(key="nama_toko").set_value("Depot Baru").run()
        at.text_input(key="x_toko").set_value("3").run()
        at.text_input(key="y_toko").set_value("-2").run()
        for key, value in (("jumlah_semut", 1), ("jumlah_iterasi", 1), ("alpha", 0.), ("beta", 0.), ("rho", .1), ("seed", 7)):
            at.number_input(key=key).set_value(value).run()
        at.session_state["pelanggan"] = dict(edited_rows={}, deleted_rows=[0], added_rows=[
            dict(Nama="A", X=3., Y=-2.), dict(Nama="B", X=6., Y=2.)])
        at.button(key="cari").click().run()
        self.assertEqual(len(at.exception), 0)
        self.assertEqual(at.metric[0].value, "10.000000 km")
        self.assertEqual(len(at.session_state["hasil"]["lokasi"]), 3)
        self.assertEqual(at.session_state["hasil"]["lokasi"][0], ("Depot Baru", 3., -2.))
        at.number_input(key="rho").set_value(1.).run()
        at.session_state["pelanggan"] = dict(edited_rows={}, deleted_rows=[0], added_rows=[
            dict(Nama="A", X=3., Y=-2.), dict(Nama="B", X=6., Y=2.)])
        at.button(key="cari").click().run()
        self.assertTrue(any("0<rho<1" in x.value for x in at.error))
        at.button(key="reset").click().run()
        at.radio[0].set_value("Masukkan Lokasi Sendiri").run()
        self.assertEqual(at.text_input(key="nama_toko").value, "Toko")
        self.assertEqual(at.text_input(key="x_toko").value, "0")
        self.assertEqual(at.session_state["pelanggan"]["added_rows"], [])

    def test_csv_dan_grafik_web(self):
        import app
        data = [{"kunjungan": 1, "lokasi": "Toko, Utama", "x_km": 0},
                {"kunjungan": 2, "lokasi": "Pelanggan É", "x_km": 2},
                {"kunjungan": 3, "lokasi": "Toko, Utama", "x_km": 0}]
        raw = app.csv_bytes(data)
        self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        self.assertEqual(rows[0]["lokasi"], "Toko, Utama")
        self.assertEqual(rows[1]["lokasi"], "Pelanggan É")
        self.assertEqual(rows[-1]["lokasi"], rows[0]["lokasi"])
        fig = app.grafik_rute(a.LOKASI_DEMO, [0, 1, 4, 3, 5, 2, 0], "Contoh")
        self.assertEqual(fig.axes[0].get_aspect(), 1.)
        self.assertTrue(any("Pelanggan A" in t.get_text() for t in fig.axes[0].texts))
        self.assertEqual(fig.axes[0].get_xlabel(), "X (km)")


if __name__ == "__main__":
    unittest.main()
