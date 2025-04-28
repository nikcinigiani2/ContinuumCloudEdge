
from dataGenerator import generate_data
from simulation  import run_simulation
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    #  Gener0 lo stato iniziale
    init_data = generate_data()
    print(">>> Avvio simulazione", flush=True)

    #  Esegui la simulazione
    history = run_simulation(
        num_slots=1000,
        slots_per_epoch=1000,   # epoca ogni 10 slot
        init_data=init_data
    )
    print(">>> Simulazione terminata", flush=True)



    print(f"Numero di μ-app iniziali: {history['num_mu'][0]}")
    print(f"Numero di λ-app iniziali: {history['num_lambda'][0]}")
    print(f"Numero di μ-app finali: {history['num_mu'][-1]}")
    print(f"Numero di λ-app finali: {history['num_lambda'][-1]}")
    print(f"Costo finale centralizzato: {history['central_cost'][-1]}")
    print(f"Costo finale greedy: {history['greedy_cost'][-1]}")


    # grafici
    plt.figure(figsize=(8,4))
    plt.plot(history['central_cost'], label='Centralized')
    plt.plot(history['greedy_cost'],    label='Greedy')
    plt.xlabel('Slot temporale')
    plt.ylabel('Costo totale')
    plt.title('Evoluzione del costo per algoritmo')
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()




if __name__ == '__main__':
    main()
