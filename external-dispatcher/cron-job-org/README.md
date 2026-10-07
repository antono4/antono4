# Opsi B — cron-job.org (tanpa kode)

Panduan lengkap memakai **cron-job.org** sebagai scheduler pihak ke-3 untuk memicu
routine antono4 setiap 10 menit lewat GitHub `workflow_dispatch`.

Kenapa: GitHub membatasi `schedule:` internal, jadi cron `*/5`/`*/10` di repo nyatanya
hanya jalan tiap 3–7 jam. cron-job.org memanggil API GitHub dari luar, jadi jadwalnya
benar-benar 10 menit.

Total waktu: ~10 menit. Gratis.

---

## Prasyarat

- Akun **cron-job.org** (gratis) — daftar di <https://cron-job.org/en/signup>.
- **Personal Access Token (PAT)** GitHub (lihat Langkah 1).

---

## Langkah 1 — Buat PAT GitHub

1. Buka <https://github.com/settings/personal-access-tokens/new> (fine-grained).
2. **Token name**: `cron-job-org-dispatcher`.
3. **Expiration**: pilih sesuai selera (mis. 1 tahun).
4. **Repository access** → *Only select repositories* → pilih **antono4/antono4**.
5. **Permissions** → *Repository permissions*:
   - **Actions**: **Read and write** ← wajib, untuk dispatch workflow.
   - **Contents**: **Read** ← untuk membaca metadata.
6. Klik **Generate token**, lalu **copy** nilainya (`github_pat_...`).

> Alternatif classic PAT: <https://github.com/settings/tokens/new> dengan scope
> `repo` dan `workflow`.

Simpan token ini — akan dipakai di Langkah 3. Jangan commit ke repo.

---

## Langkah 2 — Ambil API key cron-job.org

1. Login ke <https://console.cron-job.org>.
2. Buka **Settings** → bagian **API key** → **Generate**/copy.
3. Simpan nilainya.

> Kalau tidak mau pakai API, kamu bisa membuat job lewat UI (Langkah 3B) dan API key
> tidak diperlukan.

---

## Langkah 3A — Otomatis (1 perintah, disarankan)

Script `create-cron-jobs.sh` membuat 5 job sekaligus, dengan offset menit yang rapi
sehingga job tidak saling bentrok di `main`. Script juga idempoten: dijalankan ulang
akan **meng-update** job yang sudah ada, bukan menduplikasi.

```bash
cd external-dispatcher/cron-job-org
chmod +x create-cron-jobs.sh

# Lihat rencananya dulu tanpa membuat apa pun:
CRONJOB_API_KEY=xxx GITHUB_TOKEN=ghp_xxx DRY_RUN=1 ./create-cron-jobs.sh

# Buat sungguhan:
CRONJOB_API_KEY=xxx GITHUB_TOKEN=ghp_xxx ./create-cron-jobs.sh
```

Cek hasilnya di <https://console.cron-job.org/jobs> — harus ada 5 job bernama
`antono4-activity-graph`, `antono4-generate-assets`, `antono4-profile-3d-contrib`,
`antono4-profile-stats`, `antono4-autocommit`.

---

## Langkah 3B — Manual lewat UI

Buat **5 job** (satu per routine). Untuk setiap job, klik **Create cronjob** dan isi:

**Common**

| Field | Nilai |
| --- | --- |
| Title | `antono4-<routine>` |
| URL | `https://api.github.com/repos/antono4/antono4/actions/workflows/<routine>.yml/dispatches` |
| Schedule | **Every 10 minutes**, atur menit sesuai tabel di bawah |
| Request method | **POST** |

**Headers** (tab *Advanced* → *Headers*)

| Name | Value |
| --- | --- |
| `Authorization` | `Bearer <PAT_dari_Langkah_1>` |
| `Accept` | `application/vnd.github+json` |
| `Content-Type` | `application/json` |

**Request body** (tab *Advanced* → *Request body*)

```json
{"ref":"main"}
```

**Tabel routine + menit eksekusi**

| Routine | URL | Menit (UTC) |
| --- | --- | --- |
| activity-graph | `.../activity-graph.yml/dispatches` | 2, 12, 22, 32, 42, 52 |
| generate-assets | `.../generate-assets.yml/dispatches` | 4, 14, 24, 34, 44, 54 |
| profile-3d-contrib | `.../profile-3d-contrib.yml/dispatches` | 6, 16, 26, 36, 46, 56 |
| profile-stats | `.../profile-stats.yml/dispatches` | 8, 18, 28, 38, 48, 58 |
| autocommit | `.../autocommit.yml/dispatches` | 0, 10, 20, 30, 40, 50 |

> Di UI, pilih preset *Every 10 minutes* lalu centang menit yang sesuai, atau pilih
> *Custom* dan isi menit-menit di atas. Zona waktu: **UTC**.

---

## Verifikasi

1. Di console cron-job.org, klik salah satu job → **Test run**. Status yang benar:
   **HTTP 204** (no content = dispatch sukses).
2. Cek GitHub Actions:
   <https://github.com/antono4/antono4/actions> — akan muncul run `workflow_dispatch`
   untuk workflow tersebut.
3. Atau lewat API:
   ```bash
   curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
     "https://api.github.com/repos/antono4/antono4/actions/workflows/activity-graph.yml/runs?per_page=1" \
     | python3 -c "import sys,json;r=json.load(sys.stdin)['workflow_runs'][0];print(r['event'],r['status'],r['conclusion'])"
   ```

---

## Troubleshooting

| Gejala | Penyebab & solusi |
| --- | --- |
| HTTP **401** | PAT salah/kadaluarsa. Perbarui header `Authorization` di job. |
| HTTP **403** | PAT kurang scope. Pastikan **Actions: Read and write** (fine-grained) atau `repo`+`workflow` (classic). |
| HTTP **404** | Nama file workflow salah, atau PAT tidak punya akses ke repo. Cek URL dan repository access. |
| HTTP **422** | Ref salah (harus `main`) atau workflow tidak punya trigger `workflow_dispatch:`. |
| Job tidak jalan | Pastikan job **enabled** dan jadwalnya benar (UTC). Cek riwayat eksekusi di console. |

> Catatan: cron-job.org mengabaikan header `User-Agent` dan `Connection`. Header lain
> (termasuk `Authorization`) didukung.

---

## Catatan biaya/kuota

- cron-job.org gratis, tiap job boleh jalan hingga 60x/jam. Jadwal kita 6x/jam per job,
  jadi sangat aman.
- Setelah dispatcher eksternal aktif, `routine-scheduler.yml` di repo tetap jadi
  lapisan kedua (me-re-dispatch routine yang benar-benar sepi).
