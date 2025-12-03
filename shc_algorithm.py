import random
import copy

def calculate_makespan(assignment, vms, tasks):
    """Menghitung makespan estimasi berdasarkan CPU load."""
    vm_processing_times = {vm.name: 0.0 for vm in vms}
    vm_map = {vm.name: vm for vm in vms}

    for task_id, vm_name in assignment.items():
        task = next((t for t in tasks if t.id == task_id), None)
        if task:
            vm = vm_map[vm_name]
            # Rumus estimasi: Load / Core
            processing_time = task.cpu_load / vm.cpu_cores
            vm_processing_times[vm_name] += processing_time

    return max(vm_processing_times.values())

def stochastic_hill_climbing(tasks, vms, max_iterations=1000):
    """Algoritma SHC dengan output print progress."""
    current_assignment = {}
    vm_names = [vm.name for vm in vms]
    
    # Inisialisasi Random
    for task in tasks:
        current_assignment[task.id] = random.choice(vm_names)

    current_makespan = calculate_makespan(current_assignment, vms, tasks)
    
    # --- PRINT AWAL ---
    print(f"Estimasi Makespan Awal (Random): {current_makespan:.2f}")

    for i in range(max_iterations):
        neighbor_assignment = current_assignment.copy()
        
        # Mutasi: Pindahkan 1 task ke VM acak lain
        random_task = random.choice(tasks)
        new_vm = random.choice(vm_names)
        neighbor_assignment[random_task.id] = new_vm
        
        neighbor_makespan = calculate_makespan(neighbor_assignment, vms, tasks)
        
        if neighbor_makespan < current_makespan:
            current_assignment = neighbor_assignment
            current_makespan = neighbor_makespan
        
        # --- TAMBAHAN: PRINT PROGRES PER 100 ITERASI ---
        if (i + 1) % 100 == 0:
            print(f"Iterasi {i + 1}/{max_iterations}: Estimasi Makespan Terbaik: {current_makespan:.2f}")

    print(f"SHC Selesai. Estimasi Makespan Terbaik: {current_makespan:.2f}")
    return current_assignment