from models.sorting_machine import SortingMachine
from fleet_manager import FleetManager
from route_manager import RouteManager
import utils
from abc import ABC, abstractmethod
from logistic_backbone_commands import (ParcelLoaded, 
                                        TransportEnded, 
                                        ParcelUnloaded,
                                        send_group)
import time
import uuid

FACILITY_TYPE_HUB = "hub"
FACILITY_TYPE_BRANCH = "branch"

class Facility(ABC):
    def __init__(self, id, latitude, longitude, sorting_machine: SortingMachine, fleet_manager: FleetManager, route_manager: RouteManager, 
                 num_sorted_parcel_per_second: int, num_loaded_parcel_per_second: int, num_unloaded_parcel_per_second: int, send_commands_flag: bool):
        super().__init__()
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.sorting_machine = sorting_machine
        self.fleet_manager = fleet_manager
        self.route_manager = route_manager
        self.NUM_SORTED_PARCEL_PER_SECOND = num_sorted_parcel_per_second 
        self.NUM_LOADED_PARCEL_PER_SECOND = num_loaded_parcel_per_second 
        self.NUM_UNLOADED_PARCEL_PER_SECOND = num_unloaded_parcel_per_second 

        self.send_commands_flag = send_commands_flag

        # facility queues
        self.parcels_to_be_sorted = []
        self.parcels_dest_queue = {} # {idNextHop: [parcels]}
        self.parcels_undeliverable = []

    @abstractmethod
    def execute_sorting(self, start_datetime, start_time):
        pass
                     
    def load_vehicle(self, start_datetime, time_now):
        commands_to_send = []
        for dest_queue in self.parcels_dest_queue:
            route_id = f"{self.id[:3]}-{dest_queue[:3]}"
            vehicle_pool = self.fleet_manager.get_available_vehicles(facility_id=self.id, route_id=route_id) 
            if len(vehicle_pool) != 0:
                for vehicle in vehicle_pool:
                    if vehicle.current_load < vehicle.max_capacity:
                        vehicle.set_current_route_id(route_id)
                        if len(vehicle.parcels) == 0:
                            vehicle.set_current_transport_id(transport_id=f"{uuid.uuid4()}")
                        loaded_parcel_counter = 0
                        num_parcel_to_load = min(self.NUM_LOADED_PARCEL_PER_SECOND, vehicle.max_capacity - vehicle.current_load, len(self.parcels_dest_queue.get(dest_queue, [])))
                        for i in range(num_parcel_to_load):
                            parcel = self.parcels_dest_queue.get(dest_queue, []).pop(0)
                            done = vehicle.add_parcel(parcel=parcel)
                            if done:
                                # LOAD COMMAND
                                command = ParcelLoaded(
                                    transport_id=vehicle.current_transport_id,
                                    parcel_id=parcel.id,
                                    vehicle_license_plate=vehicle.id,
                                    facility_id=self.id,
                                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now+i*1/self.NUM_LOADED_PARCEL_PER_SECOND +(1/self.NUM_LOADED_PARCEL_PER_SECOND))
                                )
                                commands_to_send.append([command.headers, command.body, command.api_path])
                                loaded_parcel_counter += 1
                        if loaded_parcel_counter == num_parcel_to_load:
                            break

        if commands_to_send and self.send_commands_flag:
            send_group.delay(commands_to_send, time.time())
        return commands_to_send   

    def unload_vehicle(self, start_datetime,  time_now):
        commands_to_send = []
        arriving_vehicles = self.fleet_manager.get_arriving_vehicles(facility_id=self.id)
        for vehicle in arriving_vehicles:
            if vehicle.arrival_time==time_now:
                vehicle.end_trip()  # running=False
                vehicle.set_current_facility_id(self.id)
                vehicle.set_busy_unloading()
                # generate EndTransport
                command = TransportEnded(
                    transport_id=vehicle.current_transport_id,
                    vehicle_license_plate=vehicle.id,
                    facility_id=self.id,
                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now)
                )
                commands_to_send.append([command.headers, command.body, command.api_path])

        arrived_vehicles = self.fleet_manager.get_arrived_vehicles(facility_id=self.id)
        for vehicle in arrived_vehicles:    
            should_go_back = False
            for i in range(min(self.NUM_UNLOADED_PARCEL_PER_SECOND, len(vehicle.parcels))):
                parcel = vehicle.parcels.pop(0)
                vehicle.current_load -= parcel.weight
                self.add_parcel_to_facility(parcel=parcel, start_datetime=start_datetime, start_time=time_now+i*1/self.NUM_UNLOADED_PARCEL_PER_SECOND +(1/self.NUM_UNLOADED_PARCEL_PER_SECOND))
                should_go_back = True
                # UNLOAD COMMAND
                command = ParcelUnloaded(
                    transport_id=vehicle.current_transport_id,
                    parcel_id=parcel.id,
                    facility_id=self.id,
                    vehicle_license_plate=vehicle.id,
                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now+i*1/self.NUM_UNLOADED_PARCEL_PER_SECOND +(1/self.NUM_UNLOADED_PARCEL_PER_SECOND))
                )
                commands_to_send.append([command.headers, command.body, command.api_path])
            vehicle.set_should_go_back(should_go_back)

            if len(vehicle.parcels) == 0:
                vehicle.set_unbusy_unloading()

        if commands_to_send and self.send_commands_flag:
            send_group.delay(commands_to_send, time.time())
        return commands_to_send 

    def add_parcel_to_facility(self, parcel, start_datetime, start_time):
        self.parcels_to_be_sorted.append(parcel)

    @abstractmethod
    def accept_parcel(self, parcel, accept_time):
        pass

    def __repr__(self) -> str:
        return self.id

    @abstractmethod
    def json(self):
        pass