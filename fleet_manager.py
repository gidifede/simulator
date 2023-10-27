from models.vehicle import Vehicle

class FleetManager():
    def __init__(self):
        self.vehicles = []

    def add_vehicle(self, vehicle: Vehicle):
        self.vehicles.append(vehicle)
    
    def get_available_vehicles(self, facility_id, route_id):
        return [vehicle for vehicle in self.vehicles if vehicle.current_facility_id == facility_id and route_id in vehicle.assigned_route_ids and not vehicle.busy_unloading and not vehicle.running]
    
    def get_arriving_vehicles(self, facility_id):
        return [vehicle for vehicle in self.vehicles if vehicle.target_facility_id == facility_id and vehicle.running]
    
    def get_arrived_vehicles(self, facility_id):
        return [vehicle for vehicle in self.vehicles if vehicle.target_facility_id == facility_id and vehicle.busy_unloading and not vehicle.running]
    
    def get_vehicle_by_id(self, vehicle_id):
        return [vehicle for vehicle in self.vehicles if vehicle.id == vehicle_id][0]
    
    def do_work(self, start_datetime, seconds_from_starting_time):
        commands = []
        for vehicle in self.vehicles:
            commands.extend(vehicle.execute_update_position(start_datetime=start_datetime, time_now=seconds_from_starting_time))
        return commands