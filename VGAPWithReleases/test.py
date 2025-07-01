import os
import json
import matplotlib.pyplot as plt
import shutil
import csv
from pathlib import Path
from newAlgs import VGAPWD, VMKPSD
from members import Machine, Client
from OKPDAlgs import WCOAlg, GreedyAlg, Design1Alg, Design2Alg, DataDrivenAlg
from simpleAlgs import FirstFitAlg, BestFitAlg, RandomOrderAlg, WorstFitAlg
from optAlg import OPTAlg

from parse_raw_data import create_random_test_sample
from consts import *

GOOGLE_CLUSTERS_TIME_INTERVAL = 1_000_000
LOAD_RANDOM_DEMANDS = False
MACHINES = [Machine([1, 1]) for _ in range(5)]
OPT_ALG_NAME = "OPT"
NUM_INTERVALS = 10

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
    print(f"Saving the value {value} to {name}")
    with open(name, "w") as f:
        f.write(str(value))

# I'm running too many tests in parallel. This is a hacky solution to properly print the results when I want to
ALL_RESULTS_NAMES = ["Our alg", "Best fit", "First fit", "Worst fit", "Random order fit", "WCO", "Greedy", "Design 1", "Design 2", OPT_ALG_NAME, "VMKPSD", "DOA"]
def print_all_results(res_dir="."):
    curr_dir = Path(res_dir)
    for name in ALL_RESULTS_NAMES:
        with open(curr_dir / name) as f:
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


def handle_cls_context(cls, name, *args):
    instance = cls(*args)
    print(f"Calculating {name}")
    value = instance.calc_value()
    save_value(name, value)
    del instance
    return value


def run_all(history_csv, clients_csv, machines):
    with open(history_csv) as f:
        raw_data = csv.DictReader(f)
        history = [Client.from_csv_entry(entry, random_demands=LOAD_RANDOM_DEMANDS) for entry in raw_data]
        write_values("current_history.csv", history)

    with open(clients_csv) as f:
        raw_data = csv.DictReader(f)
        clients = [Client.from_csv_entry(entry, random_demands=LOAD_RANDOM_DEMANDS) for entry in raw_data]
        write_values("current_clients.csv", clients)

    print("Calculating our algs")
    vgapwd_val = handle_cls_context(VGAPWD, "Our alg", history, machines, clients, NUM_INTERVALS)
    vmkpsd_val = handle_cls_context(VMKPSD, "VMKPSD", history, machines, clients, NUM_INTERVALS)


    print("calculating simple")
    best_fit_val = handle_cls_context(BestFitAlg, "Best fit", machines, clients)
    first_fit_val = handle_cls_context(FirstFitAlg, "First fit", machines, clients)
    worst_fit_val = handle_cls_context(WorstFitAlg, "Worst fit", machines, clients)
    random_order_val = handle_cls_context(RandomOrderAlg, "Random order fit", machines, clients)

    print("calculating OKPD")
    wco_val = handle_cls_context(WCOAlg, "WCO", machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL)
    greedy_val = handle_cls_context(GreedyAlg, "Greedy", machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL)
    design1_val = handle_cls_context(Design1Alg, "Design 1", machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL)
    design2_val = handle_cls_context(Design2Alg, "Design 2", machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL)
    doa_val = handle_cls_context(DataDrivenAlg, "DOA", machines, clients, history, GOOGLE_CLUSTERS_TIME_INTERVAL)

    print("calculating opt")
    opt_val = handle_cls_context(OPTAlg, OPT_ALG_NAME, machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL)

    print_all_results()
    # return [vmkpsd_val, vgapwd_val, best_fit_val, first_fit_val, worst_fit_val, random_order_val, wco_val, greedy_val, design1_val, desi]


def move_results_to_dir(dir_name):
    dir_path = Path(dir_name)
    dir_path.mkdir(exist_ok=True, parents=True)
    for name in ALL_RESULTS_NAMES + ["current_clients.csv", "current_history.csv"]:
        shutil.move(name, dir_path / name)



def plot_results(dir_name):
    dir_path = Path(dir_name)
    values = []
    for name in ALL_RESULTS_NAMES:
        with open(dir_path / name) as f:
            values.append(float(f.read()))
    plt.bar(ALL_RESULTS_NAMES, values)
    plt.xlabel("Alg")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Value")
    plt.title(dir_name)

    plt.show()


def calc_competative_value(alg_name, base_dir="."):
    dir_path = Path(base_dir)
    with open(dir_path / alg_name) as f:
        alg_res = float(f.read())
    with open(dir_path / OPT_ALG_NAME) as f:
        opt_res = float(f.read())
    return alg_res / opt_res


def plot_relative_result(dir_name):
    values = []
    for name in ALL_RESULTS_NAMES:
        values.append(calc_competative_value(name, dir_name))
    bars = plt.bar(ALL_RESULTS_NAMES, values)
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Value")
    plt.title(dir_name)

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

def calc_average_competative_value(base_dir="."):
    all_subdirs = []
    for dirpath, dirnames, _ in os.walk(base_dir):
        all_subdirs.extend([os.path.join(dirpath, d) for d in dirnames])
    algs_value = {name: 0 for name in ALL_RESULTS_NAMES}
    for dir_name in all_subdirs:
        for name in ALL_RESULTS_NAMES:
            with open(Path(dir_name) / name) as f:
                algs_value[name] += float(f.read())
    return {v : algs_value[v] / algs_value[OPT_ALG_NAME] for v in algs_value}

def plot_average_competative_value(base_dir="."):
    algs_values = calc_average_competative_value(base_dir)
    bars = plt.bar(algs_values.keys(), algs_values.values())
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Value")
    plt.title(base_dir)

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

def run_test_with_theta(theta):
    BASE_CLUSTER_A_RES_PATH = Path(".").parent / f"Cluster A - theta {theta} - 300 instances"
    for i in range(1):
        print("Creating sample")
        while not create_random_test_sample(theta, 10):
            print("Sample size too small. Creating new sample")
        print("Running sample")
        run_all(HISTORY_FROM_CLUSTER_A, CLIENTS_FROM_CLUSTER_A, MACHINES)
        move_results_to_dir(BASE_CLUSTER_A_RES_PATH / f"run_{i}")

run_test_with_theta(10)