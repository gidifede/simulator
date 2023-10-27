from models.facility import Facility
import utils
from models.sorting_machine import SortingMachine
from fleet_manager import FleetManager
from route_manager import RouteManager
from logistic_backbone_commands import (ParcelProcessingFailed, 
                                        ParcelProcessed, 
                                        send_group)
import time

class Hub(Facility):
    def __init__(self, id, latitude, longitude, sorting_machine: SortingMachine, fleet_manager: FleetManager, route_manager: RouteManager, 
                 num_sorted_parcel_per_second: int, num_loaded_parcel_per_second: int, num_unloaded_parcel_per_second: int, send_commands_flag: bool):
        super().__init__(id=id, latitude=latitude, longitude=longitude, sorting_machine=sorting_machine, fleet_manager=fleet_manager, route_manager=route_manager, 
                         num_sorted_parcel_per_second=num_sorted_parcel_per_second, num_loaded_parcel_per_second=num_loaded_parcel_per_second, 
                         num_unloaded_parcel_per_second=num_unloaded_parcel_per_second, send_commands_flag=send_commands_flag)
    

    def execute_sorting(self, start_datetime, time_now):
        commands_to_send = []
        for i in range(min(self.NUM_SORTED_PARCEL_PER_SECOND, len(self.parcels_to_be_sorted))):
            parcel = self.parcels_to_be_sorted.pop(0)
            dest_queue = self.sorting_machine.sort_parcel(self.id, parcel)

            if dest_queue is not None:
                next_hop_parcels = self.parcels_dest_queue.get(dest_queue, [])
                next_hop_parcels.append(parcel)
                self.parcels_dest_queue.update({dest_queue: next_hop_parcels}) 
                # generate  ParcelProcessed  
                command = ParcelProcessed(
                    parcel_id=parcel.id,
                    facility_id=self.id,
                    destination_facility_id=dest_queue,
                    sorting_machine_id=self.sorting_machine.id,
                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now+i*(1/self.NUM_SORTED_PARCEL_PER_SECOND)+(1/self.NUM_SORTED_PARCEL_PER_SECOND))
                    )
                commands_to_send.append([command.headers, command.body, command.api_path])
            else:
                self.parcels_undeliverable.append(parcel)
                # generate ParcelProcessingFailed
                command = ParcelProcessingFailed(
                    parcel_id=parcel.id,
                    facility_id=self.id,
                    sorting_machine_id=self.sorting_machine.id,
                    err_msg=f"Cannot find branch that manages zip code {parcel.receiver_zip_code}",
                    timestamp=utils.get_time_from_seconds_passed(start_datetime, time_now+i*(1/self.NUM_SORTED_PARCEL_PER_SECOND) +(1/self.NUM_SORTED_PARCEL_PER_SECOND))
                )
                commands_to_send.append([command.headers, command.body, command.api_path])

        if commands_to_send and self.send_commands_flag:
            send_group.delay(commands_to_send, time.time())
        return commands_to_send
    
    def json(self):
        return {
            "id": self.id,
            "parcels_to_be_sorted": self.parcels_to_be_sorted,
            "parcels_dest_queue": self.parcels_dest_queue,
            "parcels_undeliverable": self.parcels_undeliverable,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "available_vehicles": self.route_manager.get_vehicles_in_facility(facility_id=self.id)
        }
    
    def accept_parcel(self, parcel, accept_time):
        pass
