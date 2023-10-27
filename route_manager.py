from datetime import datetime, timedelta
from models.route import Route
from fleet_manager import FleetManager

class RouteManager():
    def __init__(self, fleet_manager: FleetManager):
        self.routes = []
        self.fleet_manager = fleet_manager

    def add_route(self, route: Route):
        self.routes.append(route)

    def get_route_by_id(self, id):
        return [route for route in self.routes if route.id == id][0]
    
    def get_route_destinations_by_source(self, source_facility_id):
        return [(route.id, route.target_facility_id) for route in self.routes if route.source_facility_id == source_facility_id] 
    
    def get_vehicles_in_facility(self, facility_id):
        result = self.get_route_destinations_by_source(facility_id)
        vehicle_grouped_per_destination = {}
        for route_id, facility_nex_hop_id in result:
            available_vehicles = [vehicle for vehicle in self.fleet_manager.vehicles if vehicle.current_facility_id == facility_id]
            if len(available_vehicles) == 0:
                vehicle_grouped_per_destination.update({facility_nex_hop_id: []})
            for vehicle in available_vehicles:
                if route_id in vehicle.assigned_route_ids:
                    items = vehicle_grouped_per_destination.get(facility_nex_hop_id, [])
                    items.append(vehicle)
                    vehicle_grouped_per_destination.update({facility_nex_hop_id: items})
        return vehicle_grouped_per_destination

    def do_work(self, start_datetime, seconds_from_starting_time):
        commands = []
        new_datetime = start_datetime + timedelta(seconds=seconds_from_starting_time)
        for route in self.routes:
            for cut_off_time in route.cut_off_times:
                if cut_off_time == new_datetime.hour and new_datetime.minute == 0 and new_datetime.second==0:  
                    commands.extend(route.execute_cut_off(start_datetime=start_datetime, time_now=seconds_from_starting_time))
            commands.extend(route.execute_return_vehicle_back(start_datetime=start_datetime, time_now=seconds_from_starting_time))
        return commands