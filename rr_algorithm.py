def round_robin_scheduling(tasks, vms):
    """
    Algoritma Round Robin (RR).
    Membagi tugas secara siklis (berputar) ke setiap VM.
    """
    assignment = {}
    num_vms = len(vms)
    vm_names = [vm.name for vm in vms]
    
    print(f"Total Tugas: {len(tasks)}, Total VM: {num_vms}")
    
    # Urutkan tugas berdasarkan index kedatangan (agar RR rapi urutannya)
    sorted_tasks = sorted(tasks, key=lambda x: x.index)

    for i, task in enumerate(sorted_tasks):
        # Gunakan modulus untuk menentukan giliran VM
        vm_index = i % num_vms
        selected_vm = vm_names[vm_index]
        
        assignment[task.id] = selected_vm
        
    return assignment