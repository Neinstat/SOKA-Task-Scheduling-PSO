import httpx
import asyncio
import time
import pandas as pd
import os
import csv
from dotenv import load_dotenv
from collections import namedtuple

# --- ALGORITMA ---
from shc_algorithm import stochastic_hill_climbing

# --- KONFIGURASI ---
load_dotenv()

# ==============================================================================
# BAGIAN INI YANG DIGANTI-GANTI UNTUK PENGUJIAN
# Pilih salah satu nama file dataset:
# 1. dataset_random_simple.txt
# 2. dataset_random_stratified.txt
# 3. dataset_low_high.txt
# ==============================================================================
TASK_FILE = "dataset_low_high.txt"
# ==============================================================================

# --- REVISI MINOR: Penamaan Output Dinamis ---
# Mengambil nama file dataset tanpa ekstensi .txt
dataset_name = os.path.splitext(TASK_FILE)[0]

# Nama file output otomatis menyesuaikan dataset
RESULTS_FILE = f"shc_{dataset_name}.csv"
SUMMARY_FILE = f"shc_{dataset_name}_summary.txt"
# ---------------------------------------------

SHC_ITERATIONS = 1000
HTTP_TIMEOUT = 120.0

VM = namedtuple('VM', ['name', 'ip', 'cpu_cores', 'ram_gb'])
Task = namedtuple('Task', ['id', 'name', 'index', 'cpu_load'])

# ============================================================
# Fungsi Load VM (Dengan Print Detail)
# ============================================================
def load_vms():
    vms = []
    i = 1
    while True:
        vm_name = f"VM{i}"
        ip = os.getenv(f"{vm_name}_IP")
        cpu = os.getenv(f"{vm_name}_CPU")
        ram = os.getenv(f"{vm_name}_RAM")
        
        if not ip: break
        try:
            vms.append(VM(name=vm_name.lower(), ip=ip, cpu_cores=int(cpu), ram_gb=int(ram)))
        except: pass
        i += 1
    
    if not vms: 
        print("Error: Tidak ada VM ditemukan.")
        exit(1)
        
    # --- PRINT VM DETAILS ---
    print(f"Berhasil memuat {len(vms)} VMs:")
    for vm in vms:
        print(f"  - {vm.name}: IP={vm.ip}, CPU={vm.cpu_cores}, RAM={vm.ram_gb}")
        
    return vms

# ============================================================
# Fungsi Load Tasks
# ============================================================
def load_tasks(task_file: str):
    tasks = []
    print(f"Membaca tugas dari {task_file}...")
    try:
        with open(task_file, 'r') as f:
            lines = f.readlines()
        
        task_id_counter = 0
        for line in lines:
            line = line.strip()
            if not line: continue
            try:
                if line.isdigit():
                    idx = int(line)
                    name = f"task-{idx}"
                elif '-' in line:
                    parts = line.split('-')
                    if len(parts) >= 2 and parts[1].isdigit():
                        idx = int(parts[1])
                        name = line
                    else: continue
                else: continue

                # CPU load simulasi
                cpu_load = (idx * idx * 100) 
                
                tasks.append(Task(id=task_id_counter, name=name, index=idx, cpu_load=cpu_load))
                task_id_counter += 1
            except: continue
        
        # --- PRINT TASK COUNT ---    
        print(f"Berhasil memuat {len(tasks)} tugas dari {task_file}")
        return tasks
    except Exception as e:
        print(f"Error membaca file dataset: {e}")
        exit(1)

# ============================================================
# Eksekusi HTTP (Dengan Print Eksekusi)
# ============================================================
async def execute_task(client, task, vm, vm_port):
    url = f"http://{vm.ip}:{vm_port}/task/{task.index}"
    
    # --- PRINT EKSEKUSI ---
    print(f"Mengeksekusi {task.name} (idx: {task.id}) di {vm.name} (IP: {vm.ip})...")
    
    try:
        response = await client.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        w_time = float(str(data.get('execution_time', '0.0')).replace('s',''))
        return {
            "index": task.index,
            "task_name": task.name,
            "vm_assigned": vm.name,
            "status": "success",
            "worker_time": w_time
        }
    except Exception as e:
        print(f"ERROR: {task.name} di {vm.name} -> {e}")
        return {
            "index": task.index, "task_name": task.name, "vm_assigned": vm.name,
            "status": "failed", "worker_time": 0.0
        }

# ============================================================
# MAIN PROGRAM
# ============================================================
async def main():
    vms = load_vms()
    tasks = load_tasks(TASK_FILE)
    vm_port = os.getenv("VM_PORT", "5000")
    
    if not tasks: return

    # --- JALANKAN ALGORITMA SHC ---
    print("\n--- Menjalankan Algoritma: Stochastic Hill Climbing (SHC) ---")
    start_algo = time.time()
    
    # Iterasi akan diprint oleh fungsi ini
    best_assignment = stochastic_hill_climbing(tasks, vms, max_iterations=SHC_ITERATIONS)
    
    algo_time = time.time() - start_algo
    print(f"Algoritma SHC selesai dalam {algo_time:.4f} detik.")

    # --- TAMPILKAN HASIL ASSIGNMENT ---
    print("\nPenugasan Tugas Terbaik Ditemukan:")
    vm_map = {vm.name: vm for vm in vms}
    tasks_to_run = []
    
    sorted_task_ids = sorted(best_assignment.keys())
    
    for task_id in sorted_task_ids:
        vm_name = best_assignment[task_id]
        task = next(t for t in tasks if t.id == task_id)
        vm = vm_map[vm_name]
        tasks_to_run.append((task, vm))
        print(f"  - Tugas {task.name} (idx: {task.id}) -> {vm.name}")

    print(f"\nMemulai eksekusi {len(tasks_to_run)} tugas secara paralel...")
    
    # --- EKSEKUSI PARALEL ---
    async with httpx.AsyncClient() as client:
        coroutines = [execute_task(client, t, v, vm_port) for t, v in tasks_to_run]
        results = await asyncio.gather(*coroutines)

    # --- POST PROCESSING ---
    valid_results = [r for r in results if r['status'] == 'success']
    sorted_results = sorted(valid_results, key=lambda x: x['index'])

    vm_finish_times = {vm.name: 0.0 for vm in vms}
    final_data = []

    for item in sorted_results:
        vm = item['vm_assigned']
        exec_time = item['worker_time']
        
        start_time = vm_finish_times[vm]
        wait_time = start_time 
        finish_time = start_time + exec_time
        
        vm_finish_times[vm] = finish_time
        
        final_data.append({
            'index': item['index'],
            'task_name': item['task_name'],
            'vm_assigned': vm,
            'start_time': start_time,
            'exec_time': exec_time,
            'finish_time': finish_time,
            'wait_time': wait_time
        })

    # --- HITUNG STATISTIK ---
    if not final_data:
        print("Gagal: Tidak ada data sukses.")
        return

    total_tasks = len(final_data)
    makespan = max(t['finish_time'] for t in final_data)
    throughput = total_tasks / makespan if makespan > 0 else 0
    total_cpu = sum(t['exec_time'] for t in final_data)
    total_wait = sum(t['wait_time'] for t in final_data)
    
    avg_start = sum(t['start_time'] for t in final_data) / total_tasks
    avg_exec = total_cpu / total_tasks
    avg_finish = sum(t['finish_time'] for t in final_data) / total_tasks
    
    loads = list(vm_finish_times.values())
    avg_load = sum(loads) / len(loads)
    imbalance = (max(loads) - min(loads)) / avg_load if avg_load > 0 else 0
    utilization = (total_cpu / (makespan * len(vms))) * 100 if makespan > 0 else 0

    # --- SIMPAN CSV ---
    fields = ['index', 'task_name', 'vm_assigned', 'start_time', 'exec_time', 'finish_time', 'wait_time']
    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(final_data)

    # --- FORMAT OUTPUT ---
    output_text = (
        f"--- Hasil Algoritma: SHC ---\n"
        f"Dataset                   : {TASK_FILE}\n"
        f"Total Tugas Selesai       : {total_tasks}\n"
        f"Makespan                  : {makespan:.4f} detik\n"
        f"Throughput                : {throughput:.4f} tugas/detik\n"
        f"Total CPU Time            : {total_cpu:.4f} detik\n"
        f"Total Wait Time           : {total_wait:.4f} detik\n"
        f"Average Exec Time         : {avg_exec:.4f} detik\n"
        f"Imbalance Degree          : {imbalance:.4f}\n"
        f"Resource Utilization      : {utilization:.4f}%\n"
        f"----------------------------------------"
    )

    # 1. Print ke Konsol
    print(f"\nSemua eksekusi tugas selesai dalam {makespan:.4f} detik.")
    print(f"Data hasil CSV disimpan ke {RESULTS_FILE}\n")
    print(output_text)

    # 2. Simpan ke Summary File (.txt)
    with open(SUMMARY_FILE, 'w') as f:
        f.write(output_text)
        
    print(f"\nRingkasan lengkap disimpan ke {SUMMARY_FILE}")

if __name__ == "__main__":
    asyncio.run(main())