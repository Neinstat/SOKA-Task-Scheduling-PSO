import httpx
import asyncio
import time
import pandas as pd
import os
from dotenv import load_dotenv
from collections import namedtuple

# --- MODIFIKASI 1: impor algoritma ---
# Stochastic Hill Climbing sebelumnya dipakai
# Sekarang diganti menggunakan PSO (Particle Swarm Optimization)
from pso_algorithm import particle_swarm_optimization
# ---------------------------------------------

# --- Konfigurasi ---
load_dotenv()

# --- MODIFIKASI 2: nama file output ---
# File hasil simulasi nanti disimpan ke CSV dengan nama ini
RESULTS_FILE = "pso_result.csv"
# -------------------------------------------

# File dataset berisi daftar tugas
TASK_FILE = "dataset.txt"

# Jumlah iterasi PSO (disamakan dengan SHC agar konsisten)
SHC_ITERATIONS = 1000

# Timeout HTTP lebih panjang karena beban komputasi tiap task besar
HTTP_TIMEOUT = 120.0

# --- Tipe Data (Harus sama dengan di file algoritma) ---
# Struktur VM: nama, IP, CPU core, RAM
VM = namedtuple('VM', ['name', 'ip', 'cpu_cores', 'ram_gb'])

# Struktur Task: id internal, nama, index, dan CPU load
Task = namedtuple('Task', ['id', 'name', 'index', 'cpu_load'])


# ============================================================
# Fungsi untuk memuat konfigurasi VM dari file .env
# ============================================================
def load_vms():
    """Memuat konfigurasi VM dari .env file."""
    vms = []
    i = 1

    # Loop untuk membaca VM1, VM2, VM3, dst dari .env
    while True:
        vm_name = f"VM{i}"
        ip = os.getenv(f"{vm_name}_IP")
        cpu = os.getenv(f"{vm_name}_CPU")
        ram = os.getenv(f"{vm_name}_RAM")
        
        # Jika IP tidak ditemukan, berarti tidak ada VM lagi
        if not ip:
            break
            
        try:
            vms.append(VM(
                name=vm_name.lower(),
                ip=ip,
                cpu_cores=int(cpu),
                ram_gb=int(ram)
            ))
        except (TypeError, ValueError) as e:
            # Jika CPU/RAM tidak valid
            print(f"Error memuat {vm_name}: CPU/RAM tidak valid. IP={ip}, CPU={cpu}, RAM={ram}. Error: {e}")
            
        i += 1
        
    # Jika tidak ada VM sama sekali, hentikan program
    if not vms:
        print("Error: Tidak ada VM yang dimuat. Pastikan file .env Anda (VM1_IP, VM1_CPU, ... ) sudah benar.")
        exit(1)
        
    print(f"Berhasil memuat {len(vms)} VMs:")
    for vm in vms:
        print(f"  - {vm.name}: IP={vm.ip}, CPU={vm.cpu_cores}, RAM={vm.ram_gb}")

    return vms



# ============================================================
# Fungsi untuk memuat task dari file dataset.txt
# Bisa membaca format angka saja atau 'task-angka'
# ============================================================
def load_tasks(task_file: str):
    """
    Memuat daftar tugas dari file teks.
    Versi ini dapat menangani format 'task-NUMBER' dan 'NUMBER'.
    """
    tasks = []
    print(f"Membaca tugas dari {task_file}...")
    try:
        with open(task_file, 'r') as f:
            lines = f.readlines()
            
        task_id_counter = 0

        # Iterasi baris per baris
        for i, line_raw in enumerate(lines):
            line_number = i + 1
            line = line_raw.strip()
            
            if not line: 
                continue  # Skip baris kosong
            
            try:
                task_name = None
                task_index = None

                if line.isdigit():
                    # Format angka murni
                    task_index = int(line)
                    task_name = f"task-{task_index}"
                
                elif '-' in line:
                    # Format 'task-N'
                    parts = line.split('-')
                    if len(parts) >= 2 and parts[1].isdigit():
                        task_index = int(parts[1])
                        task_name = line
                    else:
                        raise ValueError("Format 'task-' tidak valid.")
                else:
                    raise ValueError("Format tidak dikenali.")

                # CPU load dihitung berdasarkan index
                task_cpu_load = (task_index * task_index * 10000)

                # Masukkan task ke list
                tasks.append(Task(
                    id=task_id_counter,
                    name=task_name,
                    index=task_index,
                    cpu_load=task_cpu_load
                ))

                task_id_counter += 1
                
            except Exception as e:
                # Jika format baris invalid
                print(f"  [PERINGATAN] Baris {line_number} diabaikan: Format tidak valid ({e}).")
                print(f"  --> Isi Baris: '{line}'")
        
        # Ringkasan
        if task_id_counter == 0:
            print(f"Berhasil membaca file, namun 0 tugas yang valid dimuat.")
        else:
            print(f"Berhasil memuat {len(tasks)} tugas dari {task_file}")
            
        return tasks
        
    except FileNotFoundError:
        print(f"Error: File dataset '{task_file}' tidak ditemukan.")
        exit(1)
    except Exception as e:
        print(f"Error saat membaca file tugas: {e}")
        exit(1)



# ============================================================
# Fungsi mengirim task ke worker VM via HTTP
# ============================================================
async def execute_task(client: httpx.AsyncClient, task: Task, vm: VM, vm_port: str):
    """Mengirim satu tugas ke VM worker dan mengembalikan hasilnya."""
    
    url = f"http://{vm.ip}:{vm_port}/task/{task.index}"
    task_id = task.id
    task_name = task.name
    vm_name = vm.name
    
    print(f"Mengeksekusi {task_name} (idx: {task_id}) di {vm_name} (IP: {vm.ip})...")
    
    start_time = time.time()

    try:
        # Kirim request GET ke VM worker
        response = await client.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()  # Raise error jika status 4xx/5xx
        
        exec_time = time.time() - start_time
        data = response.json()  # Response dari VM worker
        
        return {
            "task_id": task_id,
            "task_name": task_name,
            "vm_name": vm_name,
            "vm_ip": vm.ip,
            "status": "success",
            "execution_time": exec_time,  
            "worker_time": float(data.get('execution_time', '0.0s').replace('s','')),
            "message": data.get('message', '')
        }
        
    except httpx.ReadTimeout:
        # Jika worker memakan waktu terlalu lama
        exec_time = time.time() - start_time
        print(f"Error TIMEOUT pada {task_name} di {vm_name}")
        return {
            "task_id": task_id, "task_name": task_name, "vm_name": vm_name, "vm_ip": vm.ip,
            "status": "timeout", "execution_time": exec_time, "worker_time": None,
            "message": f"ReadTimeout: Tugas berjalan lebih dari {HTTP_TIMEOUT} detik."
        }

    except httpx.ConnectError as e:
        # Jika VM tidak bisa dihubungi
        exec_time = time.time() - start_time
        print(f"Error KONEKSI pada {task_name} di {vm_name}: {e}")
        return {
            "task_id": task_id, "task_name": task_name, "vm_name": vm_name, "vm_ip": vm.ip,
            "status": "connect_error", "execution_time": exec_time, "worker_time": None,
            "message": str(e)
        }

    except Exception as e:
        # Error lain
        exec_time = time.time() - start_time
        print(f"Error LAINNYA pada {task_name} di {vm_name}: {e}")
        return {
            "task_id": task_id, "task_name": task_name, "vm_name": vm_name, "vm_ip": vm.ip,
            "status": "error", "execution_time": exec_time, "worker_time": None,
            "message": str(e)
        }



# ============================================================
# Fungsi utama scheduler
# ============================================================
async def main():
    """Fungsi utama untuk menjalankan scheduler."""

    # Load VM dari .env
    vms = load_vms()

    # Load daftar task dari file
    tasks = load_tasks(TASK_FILE)

    # Port worker
    vm_port = os.getenv("VM_PORT", "5000")
    
    if not tasks:
        print("Tidak ada tugas untuk dijalankan.")
        return

    # ========================================================
    # Jalankan algoritma PSO untuk mencari penjadwalan terbaik
    # ========================================================
    print("\n--- Menjalankan Algoritma Penjadwalan PSO ---")
    start_algo_time = time.time()
    
    best_assignment = particle_swarm_optimization(
        tasks, 
        vms, 
        max_iterations=SHC_ITERATIONS,
        num_particles=30  # Jumlah particle dalam PSO
    )
    
    algo_time = time.time() - start_algo_time
    print(f"Algoritma PSO selesai dalam {algo_time:.4f} detik.")
    
    # ========================================================
    # Tampilkan hasil assignment terbaik dari PSO
    # ========================================================
    print("\nPenugasan Tugas Terbaik Ditemukan:")
    vm_map = {vm.name: vm for vm in vms}

    tasks_to_run = []

    for task_id, vm_name in best_assignment.items():
        task = tasks[task_id]
        vm = vm_map[vm_name]
        tasks_to_run.append((task, vm))
        print(f"  - Tugas {task.name} (idx: {task.id}) -> {vm.name}")

    # ========================================================
    # Eksekusi seluruh task secara paralel menggunakan asyncio
    # ========================================================
    print(f"\nMemulai eksekusi {len(tasks_to_run)} tugas secara paralel...")
    simulation_start_time = time.time()
    
    async with httpx.AsyncClient() as client:
        # Siapkan coroutine semua task
        task_coroutines = [
            execute_task(client, task, vm, vm_port) 
            for task, vm in tasks_to_run
        ]

        # Jalankan semuanya secara paralel
        results = await asyncio.gather(*task_coroutines)
        
    simulation_end_time = time.time()
    makespan = simulation_end_time - simulation_start_time
    print(f"\nSemua eksekusi tugas selesai dalam {makespan:.4f} detik.")
    
    # ========================================================
    # Analisis & Penyimpanan hasil
    # ========================================================
    df = pd.DataFrame(results)

    # Simpan hasil raw ke CSV
    df.to_csv(RESULTS_FILE, index=False)
    print(f"Data hasil eksekusi disimpan ke {RESULTS_FILE}")

    # Filter task yang sukses
    successful_tasks = df[df['status'] == 'success']
    if successful_tasks.empty:
        print("Tidak ada tugas yang berhasil diselesaikan. Metrik tidak dapat dihitung.")
        return

    # Hitung metrik performa
    avg_turnaround = successful_tasks['execution_time'].mean()
    avg_worker_time = successful_tasks['worker_time'].mean()
    num_success = len(successful_tasks)
    num_failed = len(df) - num_success

    print("\n--- Ringkasan Metrik ---")
    print(f"Total Makespan (Waktu Eksekusi Total): {makespan:.4f} detik")
    print(f"Average Turnaround Time (Scheduler):   {avg_turnaround:.4f} detik")
    print(f"Average Execution Time (Worker):     {avg_worker_time:.4f} detik")
    print(f"Tugas Berhasil: {num_success}")
    print(f"Tugas Gagal:    {num_failed}")
    
    # Buat summary ke file .txt
    summary_file = RESULTS_FILE.replace(".csv", "_summary.txt")
    
    with open(summary_file, 'w') as f:
        f.write("--- Ringkasan Hasil Simulasi ---\n")
        f.write(f"Algorithm: Particle Swarm Optimization (PSO)\n")
        f.write(f"Algorithm Runtime: {algo_time:.4f} detik\n")
        f.write(f"Total Makespan: {makespan:.4f} detik\n")
        f.write(f"Average Turnaround Time (Scheduler): {avg_turnaround:.4f} detik\n")
        f.write(f"Average Execution Time (Worker): {avg_worker_time:.4f} detik\n")
        f.write(f"Tugas Berhasil: {num_success}\n")
        f.write(f"Tugas Gagal: {num_failed}\n")
        f.write(f"Total Tugas: {len(df)}\n")
        f.write(f"Dataset: {TASK_FILE}\n")
        f.write(f"Iterations: {SHC_ITERATIONS}\n")
    
    print(f"Ringkasan metrik disimpan ke {summary_file}")


if __name__ == "__main__":
    asyncio.run(main())
