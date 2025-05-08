import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from dataGenerator import generate_data
from simulation import run_simulation_event_based

def main():
    regimes   = ['scarcity', 'abundance']
    ne_values = list(range(10, 101, 10))
    modes     = [False, True]    # False = solo centralized, True = centralized+greedy

    # titolo per la modalità
    label_mode = {False: 'Centralized only', True: 'Centralized+Greedy'}

    for regime in regimes:
        for do_greedy in modes:
            histories = []
            # Simula per ogni ne
            for ne in ne_values:
                init_data = generate_data()

                h = run_simulation_event_based(
                    init_data,
                    ne,
                    regime,
                    do_greedy=do_greedy
                )
                histories.append(h)

            # –– A) Stampa i riepiloghi sul console ––
            total_births = sum(h['births'][-1] for h in histories)
            total_deaths = sum(h['deaths'][-1] for h in histories)
            total_migrations = sum(h['migrations'][-1] for h in histories)
            total_relocations = sum(h['relocations'][-1] for h in histories)

            print(f"--- Regime={regime}, mode={label_mode[do_greedy]} ---")
            print(f"Totale nascite:      {total_births}")
            print(f"Totale morti:        {total_deaths}")
            print(f"Totale migrazioni:   {total_migrations}")
            print(f"Totale riallocazioni:{total_relocations}")
            print()

            # –– B) Grafico 1: ne vs alloc_changes  ––
            plt.figure()
            plt.plot(ne_values,
                     [h['relocations'][-1] for h in histories],
                     marker='o')
            plt.title(f"Alloc relocalizzazioni – {regime}, {label_mode[do_greedy]}")
            plt.xlabel('ne (eventi per epoca)')
            plt.ylabel('Numero riallocazioni')
            plt.grid(True)

            # –– C) Grafico 2: ne vs costo totale centralizzato (e greedy se richiesto) ––
            plt.figure()
            plt.plot(ne_values,
                     [h['central_cost'][-1] for h in histories],
                     marker='o',
                     label='Centralized')
            if do_greedy:
                plt.plot(ne_values,
                         [h['greedy_cost'][-1] for h in histories],
                         marker='x',
                         label='Greedy')
                plt.legend()
            plt.title(f"Costo finale – {regime}, {label_mode[do_greedy]}")
            plt.xlabel('ne (eventi per epoca)')
            plt.ylabel('Costo')
            plt.grid(True)

            # –– D) Grafico 3: distribuzione costi nel tempo ––
            plt.figure()
            all_costs = []
            for h in histories:
                all_costs.extend(h['central_cost'])
                if do_greedy:
                    all_costs.extend(h['greedy_cost'])
            plt.hist(all_costs, bins=30, density=True, alpha=0.7)
            plt.title(f"Distribuzione costi – {regime}, {label_mode[do_greedy]}")
            plt.xlabel('Costo')
            plt.ylabel('PDF')
            plt.grid(True)



    # mostra tutte le 12 figure
    plt.show()

if __name__ == '__main__':
    main()
