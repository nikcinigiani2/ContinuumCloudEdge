import matplotlib.pyplot as plt
from dataGenerator import generate_data
from simulation import run_simulation_event_based

def plot_allocations(ne_values, histories, regime, suffix):
    plt.figure()
    allocs = [h['alloc_events'][-1] for h in histories]
    plt.plot(ne_values, allocs, marker='o')
    plt.xlabel('ne (eventi per epoca)')
    plt.ylabel('Numero totale di allocazioni')
    plt.title(f'Allocazioni vs ne – {regime} ({suffix})')
    plt.grid(True)

def plot_costs(ne_values, histories, regime, suffix, comparison=False):
    plt.figure()
    central = [h['central_cost'][-1] for h in histories]
    plt.plot(ne_values, central, marker='o', label='Centralized')
    # disegno greedy **solo** se comparison=True
    if comparison:
        greedy = [h['greedy_cost'][-1] for h in histories]
        plt.plot(ne_values, greedy, marker='x', label='Greedy')
    plt.xlabel('ne (eventi per epoca)')
    plt.ylabel('Costo finale')
    plt.title(f'Costo vs ne – {regime} ({suffix})')
    if comparison:
        plt.legend()
    plt.grid(True)

def plot_histogram(histories, regime, suffix):
    plt.figure()
    all_costs = []
    for h in histories:
        all_costs.extend(h['central_cost'])
    plt.hist(all_costs, bins=30, alpha=0.7)
    plt.xlabel('Costo')
    plt.ylabel('Frequenza')
    plt.title(f'Distribuzione costi nel tempo – {regime} ({suffix})')
    plt.grid(True)

def main():
    regimes   = ['scarcity', 'abundance']
    ne_values = list(range(10, 101, 10))

    for regime in regimes:
        histories_c = []
        histories_b = []
        for ne in ne_values:
            init_data = generate_data()

            # solo centralized
            h_c = run_simulation_event_based(init_data, ne, regime, do_greedy=False)
            histories_c.append(h_c)

            # centralized + greedy
            h_b = run_simulation_event_based(init_data, ne, regime, do_greedy=True)
            histories_b.append(h_b)

        # Grafici per “solo Centralized”
        plot_allocations(ne_values, histories_c, regime, 'Centralized')
        plot_costs     (ne_values, histories_c, regime, 'Centralized', comparison=False)
        plot_histogram(histories_c, regime, 'Centralized')

        # Grafici per “Centralized vs Greedy”
        plot_allocations(ne_values, histories_b, regime, 'Comparison')
        plot_costs     (ne_values, histories_b, regime, 'Comparison', comparison=True)
        plot_histogram(histories_b, regime, 'Comparison')

    plt.show()

if __name__ == '__main__':
    main()
