import csv
import random
from collections import defaultdict
from consts import *
from members import Client

def get_concated_instance(inst):
    ordered_inst = {}
    for key in inst[0]:
        ordered_inst[key] = inst[0][key]
    ordered_inst['max_cpus'] = float(ordered_inst['max_cpus'])
    ordered_inst['max_memory'] = float(ordered_inst['max_memory'])
    ordered_inst['start_time'] = int(ordered_inst['start_time'])
    ordered_inst['end_time'] = int(ordered_inst['end_time'])
    for entry in inst:
        ordered_inst['start_time'] = min(ordered_inst['start_time'], int(entry['start_time']))
        ordered_inst['end_time'] = max(ordered_inst['end_time'], int(entry['end_time']))
        ordered_inst['max_cpus'] = max(ordered_inst['max_cpus'], float(entry['max_cpus']))
        ordered_inst['max_memory'] = max(ordered_inst['max_memory'], float(entry['max_memory']))
    return ordered_inst


def get_instance_by_start_time(instances):
    instances_by_time = defaultdict(lambda: 0)
    for i in instances:
        instances_by_time[instances[i]['start_time']] += 1
    return instances_by_time


def fix_max_end_time(values, time_interval):
    for value in values:
        if int(value['end_time']) - int(value['start_time']) > time_interval:
            value['end_time'] = int(value['start_time']) + time_interval

def get_history_and_online_set(first_values, second_values):
    """
    The history set must be bigger than the online set
    """
    if len(first_values) > len(second_values):
        return first_values, second_values
    return second_values, first_values

def give_value_by_theta(inst, theta):
    inst_d = (int(inst['end_time']) - int(inst['start_time'])) / GOOGLE_CLUSTERS_TIME_INTERVAL
    # TODO: Random int? Why not random float?
    inst["value"] = random.randint(1, theta) * (inst['max_memory'] + inst['max_cpus']) * inst_d

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

def create_random_test_sample(theta, required_time):
    required_interval_time = required_time * GOOGLE_CLUSTERS_TIME_INTERVAL
    max_query_interval = ((QUERY_END_TIME - QUERY_START_TIME) // GOOGLE_CLUSTERS_TIME_INTERVAL) - 3 * required_time

    with open(COMBINED_A_RUNS) as f:
        raw_data = csv.DictReader(f)
        parsed_data = [row for row in raw_data]

    instances = defaultdict(lambda: [])
    for inst in parsed_data:
        if inst['max_cpus'] and inst['max_memory'] and (float(inst['max_cpus']) > 0  or float(inst['max_memory']) > 0):
            instances[inst["instance_index"], inst["collection_id"]].append(inst)

    concated_instances = {}
    
    for raw_instance_key in instances:
        ordered_intance = get_concated_instance(instances[raw_instance_key])
        if ordered_intance:
            concated_instances[raw_instance_key] = ordered_intance

    # Select a random time to derive the history and online set from
    current_query_time = random.randint(1, max_query_interval) * GOOGLE_CLUSTERS_TIME_INTERVAL + QUERY_START_TIME

    # remove heavy machiens
    concated_instances = {i: concated_instances[i] for i in concated_instances if concated_instances[i]['max_cpus'] <= 0.5 and concated_instances[i]['max_memory'] <= 0.5}

    first_interval = {i: concated_instances[i] for i in concated_instances if current_query_time <= int(concated_instances[i]['start_time']) < current_query_time + required_interval_time}
    second_interval = {i: concated_instances[i] for i in concated_instances if current_query_time + required_interval_time <= int(concated_instances[i]['start_time']) < current_query_time + required_interval_time * 2}

    first_interval_values = list(first_interval.values())
    second_interval_values = list(second_interval.values())

    if len(first_interval_values) < MIN_SAMPLE_SIZE or len(second_interval_values) < MIN_SAMPLE_SIZE:
        return None, None 

    first_interval_values.sort(key=lambda x: int(x['start_time']))
    second_interval_values.sort(key=lambda x: int(x['start_time']))

    fix_max_end_time(first_interval_values, required_interval_time)
    fix_max_end_time(second_interval_values, required_interval_time)

    # After fixing the times, we are left with assignments which may start and end at the same time. Remove them
    first_interval_values = [value for value in first_interval_values if int(value['start_time']) != int(value['end_time'])]
    second_interval_values = [value for value in second_interval_values if int(value['start_time']) != int(value['end_time'])]
    history_set, online_set = first_interval_values, second_interval_values
    for inst in history_set:
        give_value_by_theta(inst, theta)

    for inst in online_set:
        give_value_by_theta(inst, theta)

    history = [Client.from_csv_entry(entry) for entry in history_set]
    clients = [Client.from_csv_entry(entry) for entry in online_set]

    return history, clients
