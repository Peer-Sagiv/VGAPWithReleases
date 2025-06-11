import json
import matplotlib.pyplot as plt
import shutil
import csv
from pathlib import Path
from newAlgs import VGAPWD, VMKPSD
from members import Machine, Client
from OKPDAlgs import WCOAlg, GreedyAlg, Design1Alg, Design2Alg
from simpleAlgs import FirstFitAlg, BestFitAlg, RandomOrderAlg, WorstFitAlg
from optAlg import OPTAlg

from consts import *

GOOGLE_CLUSTERS_TIME_INTERVAL = 1_000_000
LOAD_RANDOM_DEMANDS = False
MACHINES = [Machine([1, 1]) for _ in range(2)]

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
ALL_RESULTS_NAMES = ["Our alg", "Best fit", "First fit", "Worst fit", "Random order fit", "WCO", "Greedy", "Design 1", "Design 2", "OPT", "VMKPSD"]
def print_all_results(res_dir="."):
    curr_dir = Path(res_dir)
    for name in ALL_RESULTS_NAMES:
        with open(curr_dir / name) as f:
            print(f"{name} value is {f.read()}")


with open(HISTORY_FROM_CLUSTER_A) as f:
    raw_data = csv.DictReader(f)
    HISTORY_SET = [Client.from_csv_entry(entry, random_demands=LOAD_RANDOM_DEMANDS) for entry in raw_data]
    write_values("current_history.csv", HISTORY_SET)
    

with open(CLIENTS_FROM_CLUSTER_A) as f:
    raw_data = csv.DictReader(f)
    CLIENTS = [Client.from_csv_entry(entry, random_demands=LOAD_RANDOM_DEMANDS) for entry in raw_data]
    write_values("current_clients.csv", CLIENTS)


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


VMKPSD_res = handle_cls_context(VMKPSD, "VMKPSD", HISTORY_SET, MACHINES, CLIENTS)
alg_res = handle_cls_context(VGAPWD, "Our alg", HISTORY_SET, MACHINES, CLIENTS)


print("calculating simple")
best_fit_res = handle_cls_context(BestFitAlg, "Best fit", MACHINES, CLIENTS)
first_fit_res = handle_cls_context(FirstFitAlg, "First fit", MACHINES, CLIENTS)
worst_fit_res = handle_cls_context(WorstFitAlg, "Worst fit", MACHINES, CLIENTS)
random_res = handle_cls_context(RandomOrderAlg, "Random order fit", MACHINES, CLIENTS)

print("calculating OKPD")
wco_res = handle_cls_context(WCOAlg, "WCO", MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)
greedy_res = handle_cls_context(GreedyAlg, "Greedy", MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)
design_1_res = handle_cls_context(Design1Alg, "Design 1", MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)
design_2_res = handle_cls_context(Design2Alg, "Design 2", MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)

print("calculating opt")
opt_res = handle_cls_context(OPTAlg, "OPT", MACHINES, CLIENTS, GOOGLE_CLUSTERS_TIME_INTERVAL)

print_all_results()


def move_results_to_dir(dir_name):
    dir_path = Path(dir_name)
    dir_path.mkdir(exist_ok=True)
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
