import threading
import time
from models.ref import register, deregister
import utils
from logistic_backbone_commands import PositionUpdated, send_group

class Vehicle():
    def __init__(self, id, max_capacity, assigned_route_ids, current_facility_id, position_update_interval, send_commands_flag):
        super().__init__()
        register(Vehicle, self)
        self.id = id
        self.max_capacity=max_capacity
        self.current_load = 0
        self.parcels = []
        self.running = False
        self.assigned_route_ids = assigned_route_ids
        self.current_facility_id = current_facility_id
        self.current_route_id = None
        self.current_transport_id = None
        self.position = None
        self.vehicle_type = "truck"
        self.busy_unloading = False
        self.arrival_time = None
        self.target_facility_id = None
        self.trip = []
        self.trip_start_time = None
        self.POSITION_UPDATE_INTERVAL = position_update_interval
        self.send_commands_flag = send_commands_flag
        self.should_go_back = False

    def add_parcel(self, parcel):
        if (self.current_load + parcel.weight) > self.max_capacity:
            return False
        self.parcels.append(parcel)
        self.current_load += parcel.weight
        return True

    def set_current_route_id(self, route_id):
        self.current_route_id = route_id

    def set_current_transport_id(self, transport_id):
        self.current_transport_id = transport_id

    def set_current_facility_id(self, facility_id):
        self.current_facility_id = facility_id

    def start_trip(self):
        self.running = True

    def end_trip(self):
        self.running = False
        self.trip = []
        self.trip_start_time = None
    
    def set_busy_unloading(self):
        self.busy_unloading = True

    def set_unbusy_unloading(self):
        self.busy_unloading = False

    def set_should_go_back(self, go_back):
        self.should_go_back = go_back
    
    def execute_update_position(self, start_datetime, time_now):
        commands_to_send = []
        if self.running:
            if (time_now-self.trip_start_time) % self.POSITION_UPDATE_INTERVAL == 0:
                self.position = self.trip[time_now-self.trip_start_time]
                # generate  PositionUpdated 
                if not self.should_go_back:
                    command = PositionUpdated(
                        vehicle_license_plate=self.id,
                        latitude=self.position[0],
                        longitute=self.position[1],
                        timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now),
                        transport_id=self.current_transport_id
                    )
                    commands_to_send.append([command.headers, command.body, command.api_path])
        if commands_to_send and self.send_commands_flag:
            send_group.delay(commands_to_send, time.time())
        return commands_to_send

    def json(self):
        return {
            "id": self.id,
            "current_route_id": self.current_route_id,
            "parcels": self.parcels,
            "current_load": self.current_load,
            "num_parcels": len(self.parcels),
            "running": self.running,
            "position": self.position,
            "vehicle_type": self.vehicle_type
        }
    
    def __repr__(self) -> str:
        return self.id