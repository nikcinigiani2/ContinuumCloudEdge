
from dataGenerator import generate_data
from simulation  import run_simulation
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

#TODO: riguarda i funzionamenti di centralized perche rialloca ogni slot ma deve farlo solo ogni epoca;
def main():
    # 1) Genera lo stato iniziale
    init_data = generate_data()
    print(">>> Avvio simulazione", flush=True)

    # 2) Esegui la simulazione: 1000 slot, epoca ogni 50 slot
    history = run_simulation(
        num_slots=1000,
        slots_per_epoch=1000,   # epoca ogni 10 slot
        init_data=init_data
    )
    print(">>> Simulazione terminata", flush=True)


    #voglio la stampa di quante mu app e lamba app c'erano alll'inizio e quante alla fine
    print(f"Numero di μ-app iniziali: {history['num_mu'][0]}")
    print(f"Numero di λ-app iniziali: {history['num_lambda'][0]}")
    print(f"Numero di μ-app finali: {history['num_mu'][-1]}")
    print(f"Numero di λ-app finali: {history['num_lambda'][-1]}")
    print(f"Costo finale centralizzato: {history['central_cost'][-1]}")
    print(f"Costo finale greedy: {history['greedy_cost'][-1]}")


    # 3) Disegna i grafici
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
