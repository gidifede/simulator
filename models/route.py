import time
import utils
from fleet_manager import FleetManager
from logistic_backbone_commands import TransportStarted, send_group
import uuid

class Route:
    def __init__(self, id, source_facility_id, source_latitude, source_longitude, target_facility_id, target_latitude, target_longitude, 
                 distance, cut_off_times, fleet_manager: FleetManager, send_commands_flag: bool):
        self.id = id
        self.source_facility_id = source_facility_id
        self.source_latitude = source_latitude
        self.source_longitude = source_longitude
        self.target_facility_id = target_facility_id
        self.target_latitude = target_latitude
        self.target_longitude = target_longitude
        self.km = distance
        self.cut_off_times = cut_off_times
        self.fleet_manager = fleet_manager
        self.send_commands_flag = send_commands_flag

    def json(self):
        return {
            "source_facility_id": self.source_facility_id,
            "target_facility_id": self.target_facility_id,
            "km": self.km,
            "cut_off_times": self.cut_off_times,
        }
    
    def __repr__(self) -> str:
        return self.id
    
    def get_route_coordinates(self, start_coords, end_coords, num_points=200):
        route_coordinates = []
        for i in range(num_points):
            lat = start_coords[0] + (end_coords[0] - start_coords[0]) * (i / (num_points - 1))
            lon = start_coords[1] + (end_coords[1] - start_coords[1]) * (i / (num_points - 1))
            route_coordinates.append((lat, lon))
        return route_coordinates

    def execute_cut_off(self, start_datetime, time_now):   
        commands_to_send = []
        available_vehicles = self.fleet_manager.get_available_vehicles(facility_id=self.source_facility_id, route_id=self.id)
        for vehicle in available_vehicles:
            if vehicle.current_load > 0:
                start = time.time()
                print(utils.get_time_from_seconds_passed(start_datetime, time_now), f"Executing cutoff route:{self}, vehicle: {vehicle.id}")
                vehicle.set_current_facility_id(facility_id=None)
                vehicle.start_trip()
                transport_time = int((self.km / 100) * 60 * 60)
                print(f"Transport time from {self.source_facility_id} to {self.target_facility_id}: {transport_time}")
                vehicle.arrival_time = time_now+transport_time
                vehicle.target_facility_id = self.target_facility_id
                vehicle.trip_start_time = time_now
                vehicle.trip = self.get_route_coordinates(start_coords=(self.source_latitude, self.source_longitude),
                                                          end_coords=(self.target_latitude, self.target_longitude),
                                                          num_points=transport_time)
                # generate  TransportStarted 
                command = TransportStarted(
                    transport_id=vehicle.current_transport_id,
                    vehicle_license_plate=vehicle.id,
                    source_facility_id=self.source_facility_id,
                    destination_facility_id=self.target_facility_id,
                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now)
                )
                commands_to_send.append([command.headers, command.body, command.api_path])
                end = time.time()
                print(f"Cutoff duration: {end-start}")
        if commands_to_send and self.send_commands_flag:
            send_group.delay(commands_to_send, time.time())
        return commands_to_send
    
    def execute_return_vehicle_back(self, start_datetime, time_now):   
        commands_to_send = []
        available_vehicles = self.fleet_manager.get_available_vehicles(facility_id=self.source_facility_id, route_id=self.id)
        for vehicle in available_vehicles:
            if vehicle.should_go_back:# and not vehicle.busy_loading:
                start = time.time()
                print(utils.get_time_from_seconds_passed(start_datetime, time_now), f"Vehicle back route:{self}, vehicle: {vehicle.id}")
                vehicle.set_current_facility_id(facility_id=None)
                vehicle.set_current_transport_id(transport_id=f"{uuid.uuid4()}")
                vehicle.start_trip()
                transport_time = int((self.km / 100) * 60 * 60)
                print(f"Transport time from {self.source_facility_id} to {self.target_facility_id}: {transport_time}")
                vehicle.arrival_time = time_now+transport_time
                vehicle.target_facility_id = self.target_facility_id
                vehicle.trip_start_time = time_now
                vehicle.trip = self.get_route_coordinates(start_coords=(self.source_latitude, self.source_longitude),
                                                          end_coords=(self.target_latitude, self.target_longitude),
                                                          num_points=transport_time)
                # generate  TransportStarted 
                time.sleep(3) # to avoi that this TrasportStarted is processed before TransportEnded
                command = TransportStarted(
                    transport_id=vehicle.current_transport_id,
                    vehicle_license_plate=vehicle.id,
                    source_facility_id=self.source_facility_id,
                    destination_facility_id=self.target_facility_id,
                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now)
                )
                commands_to_send.append([command.headers, command.body, command.api_path])

                end = time.time()
                print(f"Cutoff duration: {end-start}")
        if commands_to_send and self.send_commands_flag:
            send_group.delay(commands_to_send, time.time())
        return commands_to_send