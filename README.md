# Pengujian Algoritma Task Scheduler pada Server IT

Repository ini berisi implementasi simulasi **Task Scheduling** pada lingkungan Komputasi Awan (Cloud Computing). Proyek ini dikerjakan untuk tugas mata kuliah **Strategi Optimasi Komputasi Awan (SOKA)**.

Program ini mensimulasikan distribusi tugas (tasks) ke beberapa Virtual Machine (VM) menggunakan berbagai algoritma penjadwalan untuk membandingkan performa metrik seperti **Makespan**, **Throughput**, **Imbalance Degree**, dan **Resource Utilization**.

## 👥 Anggota Kelompok

**Kelompok I — Kelas SOKA B**

| No | Nama | NRP |
|----|------|-----|
| 1. | Muhammad Andrean Rizq P | 5027231052 |
| 2. | Fikri Aulia As Sa'adi | 5027231026 |
| 3. | Malvin Putra | ...069 |
| 4. | Fadhil Saifullah | ...069 |
| 5. | Dani Wahyu Anak Ary | ...069 |

*(Catatan: Silakan sesuaikan NRP jika ada kesalahan penulisan)*

---

##  Fitur & Algoritma

Proyek ini mengimplementasikan dan membandingkan 4 algoritma penjadwalan:

1.  **Particle Swarm Optimization (PSO)** 
    *   Algoritma utama yang dioptimalkan. Menggunakan prinsip kecerdasan kawanan (swarm intelligence) untuk mencari solusi global optimum dalam pembagian tugas.
2.  **Stochastic Hill Climbing (SHC)** 
    *   Algoritma pencarian lokal yang secara acak memindahkan tugas ke VM lain untuk mencari solusi yang lebih baik (makespan lebih kecil).
3.  **Round Robin (RR)** 
    *   Algoritma statis yang membagi tugas secara bergiliran (siklis) ke setiap VM tanpa mempedulikan beban kerja saat itu.
4.  **First-Come First-Served (FCFS)** 
    *   Algoritma greedy yang menugaskan tugas yang datang pertama ke VM yang paling cepat tersedia (memiliki estimasi waktu selesai tercepat).

---

##  Dataset

Pengujian dilakukan menggunakan 3 jenis dataset dengan karakteristik beban kerja (CPU Load) yang berbeda:

1.  **`dataset_random_simple.txt`**: Daftar tugas dengan beban komputasi acak sederhana.
2.  **`dataset_random_stratified.txt`**: Daftar tugas dengan beban yang terstratifikasi (berlapis).
3.  **`dataset_low_high.txt`**: Daftar tugas dengan variasi ekstrem (campuran tugas sangat ringan dan sangat berat).

---

##  Instalasi & Persiapan

Sebelum menjalankan program, pastikan Anda telah menyiapkan lingkungan berikut:

### 1. Clone Repository
```bash
git clone https://github.com/Neinstat/SOKA-Task-Scheduling-PSO.git
cd SOKA-Task-Scheduling-PSO
```

### 2. Buat Virtual Environment (Opsional tapi Disarankan)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

### 3. Install Dependencies
Program ini membutuhkan library `httpx`, `pandas`, dan `python-dotenv`.
```bash
pip install -r requirements.txt
```
*(Jika file requirements.txt belum ada, install manual: `pip install httpx pandas python-dotenv`)*

### 4. Konfigurasi File `.env`
Buat file `.env` di root folder dan atur konfigurasi IP Worker VM Anda:

```env
# Konfigurasi VM Worker (Sesuaikan dengan IP Worker Anda)
VM1_IP=10.15.42.77
VM1_CPU=1
VM1_RAM=1

VM2_IP=10.15.42.78
VM2_CPU=2
VM2_RAM=2

VM3_IP=10.15.42.79
VM3_CPU=4
VM3_RAM=4

VM4_IP=10.15.42.80
VM4_CPU=8
VM4_RAM=4

# Port Aplikasi Worker
VM_PORT=5000
```

---

##  Cara Penggunaan

Terdapat file scheduler terpisah untuk setiap algoritma agar memudahkan pengujian.

### 1. Memilih Dataset
Buka file scheduler yang ingin dijalankan (misal `shc_scheduler.py`), lalu ubah bagian `TASK_FILE` sesuai dataset yang ingin diuji:

```python
# Pilih salah satu:
TASK_FILE = "dataset_random_simple.txt"
# TASK_FILE = "dataset_random_stratified.txt"
# TASK_FILE = "dataset_low_high.txt"
```

### 2. Menjalankan Scheduler
Jalankan perintah berikut di terminal:

*   **Untuk PSO:**
    ```bash
    python pso_scheduler.py
    ```
*   **Untuk SHC:**
    ```bash
    python shc_scheduler.py
    ```
*   **Untuk Round Robin:**
    ```bash
    python rr_scheduler.py
    ```
*   **Untuk FCFS:**
    ```bash
    python fcfs_scheduler.py
    ```

---

## Output Hasil

Setelah program selesai berjalan, akan muncul dua file output di folder proyek dengan penamaan otomatis sesuai algoritma dan dataset:

1.  **File CSV (`algo_dataset.csv`)**
    *   Berisi detail eksekusi per tugas: *Task Name, VM Assigned, Start Time, Execution Time (Worker), Finish Time, Wait Time*.
2.  **File Summary (`algo_dataset_summary.txt`)**
    *   Berisi ringkasan metrik performa untuk perbandingan, mencakup:
        *   Makespan
        *   Throughput
        *   Total CPU Time & Wait Time
        *   Imbalance Degree
        *   Resource Utilization

### Contoh Output Summary
```text
--- Hasil Algoritma: SHC ---
Dataset                   : dataset_random_simple.txt
Total Tugas Selesai       : 50
Makespan                  : 65.6361 detik
Throughput                : 0.7618 tugas/detik
Total CPU Time            : 233.6527 detik
Total Wait Time           : 772.9520 detik
Average Exec Time         : 4.6731 detik
Imbalance Degree          : 0.3780
Resource Utilization      : 88.9955%
----------------------------------------
```

---

## Struktur Proyek

*   `pso_scheduler.py` & `pso_algorithm.py` : Implementasi PSO.
*   `shc_scheduler.py` & `shc_algorithm.py` : Implementasi SHC.
*   `rr_scheduler.py` & `rr_algorithm.py` : Implementasi Round Robin.
*   `fcfs_scheduler.py` & `fcfs_algorithm.py` : Implementasi FCFS.
*   `dataset_*.txt` : File dataset tugas.
*   `.env` : Konfigurasi environment (IP VM).

---
