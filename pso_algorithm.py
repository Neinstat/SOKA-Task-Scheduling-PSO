import numpy as np
import time
from collections import namedtuple

# Tipe data VM dan Task harus sama dengan yang dipakai di pso_scheduler.py
VM = namedtuple('VM', ['name', 'ip', 'cpu_cores', 'ram_gb'])
Task = namedtuple('Task', ['id', 'name', 'index', 'cpu_load'])

def calculate_makespan(tasks: list[Task], vms: list[VM], position: np.ndarray) -> float:
    """
    Fungsi ini digunakan sebagai 'fitness function' dalam PSO.
    Logikanya:
    - Setiap posisi (solusi) menunjukkan task dipetakan ke VM mana.
    - Kita hitung total waktu kerja tiap VM berdasarkan beban (cpu_load / cpu_cores).
    - Makespan = waktu VM yang paling lama bekerja.
    Semakin kecil makespan → semakin baik solusi tersebut.
    """
    num_vms = len(vms)
    vm_loads = np.zeros(num_vms) 
    vm_cpu_cores = np.array([vm.cpu_cores for vm in vms])  # kapasitas CPU tiap VM

    for i, task in enumerate(tasks):
        # Ambil nilai posisi partikel, dibulatkan untuk menentukan VM final.
        vm_index = int(np.round(position[i]))
        
        # Pastikan tidak keluar indeks.
        vm_index = max(0, min(vm_index, num_vms - 1))
        
        # Hitung waktu eksekusi task di VM tersebut.
        # Semakin besar cpu_cores → semakin cepat task selesai.
        task_exec_time = task.cpu_load / vm_cpu_cores[vm_index]
        
        # Tambahkan ke total workload VM itu.
        vm_loads[vm_index] += task_exec_time

    # Makespan adalah waktu kerja maksimum di antara semua VM.
    return np.max(vm_loads)

class Particle:
    """Setiap Particle mewakili 1 solusi penjadwalan lengkap."""
    def __init__(self, num_tasks: int, num_vms: int):
        self.num_tasks = num_tasks
        self.num_vms = num_vms
        
        # Posisi awal: solusi acak (task ke VM mana)
        # Contoh: [0.2, 2.8, 1.1] → akan dibulatkan jadi VM 0, VM 3, VM 1
        self.position = np.random.uniform(0, num_vms, num_tasks)
        
        # Kecepatan awal: arah perubahan posisi (random)
        # Ini menentukan perubahan solusi setiap iterasi.
        self.velocity = np.random.uniform(-1, 1, num_tasks)
        
        # Personal best (solusi terbaik yang pernah ditemukan partikel ini)
        self.pbest_position = self.position.copy()
        self.pbest_fitness = np.inf

    def update_velocity(self, gbest_position: np.ndarray, w: float, c1: float, c2: float):
        """
        Rumus update kecepatan PSO (standar):
        velocity = w * velocity + c1 * r1 * (pbest - position) + c2 * r2 * (gbest - position)

        Intinya:
        - w   → mempertahankan arah sebelumnya (inersia)
        - c1  → partikel belajar dari pengalaman terbaik dirinya sendiri
        - c2  → partikel mengikuti solusi terbaik dari seluruh swarm
        """
        r1 = np.random.rand(self.num_tasks)
        r2 = np.random.rand(self.num_tasks)
        
        cognitive_component = c1 * r1 * (self.pbest_position - self.position)
        social_component = c2 * r2 * (gbest_position - self.position)
        inertia_component = w * self.velocity
        
        # Total kecepatan baru
        self.velocity = inertia_component + cognitive_component + social_component

    def update_position(self):
        """
        Update posisi partikel berdasarkan velocity.
        Posisi = solusi baru (penugasan task → VM).
        """
        self.position = self.position + self.velocity
        
        # Pastikan posisi tetap dalam range VM yang valid (0 sampai num_vms)
        # Supaya tidak terjadi VM index negatif atau lebih besar dari jumlah VM.
        self.position = np.clip(self.position, 0, self.num_vms - 1e-6)


def particle_swarm_optimization(tasks: list[Task], vms: list[VM],
                                max_iterations: int, num_particles: int = 30,
                                w: float = 0.5, c1: float = 1.5, c2: float = 1.5):
    """
    Fungsi utama PSO:
    - Membuat swarm (kumpulan partikel = kumpulan solusi).
    - Setiap iterasi, evaluasi semua solusi, update pbest dan gbest.
    - Update velocity dan position.
    - Setelah iterasi selesai, keluarkan solusi terbaik (gbest).

    PSO mencari solusi optimal secara global,
    tidak seperti SHC yang hanya mencari di sekitar 1 solusi saja.
    """
    num_tasks = len(tasks)
    num_vms = len(vms)
    vm_names = [vm.name for vm in vms]  # untuk hasil akhir mapping ke VM name

    # Inisialisasi swarm dengan banyak partikel (banyak solusi awal)
    swarm = [Particle(num_tasks, num_vms) for _ in range(num_particles)]
    gbest_position = None
    gbest_fitness = np.inf  # semakin kecil → semakin baik

    print(f"Memulai Particle Swarm Optimization ({max_iterations} iterasi, {num_particles} partikel)...")
    start_time = time.time()

    # Perulangan iterasi PSO
    for i in range(max_iterations):
        for particle in swarm:
            # Hitung fitness (makespan) untuk solusi partikel saat ini
            fitness = calculate_makespan(tasks, vms, particle.position)
            
            # Perbarui personal best jika solusi saat ini lebih baik
            if fitness < particle.pbest_fitness:
                particle.pbest_fitness = fitness
                particle.pbest_position = particle.position.copy()
            
            # Perbarui global best (solusi terbaik di seluruh swarm)
            if fitness < gbest_fitness:
                gbest_fitness = fitness
                gbest_position = particle.position.copy()
        
        # Setelah semua partikel dievaluasi, update velocity dan position
        for particle in swarm:
            particle.update_velocity(gbest_position, w, c1, c2)
            particle.update_position()
            
        # Log progress tiap 10% iterasi
        if (i + 1) % (max_iterations // 10 or 1) == 0:
            print(f"Iterasi {i+1}/{max_iterations}: Estimasi Makespan Terbaik: {gbest_fitness:.2f}")

    end_time = time.time()
    print(f"PSO Selesai dalam {end_time - start_time:.2f} detik. Estimasi Makespan Terbaik: {gbest_fitness:.2f}")

    # Konversi solusi terbaik (gbest_position) ke dictionary task → VM
    best_assignment = {}
    final_indices = np.round(gbest_position).astype(int)
    final_indices = np.clip(final_indices, 0, num_vms - 1)  # jaga tetap valid

    for i, task in enumerate(tasks):
        vm_index = final_indices[i]
        best_assignment[task.id] = vm_names[vm_index]
        
    return best_assignment
