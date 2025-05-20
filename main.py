import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

from dataGenerator import generate_data
from simulation import run_simulation_event_based

def main():
    regimes   = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))

    for regime in regimes:
        # raccolgo risultati per ciascun ne
        cen_costs    = []  # costo finale centralizzato
        gs_costs     = []  # costo finale greedy static
        gd_costs     = []  # costo finale greedy dynamic
        avg_cen      = []  # costo medio per epoca centralizzato
        avg_gs       = []  # costo medio per epoca greedy static
        avg_gd       = []  # costo medio per epoca greedy dynamic
        rel_c        = []  # riallocazioni centralizzato
        rel_gs       = []  # riallocazioni greedy static
        rel_gd       = []  # riallocazioni greedy dynamic
        hist_c       = []  # tutti i costi centralizzati
        hist_gd      = []  # tutti i costi dynamic

        print(f"\n=== Regime: {regime} ===")
        for ne in ne_values:
            init_data = generate_data()

            # run matching OFF (static)
            h_off = run_simulation_event_based(init_data, ne, regime, do_greedy=False)
            # run matching ON (dynamic)
            h_on  = run_simulation_event_based(init_data, ne, regime, do_greedy=True)

            # 1) costi finali
            cen_costs.append( h_off['central_cost'][-1] )
            gs_costs .append( h_off['greedy_cost'][-1]  )
            gd_costs .append( h_on ['greedy_cost'][-1]  )

            # 2) costo medio per epoca
            avg_cen.append( np.mean(h_off['central_cost']) )
            avg_gs .append( np.mean(h_off['greedy_cost'])  )
            avg_gd .append( np.mean(h_on ['greedy_cost'])  )

            # 3) riallocazioni finali
            rel_c .append( h_off['relocations'][-1] )
            rel_gs.append( h_off['relocations_greedy'][-1] )
            rel_gd.append( h_on ['relocations_greedy'][-1] )

            # 4) accumulo per istogramma
            hist_c .extend(h_off['central_cost'])
            hist_gd.extend(h_on ['greedy_cost'])

            print(f"ne={ne:3d} → cen={cen_costs[-1]:6.1f}  "
                  f"gs={gs_costs[-1]:6.1f}  gd={gd_costs[-1]:6.1f}  "
                  f"relocC={rel_c[-1]:3d}  relocGS={rel_gs[-1]:3d}  relocGD={rel_gd[-1]:3d}")

        # — Grafico 1: costo medio per epoca vs ne —
        plt.figure()
        plt.plot(ne_values, avg_cen, 'o-', label='Centralized (avg/epoca)')
        plt.plot(ne_values, avg_gs,  'x--', label='Greedy static (avg/epoca)')
        plt.plot(ne_values, avg_gd,  's-.', label='Greedy dynamic (avg/epoca)')
        plt.title(f"Costo medio per epoca vs ne – {regime}")
        plt.xlabel('ne (eventi per epoca)')
        plt.ylabel('Costo medio per epoca')
        plt.legend()
        plt.grid(True)

        # — Grafico 2: ne vs numero di riallocazioni —
        plt.figure()
        plt.plot(ne_values, rel_c,  'o-', label='Centralized')
        plt.plot(ne_values, rel_gs, 'x--', label='Greedy static')
        plt.plot(ne_values, rel_gd, 's-.', label='Greedy dynamic')
        plt.title(f"Riallocazioni vs ne – {regime}")
        plt.xlabel('ne (eventi per epoca)')
        plt.ylabel('Numero riallocazioni')
        plt.legend()
        plt.grid(True)

        # — Grafico 3: istogramma probabilità costi totali —
        plt.figure()
        mn, mx = min(hist_c + hist_gd), max(hist_c + hist_gd)
        bins = 30
        plt.hist(hist_c,  bins=bins, range=(mn, mx),
                 density=True, alpha=0.6, label='Centralized')
        plt.hist(hist_gd, bins=bins, range=(mn, mx),
                 density=True, alpha=0.6, label='Greedy dynamic')
        plt.title(f"Distribuzione costi totali – {regime}")
        plt.xlabel('Costo totale')
        plt.ylabel('PDF')
        plt.xlim(mn, mx)
        plt.legend()
        plt.grid(True)

    plt.show()

if __name__ == '__main__':
    main()
