import httpx
import asyncio
import time
import pandas as pd
import os
import csv
from dotenv import load_dotenv
from collections import namedtuple

# --- IMPORT ALGORITMA RR ---
from rr_algorithm import round_robin_scheduling

# --- KONFIGURASI ---
load_dotenv()

# ==============================================================================
# GANTI DATASET DI SINI:
# 1. dataset_random_simple.txt
# 2. dataset_random_stratified.txt
# 3. dataset_low_high.txt
# ==============================================================================
TASK_FILE = "dataset_random_simple.txt"
# ==============================================================================

# Nama File Output Dinamis
dataset_name = os.path.splitext(TASK_FILE)[0]
RESULTS_FILE = f"rr_{dataset_name}.csv"
SUMMARY_FILE = f"rr_{dataset_name}_summary.txt"

HTTP_TIMEOUT = 120.0

VM = namedtuple('VM', ['name', 'ip', 'cpu_cores', 'ram_gb'])
Task = namedtuple('Task', ['id', 'name', 'index', 'cpu_load'])

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
    if not vms: exit(1)
    print(f"Berhasil memuat {len(vms)} VMs:")
    for vm in vms:
        print(f"  - {vm.name}: IP={vm.ip}, CPU={vm.cpu_cores}, RAM={vm.ram_gb}")
    return vms

def load_tasks(task_file):
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
                cpu_load = (idx * idx * 100) 
                tasks.append(Task(id=task_id_counter, name=name, index=idx, cpu_load=cpu_load))
                task_id_counter += 1
            except: continue
        print(f"Berhasil memuat {len(tasks)} tugas.")
        return tasks
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

async def execute_task(client, task, vm, vm_port):
    url = f"http://{vm.ip}:{vm_port}/task/{task.index}"
    print(f"Mengeksekusi {task.name} (idx: {task.id}) di {vm.name}...")
    try:
        response = await client.get(url, timeout=HTTP_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        w_time = float(str(data.get('execution_time', '0.0')).replace('s',''))
        return {"index": task.index, "task_name": task.name, "vm_assigned": vm.name, "status": "success", "worker_time": w_time}
    except Exception as e:
        print(f"Error {task.name}: {e}")
        return {"index": task.index, "task_name": task.name, "vm_assigned": vm.name, "status": "failed", "worker_time": 0.0}

async def main():
    vms = load_vms()
    tasks = load_tasks(TASK_FILE)
    vm_port = os.getenv("VM_PORT", "5000")
    
    if not tasks: return

    print("\n--- Menjalankan Algoritma: Round Robin (RR) ---")
    start_algo = time.time()
    
    # PANGGIL ALGORITMA RR
    best_assignment = round_robin_scheduling(tasks, vms)
    
    algo_time = time.time() - start_algo
    print(f"Algoritma RR selesai dalam {algo_time:.4f} detik.")

    print("\nPenugasan Tugas:")
    vm_map = {vm.name: vm for vm in vms}
    tasks_to_run = []
    
    sorted_task_ids = sorted(best_assignment.keys())
    for task_id in sorted_task_ids:
        vm_name = best_assignment[task_id]
        task = next(t for t in tasks if t.id == task_id)
        tasks_to_run.append((task, vm_map[vm_name]))
        print(f"  - Tugas {task.name} -> {vm_name}")

    print(f"\nMemulai eksekusi {len(tasks_to_run)} tugas...")
    
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
        vm_finish_times[vm] = start_time + exec_time
        final_data.append({
            'index': item['index'], 'task_name': item['task_name'], 'vm_assigned': vm,
            'start_time': start_time, 'exec_time': exec_time, 
            'finish_time': start_time + exec_time, 'wait_time': start_time
        })

    if not final_data: return

    total_tasks = len(final_data)
    makespan = max(t['finish_time'] for t in final_data)
    throughput = total_tasks / makespan if makespan > 0 else 0
    total_cpu = sum(t['exec_time'] for t in final_data)
    total_wait = sum(t['wait_time'] for t in final_data)
    avg_exec = total_cpu / total_tasks
    
    loads = list(vm_finish_times.values())
    avg_load = sum(loads) / len(loads)
    imbalance = (max(loads) - min(loads)) / avg_load if avg_load > 0 else 0
    utilization = (total_cpu / (makespan * len(vms))) * 100 if makespan > 0 else 0

    with open(RESULTS_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['index', 'task_name', 'vm_assigned', 'start_time', 'exec_time', 'finish_time', 'wait_time'])
        writer.writeheader()
        writer.writerows(final_data)

    output_text = (
        f"--- Hasil Algoritma: Round Robin (RR) ---\n"
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

    print(f"\nSemua eksekusi tugas selesai dalam {makespan:.4f} detik.")
    print(output_text)
    
    with open(SUMMARY_FILE, 'w') as f:
        f.write(output_text)
    print(f"\nRingkasan disimpan ke {SUMMARY_FILE}")

if __name__ == "__main__":
    asyncio.run(main())