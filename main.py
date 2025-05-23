import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import numpy as np

from dataGenerator import generate_data
from simulation import run_simulation_event_based

NUM_RUNS = 1


def main():
    regimes   = ['scarsità', 'abbondanza']
    ne_values = list(range(10, 101, 10))

    for regime in regimes:
        # Inizializzo le somme su tutte le run
        sum_avg_cen  = np.zeros(len(ne_values))
        sum_avg_gs   = np.zeros(len(ne_values))
        sum_avg_gd   = np.zeros(len(ne_values))
        sum_rel_c    = np.zeros(len(ne_values))
        sum_rel_gs   = np.zeros(len(ne_values))
        sum_rel_gd   = np.zeros(len(ne_values))
        hist_cen = []  # tutti i costi finali Centralized
        hist_gs = []  # tutti i costi finali Greedy static
        hist_gd = []  # tutti i costi finali Greedy dynamic

        print(f"\n=== Regime: {regime} ===")
        for run in range(NUM_RUNS):
            print(f" Run {run+1}/{NUM_RUNS}")
            for i, ne in enumerate(ne_values):
                # uno stato iniziale per ciascuna coppia (regime, ne, run)
                init_data = generate_data()

                # run matching OFF (static)
                h_off = run_simulation_event_based(init_data, ne, regime, do_greedy=False)
                # run matching ON (dynamic)
                h_on  = run_simulation_event_based(init_data, ne, regime, do_greedy=True)

                # media costi per epoca
                sum_avg_cen[i] += np.mean(h_off['central_cost'])
                sum_avg_gs[i]  += np.mean(h_off['greedy_cost'])
                sum_avg_gd[i]  += np.mean(h_on['greedy_cost'])

                # riallocazioni finali
                sum_rel_c[i]  += h_off['relocations'][-1]
                sum_rel_gs[i] += h_off['relocations_greedy'][-1]
                sum_rel_gd[i] += h_on['relocations_greedy'][-1]

                # accumulo costi finali per istogramma
                hist_cen.append(h_off['central_cost'][-1])
                hist_gs.append(h_off['greedy_cost'][-1])
                hist_gd.append(h_on['greedy_cost'][-1])

        # Calcolo delle medie
        m_avg_cen = sum_avg_cen / NUM_RUNS
        m_avg_gs  = sum_avg_gs  / NUM_RUNS
        m_avg_gd  = sum_avg_gd  / NUM_RUNS
        m_rel_c   = sum_rel_c   / NUM_RUNS
        m_rel_gs  = sum_rel_gs  / NUM_RUNS
        m_rel_gd  = sum_rel_gd  / NUM_RUNS

        # — Grafico 1: costo medio per epoca vs ne —
        plt.figure()
        plt.plot(ne_values, m_avg_cen, 'o-', label='Centralized ')
        plt.plot(ne_values, m_avg_gs,  'x--', label='MatchingAlg static ')
        plt.plot(ne_values, m_avg_gd,  's-.', label='MatchingAlg dynamic ')
        plt.title(f"Costo totale  (epoca vs ne) – {regime}")
        plt.xlabel('ne (eventi per epoca)')
        plt.ylabel('Costo medio per epoca')
        plt.legend()
        plt.grid(True)

        # — Grafico 2: ne vs numero di riallocazioni —
        plt.figure()
        plt.plot(ne_values, m_rel_c,  'o-', label='Centralized')
        plt.plot(ne_values, m_rel_gs, 'x--', label='MatchingAlg static')
        plt.plot(ne_values, m_rel_gd, 's-.', label='MatchingAlg dynamic')
        plt.title(f"Riallocazioni vs ne – {regime}")
        plt.xlabel('ne (eventi per epoca)')
        plt.ylabel('Numero  di riallocazioni')
        plt.legend()
        plt.grid(True)

        # — Grafico 3: istogramma probabilità costi totali —
        plt.figure()
        mn, mx = min(hist_cen + hist_gs + hist_gd), max(hist_cen + hist_gs + hist_gd)
        plt.hist(hist_cen, bins=30, range=(mn, mx),
                 density=True, alpha=0.6, label='Centralized')
        plt.hist(hist_gs, bins=30, range=(mn, mx),
                 density=True, alpha=0.6, label='Greedy static')
        plt.hist(hist_gd, bins=30, range=(mn, mx),
                 density=True, alpha=0.6, label='Greedy dynamic')
        plt.title(f"Distribuzione costi finali – {regime}")
        plt.xlabel('Costo totale')
        plt.ylabel('PDF')
        plt.xlim(mn, mx)
        plt.legend()
        plt.grid(True)

    plt.show()

if __name__ == '__main__':
    main()
