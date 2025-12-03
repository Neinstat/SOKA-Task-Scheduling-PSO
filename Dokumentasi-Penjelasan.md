## Cara menjelankan Program
1. Cek ketersediaan server VM apakah bisa digunakan
 `ping -c 3 10.15.42.77`
2. Masuk ke direktori program `cd SOKA-Task-Scheduling-Server-Test`
3. Masuk ke Virtual Environment/venv `source venv/bin/activate`


## Tujuan Program

Program ini dibuat untuk mensimulasikan penjadwalan tugas (task scheduling) di lingkungan cloud computing, menggunakan algoritma `optimasi Particle Swarm Optimization (PSO).`
*Tujuannya:*
1. menentukan penempatan task → VM yang paling efisien,
2. meminimalkan makespan (total waktu eksekusi paling lama di antara VM),
3. lalu benar-benar menjalankan tugas‐tugas itu pada VM worker menggunakan HTTP secara paralel.

## Arsitektur Sistem

1.  Scheduler (pso_scheduler.py)
- membaca daftar VM dari file `.env`,
- membaca dataset task dari `dataset.txt`,
- menjalankan algoritma PSO untuk menentukan VM terbaik untuk setiap task,
- mengirim task ke VM via HTTP (/task/<index>),
- menerima waktu eksekusi dari worker,
- menyimpan hasil ke CSV dan membuat ringkasan metrik.

2. Algoritma PSO (pso_algorithm.py)
- melakukan proses optimasi berdasarkan makespan,
- menghasilkan kombinasi penjadwalan terbaik.

## Hasil & Perbandingan algoritma
- SHC menggunakan hill climbing yang hanya memindahkan satu task ke satu VM dalam setiap iterasi dan menerima perubahan hanya jika lebih baik. Ini membuat algoritma cepat tetapi mudah stuck di local optimum.

- Sementara itu, PSO menggantinya dengan pendekatan swarm intelligence di mana banyak solusi bekerja bersama. Setiap particle memperbarui seluruh assignment task berdasarkan tiga hal: kondisi sekarang, solusi terbaik yang pernah ditemukan (pBest), dan solusi terbaik global (gBest). Mekanisme ini membuat PSO mampu menjelajahi ruang solusi lebih luas, tidak mudah buntu, dan menghasilkan makespan lebih optimal serta distribusi beban VM lebih seimbang dibanding SHC.

## Kesimpulan
Kami memilih PSO karena algoritma ini sangat efektif untuk masalah optimasi seperti task scheduling. PSO bekerja dengan pendekatan populasi (swarm), sehingga eksplorasi solusinya lebih luas, cepat menemukan pola, dan tidak mudah terjebak di local optimum seperti algoritma heuristik biasa. Selain itu, PSO fleksibel, mudah diimplementasikan, dan dapat memberikan penjadwalan yang lebih seimbang karena tiap partikel terus memperbaiki solusi berdasarkan pengalaman dirinya dan swarm.