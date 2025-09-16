import sys
import json
#import matplotlib.pyplot as plt
import shutil
import csv
from collections import defaultdict
from pathlib import Path
from newAlgs import VGAPWD, VMKPSD, VMKPSDWH, GreedyVGAPWD, GreedyVMKPSD, GreedyVMKPSDNoInfo
from members import Machine
from OKPDAlgs import WCOAlg, GreedyAlg, Design1Alg, Design2Alg, DataDrivenAlg, GammaOfflineAlg
from simpleAlgs import FirstFitAlg, BestFitAlg, RandomOrderAlg, WorstFitAlg
from optAlg import OPTAlg

from parse_raw_data import create_random_test_sample
from parse_azure_data import process_azure_data
from consts import *

import argparse

GOOGLE_CLUSTERS_TIME_INTERVAL = 1_000_000
LOAD_RANDOM_DEMANDS = False
TESTS_PER_TARGET = 10

# with open("clean_1000_rounds_valued.json") as f:
#     rounds = json.load(f)
#     CLIENTS = [Client.from_json_entry(entry) for entry in rounds]

# with open("clean_1000_history_valued.json") as f:
#     rounds = json.load(f)
#     HISTORY_SET = [Client.from_json_entry(entry) for entry in rounds]

def write_values(name, clients):
    values = [c.to_dict() for c in clients]
    with open(name, "w") as f:
        writer = csv.DictWriter(f, values[0].keys())
        writer.writeheader()
        writer.writerows(values)

def save_value(name, value):
    with open(name, "w") as f:
        f.write(str(value))

def print_all_results(res_dir="."):
    curr_dir = Path(res_dir)
    for name in ALGS_NAMES:
        curr_res: Path = curr_dir / name
        if curr_res.exists():
            with open(curr_res) as f:
                print(f"{name} value is {f.read()}")


# """
# Load from existing random round
# """
# with open("current_history.csv") as f:
#     raw_data = csv.DictReader(f)
#     HISTORY_SET = [Client.from_presaved_entry(entry) for entry in raw_data]


# with open("current_clients.csv") as f:
#     raw_data = csv.DictReader(f)
#     CLIENTS = [Client.from_presaved_entry(entry) for entry in raw_data]


def handle_cls_context(cls, name, *args, log_results=False):
    instance = cls(*args)
    # print(f"Calculating {name}")
    value = instance.calc_value()
    if log_results:
        save_value(name, value)
    del instance
    return value

def get_test_sample_from_source(theta, required_time, history_time, pareto_alpha, azure=False, parallel=False):
    if azure:
        return process_azure_data(theta, required_time, history_time, pareto_alpha, parallel_time=parallel)
    return create_random_test_sample(theta, required_time, history_time, pareto_alpha)


def run_all(large_history, clients, machines, run_simple_alg=False, log_results=False, alpha=None):


    history, older_history = large_history.get_latest_from_window(clients.length)

    values = {}
    # print("Calculating our algs")
    # if run_simple_alg:
    #     values[VGAPWD_NAME] = handle_cls_context(VGAPWD, VGAPWD_NAME, history, machines, clients, log_results=log_results)
    # values[VMKPSD_NAME] = handle_cls_context(VMKPSD, VMKPSD_NAME, history, machines, clients, 0.5, log_results=log_results)
    # values[VMKPSDWH_NAME] = handle_cls_context(VMKPSDWH, VMKPSDWH_NAME, large_history, history, machines, clients, log_results=log_results)

    if run_simple_alg:
        values[GREEDY_VGAPWD_NAME] = handle_cls_context(GreedyVGAPWD, GREEDY_VGAPWD_NAME, history, machines, clients, alpha, log_results=log_results)

    values[GREEDY_VMKPSD_NAME] = handle_cls_context(GreedyVMKPSD, GREEDY_VMKPSD_NAME, history, machines, clients, alpha, log_results=log_results)
    values[GREEDY_VMKPSD_NO_INFO_NAME] = handle_cls_context(GreedyVMKPSDNoInfo, GREEDY_VMKPSD_NO_INFO_NAME, older_history, machines, clients, alpha, log_results=log_results)

    # print("calculating simple")
    values[BEST_FIT_NAME] = handle_cls_context(BestFitAlg, BEST_FIT_NAME, machines, clients, log_results=log_results)
    values[FIRST_FIT_NAME] = handle_cls_context(FirstFitAlg, FIRST_FIT_NAME, machines, clients, log_results=log_results)
    values[WORST_FIT_NAME] = handle_cls_context(WorstFitAlg, WORST_FIT_NAME, machines, clients, log_results=log_results)
    values[RANDOM_ORDER_NAME] = handle_cls_context(RandomOrderAlg, RANDOM_ORDER_NAME, machines, clients, log_results=log_results)

    # print("calculating OKPD")
    values[WCO_NAME] = handle_cls_context(WCOAlg, WCO_NAME, machines, clients, log_results=log_results)
    values[GREEDY_NAME] = handle_cls_context(GreedyAlg, GREEDY_NAME, machines, clients, log_results=log_results)
    values[DESIGN_1_NAME] = handle_cls_context(Design1Alg, DESIGN_1_NAME, machines, clients, log_results=log_results)
    values[DESIGN_2_NAME] = handle_cls_context(Design2Alg, DESIGN_2_NAME, machines, clients, log_results=log_results)
    values[DATA_DRIVEN_NAME] = handle_cls_context(DataDrivenAlg, DATA_DRIVEN_NAME, machines, clients, history, log_results=log_results)
    values[GAMMA_OFFLINE_NAME] = handle_cls_context(GammaOfflineAlg, GAMMA_OFFLINE_NAME, machines, clients, history, log_results=log_results)

    # print("calculating opt")
    values[OPT_NAME] = handle_cls_context(OPTAlg, OPT_NAME, machines, clients, log_results=log_results)

    if log_results:
        print_all_results(values)

    return values

def move_results_to_dir(dir_name):
    dir_path = Path(dir_name)
    dir_path.mkdir(exist_ok=True, parents=True)
    for name in ALGS_NAMES:
        shutil.move(name, dir_path / name)


def plot_results(results_path):
    with open(results_path) as f:
        values = (json.load(f))
    plt.bar(values.keys(), values.values())
    plt.xlabel("Alg")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Value")
    plt.title(results_path.parent.name)

    plt.show()


def plot_relative_result(results_path):
    values = []
    with open(results_path) as f:
        raw_values = (json.load(f))
    for v in raw_values:
        values.append(raw_values[v] / raw_values[OPT_NAME])
    bars = plt.bar(raw_values.keys(), values)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Value")
    plt.title(results_path.parent.name)

    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}",
            ha='center', va='bottom'
        )

    plt.tight_layout()
    plt.show()

import math
import argparse
import json
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Run algorithm tests with specified parameters.")

    parser.add_argument("theta", type=int, help="Theta parameter")
    parser.add_argument("required_time_online", type=int, help="Required time for online computations")
    parser.add_argument("required_time_history", type=int, help="Required time for history window")
    parser.add_argument("required_time_older_history", type=int, help="Required time for older history window")
    parser.add_argument("num_machines", type=int, help="Number of machines to simulate (overridden if --load is set)")
    parser.add_argument("machine_size", type=float, help="Size parameter for machines")
    parser.add_argument(
        "dimensions", type=int, nargs="?", default=2,
        help="Number of dimensions for machine resource vector (default: 2)"
    )
    parser.add_argument("run_simple_alg", type=lambda x: x.lower() == "true", help="Run simple algorithms (true/false)")
    parser.add_argument("log_results", type=lambda x: x.lower() == "true", help="Log results (true/false)")
    parser.add_argument("name", type=str, help="Name for results directory")
    parser.add_argument("trial", type=int, help="Trial iteration number")
    parser.add_argument("--pareto_alpha", type=float, default=None,
                        help="Pareto alpha parameter (optional)")
    parser.add_argument("--load", type=float, default=None,
                        help="Requested load (optional). Overrides num_machines based on clients max load.")
    parser.add_argument("--azure", type=bool, default=False,
                        help="Load azure data.")
    parser.add_argument("--parallel", type=bool, default=False,
                        help="Use parallel history (Azure only).")
    
    parser.add_argument("--learn-phase", type=bool, default=False,
                        help="Create data for the learning phase, to lear the best alpha.")
    
    args = parser.parse_args()

    results_dir = Path(args.name)
    results_dir.mkdir(exist_ok=True, parents=True)
    curr_res_path = results_dir / f"run_{args.trial}"

    total_history = args.required_time_history + args.required_time_older_history
    large_history, clients = get_test_sample_from_source(
        args.theta,
        args.required_time_online,
        total_history,
        args.pareto_alpha,
        args.azure,
        args.parallel
    )
    while large_history is None:
        print("Sample too small. Retrying...")
        large_history, clients = get_test_sample_from_source(
            args.theta,
            args.required_time_online,
            total_history,
            args.pareto_alpha,
            args.azure,
            args.parallel
        )

    history, older_history = large_history.get_latest_from_window(args.required_time_history)

    # Determine number of machines based on load if --load provided
    num_machines = args.num_machines
    if args.load is not None:
        # Compute peak load from clients in the history window

        print("max_demands=", clients.get_max_total_demand())
        print("avg_demands=", clients.get_avg_demand())
        max_demand = max(clients.get_max_total_demand())
        avg_demand = max(clients.get_avg_demand())
        print("max_demand=", max_demand)
        print("avg_demand=", avg_demand)

        # Compute required machines to get requested load
        required_machines_max_demand = math.floor(max_demand / (args.machine_size * args.load))
        required_machines_avg_demand = math.floor(avg_demand / (args.machine_size * args.load))


        print("required_machines_max_demand=", required_machines_max_demand)
        print("required_machines_avg_demand=", required_machines_avg_demand)


        required_machines = required_machines_avg_demand

        if required_machines < 1:
            required_machines = 1  # At least one machine needed

        num_machines = required_machines

        print(f"Computed number of machines needed for load {args.load}: {num_machines}")

    # Create machines using final num_machines
    machines = [Machine([args.machine_size] * args.dimensions) for _ in range(num_machines)]

    if args.learn_phase:
        for alpha in TRAIN_ALPHA_VALUES:
            results = run_all(
                large_history,
                clients,
                machines,
                run_simple_alg=args.run_simple_alg,
                alpha=alpha,
                log_results=args.log_results
            )

            with open(curr_res_path / f"alpha_{alpha}", "w") as f:
                json.dump(results, f)

            print(f"Results saved to {curr_res_path}")

    else:
        results = run_all(
            large_history,
            clients,
            machines,
            run_simple_alg=args.run_simple_alg,
            log_results=args.log_results
        )

        with open(curr_res_path, "w") as f:
            json.dump(results, f)

        print(f"Results saved to {curr_res_path}")

if __name__ == "__main__":
    main()

