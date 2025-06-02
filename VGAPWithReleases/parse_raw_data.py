import csv
import random
from collections import defaultdict

with open("cluster_h_first10min.csv") as f:
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

MIDWAY_POINT = 900000000

# remove heavy machiens
concated_instances = {i: concated_instances[i] for i in concated_instances if concated_instances[i]['max_cpus'] <= 0.5 and concated_instances[i]['max_memory'] <= 0.5 }

first_half =  {i: concated_instances[i] for i in concated_instances if int(concated_instances[i]['end_time']) < MIDWAY_POINT}
second_half = {i: concated_instances[i] for i in concated_instances if int(concated_instances[i]['start_time']) > MIDWAY_POINT}

random_first_half = random.sample(list(first_half.values()), 1000)
random_second_half = random.sample(list(second_half.values()), 1000)

for inst in random_first_half:
    inst["value"] = random.randint(1, 100)

for inst in random_second_half:
    inst["value"] = random.randint(1, 100)

with open("first_five_minutes.csv", "w") as f:
    writer = csv.DictWriter(f, random_first_half[0].keys())
    writer.writeheader()
    writer.writerows(random_first_half)

with open("second_five_minutes.csv", "w") as f:
    writer = csv.DictWriter(f, random_second_half[0].keys())
    writer.writeheader()
    writer.writerows(random_second_half)

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
