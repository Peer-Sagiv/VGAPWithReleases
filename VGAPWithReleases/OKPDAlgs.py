import math
import numpy as np
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .members import Machine, Client


class OKPDAlgBase:
    def __init__(self, machines:List['Machine'], clients: List['Client'], time_slot_interval):
        self._machines = machines
        self._value = 0
        self._clients: List['Client'] = clients
        self._time_slot_interval = time_slot_interval
        self._min_assign_time, self._max_departure_time = self._get_time_slots_edges()
        self._alpha = self._calc_alpha()
        self._theta = self._calc_theta()
        self._utilization = {m : [[0 for _ in range(self._min_assign_time, self._max_departure_time, self._time_slot_interval)] for _ in range(m.dimensions())] for m in self._machines}
    
    def _threshold_function(self, z, capacity, slot_duration):
        raise NotImplemented()
    
    def _get_time_slots_edges(self):
        max_departure_time = max([c.departure_time for c in self._clients])
        min_assign_time = min([c.assign_time for c in self._clients])
        return min_assign_time, max_departure_time

    def _calc_theta(self):
        theta = None
        for c in self._clients:
            c_theta = c.value / (sum(c.demands) * ((c.departure_time -  c.assign_time) / self._time_slot_interval))
            if not theta or c_theta > theta:
                theta = c_theta
        return c_theta

    def _calc_alpha(self):
        alpha = None
        for c in self._clients:
            c_alpha = (c.departure_time -  c.assign_time) / self._time_slot_interval
            if not alpha or c_alpha > alpha:
                alpha = c_alpha
        return c_alpha

    def _get_client_timeslots(self, client: 'Client'):
        return range((client.assign_time - self._min_assign_time) // self._time_slot_interval,
                     (client.departure_time - self._min_assign_time) // self._time_slot_interval)
    
    def _get_client_slots_duration(self, client: 'Client'):
        return client.departure_time / self._time_slot_interval - client.assign_time / self._time_slot_interval

    def _calc_sum_threshhold(self, machine: 'Machine', client: 'Client'):
        machine_utilization = self._utilization[machine]
        client_timeslots = self._get_client_timeslots(client)

        utilization = 0
        for timeslot in client_timeslots:
            for d in range(machine.dimensions()):
                utilization += self._threshold_function(machine_utilization[d][timeslot], machine.capacity(d), self._get_client_slots_duration(client)) * client.demands[d]
        return utilization
    
    def _update_utilization(self, machine: 'Machine', client: 'Client'):
        utilization = self._utilization[machine]
        for d in range(machine.dimensions()):
            for timeslot in self._get_client_timeslots(client):
                utilization[d][timeslot] + client.demands[d]

    def step(self, client: 'Client'):
        possible_machines = []
        for m in self._machines:
            m.flush(client)
            if m.check_feasible(client):
                if self._calc_sum_threshhold(m, client) <= client.value:
                    possible_machines.append(m)
        # TODO: Is it ok to always pick the first machine?
        if possible_machines:
            chosen_machine = possible_machines[0]
            self._update_utilization(chosen_machine, client)
            chosen_machine.assign(client)
            self._value += client.value

    def calc_value(self):
        self._clients.sort(key=lambda c:c.assign_time)
        for m in self._machines:
            m.clear()
        for c in self._clients:
            self.step(c)
        return self._value

class GreedyAlg(OKPDAlgBase):
    def _threshold_function(self, z, capacity, slot_duration):
        return 1

class Design1Alg(OKPDAlgBase):
    def _threshold_function(self, z, capacity, slot_duration):
        if z < capacity / (1 + np.log(self._theta)):
            return 1
        return np.exp((1 + np.log(self._theta) * z ) / (capacity - 1))
    
class Design2Alg(OKPDAlgBase):
    def _threshold_function(self, z, capacity, slot_duration):
        return math.floor(2 ** (z * np.log10(self._theta * slot_duration) / capacity)) - 1
    
class WCOAlg(OKPDAlgBase):
    def _threshold_function(self, z, capacity, slot_duration):
        return np.exp(z * np.log(self._alpha * self._theta + 1))
