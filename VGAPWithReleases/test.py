import sys
import json
import matplotlib.pyplot as plt
import shutil
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from collections import defaultdict
from pathlib import Path
from newAlgs import VGAPWD, VMKPSD
from members import Machine
from OKPDAlgs import WCOAlg, GreedyAlg, Design1Alg, Design2Alg, DataDrivenAlg, GammaOfflineAlg
from simpleAlgs import FirstFitAlg, BestFitAlg, RandomOrderAlg, WorstFitAlg
from optAlg import OPTAlg

from parse_raw_data import create_random_test_sample
from consts import *

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


def run_all(history, clients, machines, required_time, run_simple_alg=False, log_results=False):
    values = {}
    # print("Calculating our algs")
    if run_simple_alg:
        values[VGAPWD_NAME] = handle_cls_context(VGAPWD, VGAPWD_NAME, history, machines, clients, required_time, log_results=log_results)
    values[VMKPSD_NAME] = handle_cls_context(VMKPSD, VMKPSD_NAME, history, machines, clients, required_time, log_results=log_results)


    # print("calculating simple")
    values[BEST_FIT_NAME] = handle_cls_context(BestFitAlg, BEST_FIT_NAME, machines, clients, log_results=log_results)
    values[FIRST_FIT_NAME] = handle_cls_context(FirstFitAlg, FIRST_FIT_NAME, machines, clients, log_results=log_results)
    values[WORST_FIT_NAME] = handle_cls_context(WorstFitAlg, WORST_FIT_NAME, machines, clients, log_results=log_results)
    values[RANDOM_ORDER_NAME] = handle_cls_context(RandomOrderAlg, RANDOM_ORDER_NAME, machines, clients, log_results=log_results)

    # print("calculating OKPD")
    values[WCO_NAME] = handle_cls_context(WCOAlg, WCO_NAME, machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)
    values[GREEDY_NAME] = handle_cls_context(GreedyAlg, GREEDY_NAME, machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)
    values[DESIGN_1_NAME] = handle_cls_context(Design1Alg, DESIGN_1_NAME, machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)
    values[DESIGN_2_NAME] = handle_cls_context(Design2Alg, DESIGN_2_NAME, machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)
    values[DATA_DRIVEN_NAME] = handle_cls_context(DataDrivenAlg, DATA_DRIVEN_NAME, machines, clients, history, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)
    values[GAMMA_OFFLINE_NAME] = handle_cls_context(GammaOfflineAlg, GAMMA_OFFLINE_NAME, machines, clients, history, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)

    # print("calculating opt")
    values[OPT_NAME] = handle_cls_context(OPTAlg, OPT_NAME, machines, clients, GOOGLE_CLUSTERS_TIME_INTERVAL, log_results=log_results)

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

# def calc_average_competative_value(base_dir="."):
#     all_subdirs = []
#     for dirpath, dirnames, _ in os.walk(base_dir):
#         all_subdirs.extend([os.path.join(dirpath, d) for d in dirnames])
#     algs_value = {name: 0 for name in ALL_RESULTS_NAMES}
#     for dir_name in all_subdirs:
#         for name in ALL_RESULTS_NAMES:
#             with open(Path(dir_name) / name) as f:
#                 algs_value[name] += float(f.read())
#     return {v : algs_value[v] / algs_value[OPT_ALG_NAME] for v in algs_value}

# def plot_average_competative_value(base_dir="."):
#     algs_values = calc_average_competative_value(base_dir)
#     bars = plt.bar(algs_values.keys(), algs_values.values())
#     plt.xticks(rotation=45, ha='right')
#     plt.ylabel("Value")
#     plt.title(base_dir)

#     for bar in bars:
#         height = bar.get_height()
#         plt.text(
#             bar.get_x() + bar.get_width() / 2,
#             height,
#             f"{height:.2f}",
#             ha='center', va='bottom'
#         )

#     plt.tight_layout()
#     plt.show()

def run_test(theta, required_time, num_machines, run_simple_alg, log_results, name):
    results_dir = Path(".") / name
    results_dir.mkdir(exist_ok=True, parents=True)
    test_result = defaultdict(lambda: 0)
    machines = [Machine([1, 1]) for _ in range(num_machines)]
    for i in range(TESTS_PER_TARGET):
        curr_res_path = results_dir / f"run_{i + 1}"
        # print("Creating sample")
        history, clients = create_random_test_sample(theta, required_time)
        while history is None:
            # print("Sample size too small. Creating new sample")
            history, clients = create_random_test_sample(theta, required_time)
        # print("Running sample")
        results = run_all(history, clients[:10], machines[:10], required_time, run_simple_alg=run_simple_alg, log_results=log_results)
        with open(curr_res_path, "w") as f:
            json.dump(results, f)
        for res in results:
            test_result[res] += results[res]
    final_res_path = results_dir / f"final"
    with open(final_res_path, "w") as f:
        json.dump(final_res_path, f)

theta = int(sys.argv[1])
required_time = int(sys.argv[2])
num_machines = int(sys.argv[3])
run_simple_alg = sys.argv[4].lower() == "true"
log_results = sys.argv[5].lower() == "true"
name = sys.argv[6]
trial = int(sys.argv[7])

results_dir = Path(name)
results_dir.mkdir(exist_ok=True, parents=True)
curr_res_path = results_dir / f"run_{trial}"

machines = [Machine([1, 1]) for _ in range(num_machines)]

# print("Creating sample")
history, clients = create_random_test_sample(theta, required_time)
while history is None:
    # print("Sample too small. Retrying...")
    history, clients = create_random_test_sample(theta, required_time)

# print("Running sample")
results = run_all(history, clients, machines, required_time, run_simple_alg=run_simple_alg, log_results=log_results)

with open(curr_res_path, "w") as f:
    json.dump(results, f)
