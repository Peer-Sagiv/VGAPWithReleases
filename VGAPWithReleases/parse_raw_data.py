import csv
import random
from collections import defaultdict
from consts import *

A_RUNS = "runs_from_cluster_a.csv"
H_RUNS = "cluster_h_first10min.csv"
THETA = 50

SECOND = 1_000

with open(A_RUNS) as f:
    raw_data = csv.DictReader(f)
    parsed_data = [row for row in raw_data]

instances = defaultdict(lambda: [])
for inst in parsed_data:
    if inst['max_cpus'] and float(inst['max_cpus']) > 0 and inst['max_memory'] and float(inst['max_memory']) > 0:
        instances[inst["instance_index"], inst["collection_id"], inst['machine_id']].append(inst)

def get_concated_instance(inst):
    inst.sort(key=lambda x: int(x['start_time']))
    ordered_inst = {}
    for key in inst[0]:
        ordered_inst[key] = inst[0][key]
    ordered_inst['max_cpus'] = float(ordered_inst['max_cpus'])
    ordered_inst['max_memory'] = float(ordered_inst['max_memory'])
    last_entry = inst[0]
    for entry in inst:
        if entry == last_entry:
            continue
        if entry['start_time'] != ordered_inst['end_time']:
            # We refer to it as a broken entry. Ignore it
            return None
        last_entry = entry
        ordered_inst['end_time'] = entry['end_time']
        ordered_inst['max_cpus'] = max(float(ordered_inst['max_cpus']), float(entry['max_cpus']))
        ordered_inst['max_memory'] = max(float(ordered_inst['max_memory']), float(entry['max_memory']))
    return ordered_inst

concated_instances = {}

for raw_instance_key in instances:
    ordered_intance = get_concated_instance(instances[raw_instance_key])
    if ordered_intance:
        concated_instances[raw_instance_key] = ordered_intance

min_start_time = min([int(i['start_time']) for i in concated_instances.values()])
max_end_time = max([int(i['end_time']) for i in concated_instances.values()])


# remove heavy machiens
concated_instances = {i: concated_instances[i] for i in concated_instances if concated_instances[i]['max_cpus'] <= 0.5 and concated_instances[i]['max_memory'] <= 0.5 }

"""
Getting random instances by size
"""
# MIDWAY_POINT = 900000000
# first_half =  {i: concated_instances[i] for i in concated_instances if int(concated_instances[i]['end_time']) <= MIDWAY_POINT}
# second_half = {i: concated_instances[i] for i in concated_instances if int(concated_instances[i]['start_time']) > MIDWAY_POINT}

# first_half_values = list(first_half.values())
# second_half_values = list(second_half.values())

# first_half_values.sort(key=lambda x: int(x['start_time']))
# second_half_values.sort(key=lambda x: int(x['start_time']))

# random_first_half = random.sample(list(first_half.values()), 1000)
# random_second_half = random.sample(list(second_half.values()), 1000)

# for inst in first_half_values:
#     inst["value"] = random.randint(1, 1000)

# for inst in second_half_values:
#     inst["value"] = random.randint(1, 1000)

# with open("first_five_minutes.csv", "w") as f:
#     writer = csv.DictWriter(f, first_half_values[0].keys())
#     writer.writeheader()
#     writer.writerows(first_half_values[:1000])

# with open("second_five_minutes.csv", "w") as f:
#     writer = csv.DictWriter(f, second_half_values[0].keys())
#     writer.writeheader()
#     writer.writerows(second_half_values[:1000])

# with open("first_five_minutes_random.csv", "w") as f:
#     writer = csv.DictWriter(f, first_half_values[0].keys())
#     writer.writeheader()
#     writer.writerows(random_first_half)

# with open("second_five_minutes_random.csv", "w") as f:
#     writer = csv.DictWriter(f, second_half_values[0].keys())
#     writer.writeheader()
#     writer.writerows(random_first_half)


def get_instance_by_start_time(instances):
    instances_by_time = defaultdict(lambda: 0)
    for i in instances:
        instances_by_time[instances[i]['start_time']] += 1
    return instances_by_time
    



"""
Getting values by duration
"""
GOOGLE_CLUSTERS_TIME_INTERVAL = 1_000_000
REQUIRED_INTERVAL = 10 * GOOGLE_CLUSTERS_TIME_INTERVAL
first_interval = {i: concated_instances[i] for i in concated_instances if int(concated_instances[i]['start_time']) <= min_start_time + REQUIRED_INTERVAL}
second_interval = {i: concated_instances[i] for i in concated_instances if min_start_time + REQUIRED_INTERVAL < int(concated_instances[i]['start_time']) <= min_start_time + REQUIRED_INTERVAL * 2}

first_interval_values = list(first_interval.values())
second_interval_values = list(second_interval.values())

first_interval_values.sort(key=lambda x: int(x['start_time']))
second_interval_values.sort(key=lambda x: int(x['start_time']))

def fix_max_end_time(values, max_end_time):
    for value in values:
        if int(value['end_time']) > max_end_time:
            value['end_time'] = max_end_time

fix_max_end_time(first_interval_values, min_start_time + REQUIRED_INTERVAL)
fix_max_end_time(second_interval_values, min_start_time + REQUIRED_INTERVAL * 2)

# After fixing the times, we are left with assignments which may start and end at the same time. Remove them
first_interval_values = [value for value in first_interval_values if int(value['start_time']) != int(value['end_time'])]
second_interval_values = [value for value in second_interval_values if int(value['start_time']) != int(value['end_time'])]

def get_history_and_online_set(first_values, second_values):
    """
    The history set must be bigger than the online set
    """
    if len(first_values) > len(second_values):
        return first_values, second_values
    return second_values, first_values

history_set, online_set = get_history_and_online_set(first_interval_values, second_interval_values)


def give_value_by_theta(inst, theta):
    inst_d = (int(inst['end_time']) - int(inst['start_time'])) / GOOGLE_CLUSTERS_TIME_INTERVAL
    # TODO: Random int? Why not random float?
    inst["value"] = random.randint(1, theta) * (inst['max_memory'] + inst['max_cpus']) * inst_d

for inst in history_set:
    give_value_by_theta(inst, THETA)

for inst in online_set:
    give_value_by_theta(inst, THETA)


with open(HISTORY_FROM_CLUSTER_A, "w") as f:
    writer = csv.DictWriter(f, history_set[0].keys())
    writer.writeheader()
    writer.writerows(history_set)

with open(CLIENTS_FROM_CLUSTER_A, "w") as f:
    writer = csv.DictWriter(f, online_set[0].keys())
    writer.writeheader()
    writer.writerows(online_set)

# Ensure the instances intersect
def count_intersections(intervals):
    events = []
    for i, interval in enumerate(intervals):
        events.append((interval["start_time"], "start"))
        events.append((interval["end_time"], "end"))

    events.sort(key=lambda x: (x[0], 0 if x[1] == "start" else 1))

    active = 0
    intersections = 0

    for time, event_type in events:
        if event_type == "start":
            intersections += active
            active += 1
        else:
            active -= 1

    return intersections

def get_average_duration(demands):
    return sum([int(v['end_time']) - int(v['start_time']) for v in demands]) / len(demands)
