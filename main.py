
from dataGenerator import generate_data
from simulation  import run_simulation
import matplotlib
matplotlib.use('TkAgg')   # oppure 'Qt5Agg' se hai Qt installato
import matplotlib.pyplot as plt


def main():
    # 1) Genera lo stato iniziale
    init_data = generate_data()

    # 2) Esegui la simulazione: 1000 slot, epoca ogni 50 slot
    history = run_simulation(
        num_slots=100,
        slots_per_epoch=1,
        init_data=init_data
    )

    # 3) Disegna i grafici
    plt.figure(figsize=(8,4))
    plt.plot(history['central_cost'], label='Centralized')
    plt.plot(history['greedy_cost'],    label='Greedy')
    plt.xlabel('Slot temporale')
    plt.ylabel('Costo totale')
    plt.title('Evoluzione del costo per algoritmo')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
