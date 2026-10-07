# External dispatcher (pihak ke-3) untuk routine antono4

GitHub membatasi (`throttle`) `schedule:` untuk cron berfrekuensi tinggi. Di repo ini
cron `*/5`/`*/10` secara nyata hanya jalan tiap **3–7 jam**, bukan tiap 5–10 menit. Jadi
jadwal internal saja tidak cukup.

Folder ini berisi scheduler **pihak ke-3** yang memanggil GitHub API `workflow_dispatch`
setiap 10 menit, terlepas dari throttle GitHub. Ada tiga opsi — pilih salah satu.

| Opsi | Kode | Biaya | Presisi | Setup |
| --- | --- | --- | --- | --- |
| A. Cloudflare Worker + Cron Trigger | ada (di sini) | gratis | 1 menit | ~5 menit, butuh akun Cloudflare |
| B. cron-job.org | tidak perlu kode | gratis | 1 menit | ~10 menit, cukup klik di web |
| C. VPS/PC sendiri + cron | `dispatch.sh` | gratis (server sendiri) | 10 menit | butuh mesin yang selalu hidup |

Semuanya memanggil endpoint yang sama:

```
POST https://api.github.com/repos/antono4/antono4/actions/workflows/<routine>.yml/dispatches
Body: {"ref":"main"}
```

## Token yang dibutuhkan

Buat **Personal Access Token (PAT)** — jangan pakai `GITHUB_TOKEN` bawaan Actions, karena
token itu tidak bisa memicu workflow dari luar.

- Fine-grained PAT, batasi ke repo `antono4/antono4`:
  - **Actions: Read and write** (wajib, untuk dispatch)
  - **Contents: Read** (untuk membaca metadata)
- Atau classic PAT dengan scope `repo` + `workflow`.

Simpan token ini **hanya** sebagai secret di pihak ke-3. Jangan pernah commit ke repo.

---

## Opsi A — Cloudflare Worker (rekomendasi)

Worker punya Cron Trigger `* * * * *` (tiap menit). Karena setiap routine punya offset
menit sendiri (2, 4, 6, 8, 10), satu tick hanya men-dispatch satu routine, sehingga job
tidak saling bentrok di branch yang sama.

### Langkah

```bash
cd external-dispatcher/cloudflare
npm install -g wrangler          # sekali saja
wrangler login                   # buka browser, login Cloudflare

wrangler secret put GITHUB_TOKEN # tempel PAT dari langkah di atas
wrangler secret put DISPATCH_TOKEN  # opsional, kunci endpoint fetch

wrangler deploy
```

Setelah deploy, uji paksa satu kali (mengabaikan jadwal):

```bash
curl "https://antono4-routine-dispatcher.<subdomain>.workers.dev/?force=1&token=<DISPATCH_TOKEN>"
```

Respons berisi `results` dengan `status: 204` untuk tiap routine yang berhasil
di-dispatch.

### Konfigurasi

Semua pengaturan ada di `wrangler.toml` (`OWNER`, `REPO`, `REF`, `ROUTINES`,
`MINUTE_OFFSETS`). Ubah `MINUTE_OFFSETS` bila ingin offset berbeda. Endpoint `fetch`
juga bisa dipakai sebagai health check (`GET /` mengembalikan status tanpa dispatch).

### Test lokal

```bash
npm test
```

---

## Opsi B — cron-job.org (tanpa kode)

Buat **5 cron job** (satu per routine), semuanya method **POST** ke URL
`https://api.github.com/repos/antono4/antono4/actions/workflows/<routine>.yml/dispatches`
dengan:

- Header `Authorization: Bearer <PAT>`
- Header `Accept: application/vnd.github+json`
- Body `{"ref":"main"}`
- Jadwal: setiap 10 menit pada menit offset masing-masing.

| Routine | Menit eksekusi |
| --- | --- |
| `activity-graph.yml` | 2, 12, 22, 32, 42, 52 |
| `generate-assets.yml` | 4, 14, 24, 34, 44, 54 |
| `profile-3d-contrib.yml` | 6, 16, 26, 36, 46, 56 |
| `profile-stats.yml` | 8, 18, 28, 38, 48, 58 |
| `autocommit.yml` | 10, 20, 30, 40, 50, 0 |

Di UI cron-job.org, pilih "Every 10 minutes" lalu atur menitnya secara manual, atau
memakai REST API:

```bash
curl -X PUT https://api.cron-job.org/jobs \
  -H "Authorization: Bearer <API_KEY_cron-job.org>" \
  -H 'Content-Type: application/json' \
  -d '{
    "job": {
      "url": "https://api.github.com/repos/antono4/antono4/actions/workflows/activity-graph.yml/dispatches",
      "requestMethod": 1,
      "requestHeaders": [
        {"name": "Authorization", "value": "Bearer <PAT>"},
        {"name": "Accept", "value": "application/vnd.github+json"}
      ],
      "requestBody": "{\"ref\":\"main\"}",
      "schedule": {"timezone": "UTC", "minutes": [2,12,22,32,42,52], "hours": [-1], "mdays": [-1], "months": [-1], "wdays": [-1]}
    }
  }'
```

> Catatan: cron-job.org mendukung header kustom dan method POST dengan body. Header
> `User-Agent` dan `Connection` diabaikan oleh layanan ini.

---

## Opsi C — VPS/PC sendiri + cron

Untuk mesin yang selalu hidup (VPS, Raspberry Pi, NAS). Pakai `dispatch.sh`:

```bash
export GITHUB_TOKEN=ghp_xxx
chmod +x external-dispatcher/dispatch.sh

# crontab -e — offset per routine agar tidak bentrok
2-59/10 * * * *  GITHUB_TOKEN=ghp_xxx /path/external-dispatcher/dispatch.sh activity-graph.yml
4-59/10 * * * *  GITHUB_TOKEN=ghp_xxx /path/external-dispatcher/dispatch.sh generate-assets.yml
6-59/10 * * * *  GITHUB_TOKEN=ghp_xxx /path/external-dispatcher/dispatch.sh profile-3d-contrib.yml
8-59/10 * * * *  GITHUB_TOKEN=ghp_xxx /path/external-dispatcher/dispatch.sh profile-stats.yml
10-59/10 * * * * GITHUB_TOKEN=ghp_xxx /path/external-dispatcher/dispatch.sh autocommit.yml
```

---

## Setelah scheduler aktif

`routine-scheduler.yml` di repo tetap berguna sebagai lapisan kedua: ia me-re-dispatch
routine yang benar-benar sepi. Dengan dispatcher eksternal, routine akan berjalan
konsisten tiap 10 menit, dan jadwal internal GitHub menjadi cadangan saja.

Bila ingin menghemat kuota Actions, jadwal internal bisa dikurangi — hapus blok
`schedule:` di tiap routine dan biarkan dispatcher eksternal yang memicu lewat
`workflow_dispatch`.
