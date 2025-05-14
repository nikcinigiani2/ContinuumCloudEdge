import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np


from dataGenerator import generate_data
from simulation import run_simulation_event_based

#TODO: aggiungi swapping matching, ricontrolla picchi costo, ricontrolla matchingON-OFF


def main():
    regimes   = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))
    modes     = [False, True]    # False = matching OFF, True = matching ON

    for regime in regimes:
        for do_matching in modes:
            histories = []
            print(f"\n=== Regime={regime}, matching={'ON' if do_matching else 'OFF'} ===")
            for ne in ne_values:
                # per riproducibilità: stessa semina Rand? (opzionale)
                init_data = generate_data()
                h = run_simulation_event_based(
                    init_data,
                    ne,
                    regime,
                    do_greedy=do_matching
                )
                histories.append(h)
                print(f"  ne={ne}  → centralized={h['central_cost'][-1]:.1f}  greedy={h['greedy_cost'][-1]:.1f}")
            """
            # 1) ne vs numero di riallocazioni
            plt.figure()
            plt.plot(ne_values,
                     [h['relocations'][-1] for h in histories],
                     marker='o', label='Riallocazioni')
            plt.title(f"Riallocazioni vs ne – {regime}, matching={'ON' if do_matching else 'OFF'}")
            plt.xlabel('ne (eventi per epoca)')
            plt.ylabel('Numero riallocazioni')
            plt.grid(True)
            """
            # 2) ne vs costo finale (centralized + matching)
            plt.figure()
            plt.plot(ne_values,
                     [h['central_cost'][-1] for h in histories],
                     marker='o', label='Centralized')
            plt.plot(ne_values,
                     [h['greedy_cost'][-1] for h in histories],
                     marker='x', label='Matching')
            plt.title(f"Costo finale vs ne – {regime}, matching={'ON' if do_matching else 'OFF'}")
            plt.xlabel('ne (eventi per epoca)')
            plt.ylabel('Costo')
            plt.legend()
            plt.grid(True)
            """
            # 3) istogramma distribuzione costi (tutte le epoche, entrambi)
            plt.figure()

            # Separiamo le due liste di costi
            central_costs = []
            matching_costs = []

            for h in histories:
                central_costs.extend(h['central_cost'])
                matching_costs.extend(h['greedy_cost'])

            # Troviamo min e max su TUTTI i costi
            all_costs = central_costs + matching_costs
            min_cost = min(all_costs)
            max_cost = max(all_costs)

            # Istogramma Centralized
            plt.hist(central_costs,
                     bins=30,
                     range=(min_cost, max_cost),
                     density=True,
                     alpha=0.6,
                     label='Centralized')

            # Istogramma Matching (se ci sono dati)
            if matching_costs:
                plt.hist(matching_costs,
                         bins=30,
                         range=(min_cost, max_cost),
                         density=True,
                         alpha=0.6,
                         label='Matching')

            # Impostiamo esplicitamente i limiti dell'asse X
            plt.xlim(min_cost, max_cost)

            plt.title(f"Distribuzione costi – {regime}, matching={'ON' if do_matching else 'OFF'}")
            plt.xlabel('Costo')
            plt.ylabel('PDF')
            plt.legend()
            plt.grid(True)
            """

    # stampa riepilogo finale (sull’ultima modalità/regime)
    last = histories[-1]
    print("\n--- Totali simulazione ---")
    print(f"Nascite:      {last['total_births']}")
    print(f"Morti:        {last['total_deaths']}")
    print(f"Migrazioni:   {last['total_migrations']}")
    print(f"Riallocazioni:{last['total_relocations']}")

    # Andamento numero di app attive nel tempo (per ciascuna epoca)
    # GRAFICO “numero di app attive vs eventi” SOLO PER l’ULTIMA SIMULAZIONE
    h_last = histories[-1]

    x = np.array(h_last['ne'])
    y = np.array(h_last['num_apps'])

    # calcolo quanti epoch = un marker ogni 3000 eventi
    # ne è il passo di eventi per epoca
    step = max(1, 3000 // ne)

    # seleziono solo quegli epoch
    x_sel = x[::step]
    y_sel = y[::step]

    plt.figure()
    plt.plot(x_sel, y_sel, marker='o', linestyle='-')
    plt.title(f"App attive vs eventi (1 marker ogni 3000 eventi) – ne={ne}")
    plt.xlabel("Eventi cumulati")
    plt.ylabel("App attive")
    plt.grid(True)
    # mostra le 12 figure (2 regimi × 2 modalità × 3 grafici) + 1 riepilogo app
    plt.show()



if __name__ == '__main__':
    main()
