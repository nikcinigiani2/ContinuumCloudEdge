import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from dataGenerator import generate_data
from simulation import run_simulation_event_based

#TODO: ricontrollare grafico app attive, ricontrollare troppi costi=0
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

            # 1) ne vs numero di riallocazioni
            plt.figure()
            plt.plot(ne_values,
                     [h['relocations'][-1] for h in histories],
                     marker='o', label='Riallocazioni')
            plt.title(f"Riallocazioni vs ne – {regime}, matching={'ON' if do_matching else 'OFF'}")
            plt.xlabel('ne (eventi per epoca)')
            plt.ylabel('Numero riallocazioni')
            plt.grid(True)

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

            # 3) istogramma distribuzione costi (tutte le epoche, entrambi)
            plt.figure()
            all_costs = []
            for h in histories:
                all_costs.extend(h['central_cost'])
                all_costs.extend(h['greedy_cost'])
            plt.hist(all_costs, bins=30, density=True, alpha=0.7)
            plt.title(f"Distribuzione costi – {regime}, matching={'ON' if do_matching else 'OFF'}")
            plt.xlabel('Costo')
            plt.ylabel('PDF')
            plt.grid(True)



    # stampa riepilogo finale (sull’ultima modalità/regime)
    last = histories[-1]
    print("\n--- Totali simulazione ---")
    print(f"Nascite:      {last['total_births']}")
    print(f"Morti:        {last['total_deaths']}")
    print(f"Migrazioni:   {last['total_migrations']}")
    print(f"Riallocazioni:{last['total_relocations']}")

    # Andamento numero di app attive nel tempo (per ciascuna epoca)
    plt.figure()
    for idx, h in enumerate(histories):
        # h['ne']      = lista di eventi cumulati ad ogni epoca
        # h['num_apps']= # di app attive a fine epoca
        plt.plot(h['ne'], h['num_apps'],
                 marker='.',
                 label=f'ne = {ne_values[idx]}')
    plt.title(f"Applicazioni attive nel tempo – {regime}, matching={'ON' if do_matching else 'OFF'}")
    plt.xlabel('Eventi cumulati')
    plt.ylabel('Numero di applicazioni attive')
    plt.legend(ncol=2, fontsize='small')
    plt.grid(True)

    # mostra le 12 figure (2 regimi × 2 modalità × 3 grafici) + 1 riepilogo app
    plt.show()



if __name__ == '__main__':
    main()
