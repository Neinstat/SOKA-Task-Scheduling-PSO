def fcfs_scheduling(tasks, vms):
    """
    Algoritma First-Come First-Served (FCFS) / Greedy Arrival.
    Tugas dijadwalkan berdasarkan urutan kedatangan ke VM yang paling 
    cepat tersedia (Estimated Finish Time Terkecil).
    """
    assignment = {}
    
    # Melacak estimasi waktu selesai setiap VM
    # Key: Nama VM, Value: Total estimasi waktu beban kerja
    vm_est_finish_times = {vm.name: 0.0 for vm in vms}
    vm_map = {vm.name: vm for vm in vms}
    
    # Urutkan tugas berdasarkan index (Arrival Order)
    sorted_tasks = sorted(tasks, key=lambda x: x.index)
    
    print(f"Menjadwalkan {len(tasks)} tugas dengan metode FCFS...")

    for task in sorted_tasks:
        # Cari VM yang 'paling kosong' atau 'paling cepat selesai' saat ini
        best_vm_name = min(vm_est_finish_times, key=vm_est_finish_times.get)
        
        # Tugaskan ke VM tersebut
        assignment[task.id] = best_vm_name
        
        # Hitung estimasi beban tugas ini
        vm_obj = vm_map[best_vm_name]
        est_proc_time = task.cpu_load / vm_obj.cpu_cores
        
        # Update waktu sibuk VM tersebut
        vm_est_finish_times[best_vm_name] += est_proc_time
        
    return assignment