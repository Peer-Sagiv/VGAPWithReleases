import copy
import random
from typing import List
from pulp import *
from members import Machine, Client
from consts import *

SLOTS = 2000
class VGAPWD:
    def __init__(self, history_set, machines: List['Machine'], clients: List['Client'], num_intervals, alpha = 0.5):
        self._slot_count = SLOTS
        self._clients: List['Client'] = copy.deepcopy(clients)
        self._current_clients_in_interval = []
        self._history_set = copy.deepcopy(history_set)
        self._dimension = len(clients[0].demands)
        self._num_intervals = num_intervals
        self._machines = machines
        self._current_assign_time = min(client.assign_time for client in self._clients) - 1
        self._value = 0
        self._alpha = alpha
        self._max_time_request = num_intervals * GOOGLE_CLUSTERS_TIME_INTERVAL
        self._current_index = 0
        self._current_random_index = 0
        self._pre_process_data()

    def _pre_process_data(self):
        self._history_set += [Client.unsatisfiable_client(self._dimension) for _ in range(self._slot_count * self._num_intervals - len(self._history_set))]

    def _get_history_set(self):
        # print(f"History set size is {len(self._history_set)}")
        chosen_history: List['Client'] = random.sample(self._history_set, self._num_intervals * self._slot_count)
        return [h for h in chosen_history if h.is_satisfible]
    
    def _pre_step_update_history(self, client: 'Client'):
        if client.assign_time > self._current_assign_time:
            # print("Creating new set of dummies")
            self._current_assign_time = client.assign_time
            self._current_clients_in_interval = [c for c in self._clients if c.assign_time == self._current_assign_time]
            self._random_sample_for_current_interval = random.sample(range(SLOTS), len(self._current_clients_in_interval))
            self._random_sample_for_current_interval.sort()
            self._current_index = 0
            self._current_random_index = 0
        
        prev_random_index = self._current_random_index
        self._current_random_index = self._random_sample_for_current_interval[self._current_index]
        self._current_index += 1
        number_of_dummies = self._current_random_index - prev_random_index
        # print(f"Number of dummies is {number_of_dummies}")
        self._history_set += [Client.unsatisfiable_client(self._dimension) for _ in range(number_of_dummies)]

    def step(self, client):
        self._pre_step_update_history(client)
        history_set: List['Client'] = self._get_history_set() + [client]
        for s in self._machines:
            s.flush(client)
        prob = LpProblem("MultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("x", ((c, s) for c in history_set for s in self._machines), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c, s)] for c in history_set for s in self._machines)

        for c in history_set:
            prob += lpSum(x[(c, s)] for s in self._machines) <= 1
        for s in self._machines:
            for d in range(self._dimension):
                prob += lpSum(c.demands[d] * ((c.departure_time - c.assign_time) / self._max_time_request) * x[(c, s)] for c in history_set) <= s.capacity(d) * self._alpha

        prob.solve(PULP_CBC_CMD(msg=0))
        probs = [(s, x[(client, s)].varValue) for s in self._machines]
        total = sum(p for _, p in probs) if probs else 0
        if total == 0:
            # print(f"Customer {client} is unassigned")
            assigned_machine = None
        else:
            normalized = [(s, p / total) for s, p in probs]
            slots, weights = zip(*normalized)
            assigned_machine = random.choices(slots, weights=weights)[0]
            # print(f"Customer {client} assigned to {assigned_machine} by randomized rounding")

        if assigned_machine and assigned_machine.check_feasible(client):
            self._value += client.value
            assigned_machine.assign(client)

    def calc_value(self):
        for m in self._machines:
            m.clear()
        self._clients.sort(key=lambda c:c.assign_time)
        for i, c in enumerate(self._clients):
            self.step(c)
            # print(f"Finished round {i}")
        return self._value


class VMKPSD(VGAPWD):
    def step(self, client):
        self._pre_step_update_history(client)
        history_set: List['Client'] = self._get_history_set() + [client]
        for s in self._machines:
            s.flush(client)
        prob = LpProblem("VectorMultipleKnapsackWithDepartures", LpMaximize)

        x = LpVariable.dicts("y", ((c) for c in history_set), lowBound=0, upBound=1)
        prob += lpSum(c.value * x[(c)] for c in history_set)

        for d in range(self._dimension):
            prob += lpSum(c.demands[d] * ((c.departure_time - c.assign_time) / self._max_time_request) * x[(c)] for c in history_set) <= len(self._machines)
        
        prob.solve(PULP_CBC_CMD(msg=0))
        probability = x[(client)].varValue
        if probability < random.random():
            # print(f"Customer {client} is unassigned")
            return
        for s in self._machines:
            if s.check_feasible(client):
                s.assign(client)
                self._value += client.value
                # print(f"Customer {client} assigned to {s} by randomized rounding")
                return
        # print(f"Customer {client} is unassigned due to no free machines")
