import math
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from dataGenerator     import generate_data
from scenario          import generate_scenario, replay_scenario
from simulation        import p  # probabilità base di nascita pura

def main():
    regimes   = ['scarsità','abbondanza'] #ho rimosso momentaneamente scarsità perche non avevo definito la differenza dei due regimi
    #dunque i grafici venivano diversi ma solo perché generate_data era dentro il for di regime in regimes
    ne_values = list(range(10, 101, 10))

    # 1) Genero lo stato iniziale
    base_init = generate_data()

    # Calcolo lam e mu da base_init
    mu = base_init['mu_appl']
    lam = len(base_init['totAppl']) - mu

    # Imposto ec (numero di slot per epoca)
    ec = 10

    # 2) Calcolo timeHorizon secondo la formula: ceil((5*(lam+mu)/p)) * ec
    timeHorizon = math.ceil((5 * (lam + mu) / p)) * ec

    # 3) Genero lo scenario usando il timeHorizon calcolato
    init_data, events = generate_scenario(timeHorizon, base_init)



    for regime in regimes:

        # 4) Per ogni ne eseguo il replay e raccolgo i risultati
        mc, mgs, mgd = [], [], []
        relC_list, relD_list = [], []

        for ne in ne_values:
            mean_c, mean_gs, mean_gd, reloc_c, reloc_d = replay_scenario(
                init_data, events, regime, ne
            )
            mc.append(mean_c)
            mgs.append(mean_gs)
            mgd.append(mean_gd)

            relC_list.append(reloc_c)
            relD_list.append(reloc_d)

        # 5a) Grafico dei costi medi
        plt.figure(figsize=(10, 5))
        plt.plot(ne_values, mc,  'o-', label='Centralized')
        plt.plot(ne_values, mgs, 'x--', label='Greedy static')
        plt.plot(ne_values, mgd, 's-.', label='Greedy dynamic')
        plt.xlabel('ne (eventi tra ricalcolo)')
        plt.ylabel('Costo medio totale')
        plt.title(f"Costo medio vs ne – {regime}")
        plt.legend()
        plt.grid(True)

        # 5b) Grafico delle rilocazioni cumulative
        plt.figure(figsize=(10, 5))
        plt.plot(ne_values, relC_list, 'o-', label='Rilocazioni Centralized')
        plt.plot(ne_values, relD_list, 's--', label='Rilocazioni Dynamic')
        plt.xlabel('ne (eventi tra ricalcolo)')
        plt.ylabel('Numero totale di rilocazioni')
        plt.title(f"Riallocazioni vs ne – {regime}")
        plt.legend()
        plt.grid(True)

    plt.show()

if __name__ == '__main__':
    main()
