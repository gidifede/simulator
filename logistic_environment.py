import time
from facility_manager import FacilityManager
from route_manager import RouteManager
from fleet_manager import FleetManager
import json
from models.parcel import Parcel
from dotenv import load_dotenv
import utils
import threading
from models.hub import Hub
from models.branch import Branch
from models.route import Route
from models.vehicle import Vehicle
from models.sorting_machine import SortingMachine
from models.hub_sorting_strategy_static import HubSortingStrategyStatic
from models.branch_sorting_strategy_static import BranchSortingStrategyStatic
from datetime import datetime, timedelta
import requests
import os
import uuid
import redis

load_dotenv()  # take environment variables from .env.

class LogisticsEnvironment(threading.Thread):
    def __init__(self, velocity, send_commands_flag):
        super().__init__()
        fleet_manager = FleetManager()
        route_manager = RouteManager(fleet_manager=fleet_manager)
        facility_manager = FacilityManager()
        self.facility_manager = facility_manager
        self.route_manager = route_manager
        self.fleet_manager = fleet_manager
        self.velocity = velocity
        self.seconds_from_start_date = 0
        self.seconds_from_start_date_external = 0
        self.start_datetime = datetime.now() #datetime.strptime('2023-09-25 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.end_datetime = self.start_datetime + timedelta(days=5) #datetime.strptime('2023-09-30 00:00:00', '%Y-%m-%d %H:%M:%S')
        self.paused = True
        self.reset_flag = threading.Event()
        self.send_commands_flag=send_commands_flag 
        self.auto_mode = True
        self.go_ahead = False

        # self.group_queue_waiting_times = []
        # self.group_queue_processing_times = []
        # self.cmd_queue_waiting_times = []
        # self.cmd_queue_processing_times = []

    # UI stuff
    def get_time(self):
        return utils.get_time_from_seconds_passed(self.start_datetime, self.seconds_from_start_date_external)

    def toggle_paused(self):
        self.paused = not self.paused
        print(F"Paused: {self.paused}")
        return self.paused

    def get_paused(self):
        return self.paused

    def update_velocity(self, velocity):
        self.velocity = velocity
        print(f"New velocity: {self.velocity}")
        return "OK"

    def get_velocity(self):
        return self.velocity

    def set_auto_mode(self):
        self.auto_mode = True
        print(F"Automode: {self.auto_mode}")
        return "OK"
    
    def set_manual_mode(self):
        self.auto_mode = False
        print(F"Automode: {self.auto_mode}")
        return "OK"
    
    def go_ahead_one_step(self):
        self.go_ahead = True
        return "OK"
    
    def get_cmds_performance(self):
        redis_client = redis.StrictRedis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)
        temp = redis_client.lrange('group_queue_waiting_times', 0, -1)
        group_queue_waiting_times =[float(value) for value in temp]

        temp = redis_client.lrange('group_queue_processing_times', 0, -1)
        group_queue_processing_times =[float(value) for value in temp]

        temp = redis_client.lrange('cmd_queue_waiting_times', 0, -1)
        cmd_queue_waiting_times =[float(value) for value in temp]

        temp = redis_client.lrange('cmd_queue_processing_times', 0, -1)
        cmd_queue_processing_times =[float(value) for value in temp]

        return {
            "len_group_queue_waiting_time" : len(group_queue_waiting_times),
            "Min_group_queue_waiting_time" : min(group_queue_waiting_times, default=0),
            "Max_group_queue_waiting_time" : max(group_queue_waiting_times, default=0),
            "Avg_group_queue_waiting_time" : 0 if len(group_queue_waiting_times) == 0 else sum(group_queue_waiting_times)/len(group_queue_waiting_times),

            "len_group_queue_processing_time" : len(group_queue_processing_times),
            "Min_group_queue_processing_time" : min(group_queue_processing_times, default=0),
            "Max_group_queue_processing_time" : max(group_queue_processing_times, default=0),
            "Avg_group_queue_processing_time" : 0 if len(group_queue_processing_times) == 0 else sum(group_queue_processing_times)/len(group_queue_processing_times),

            "len_cmd_queue_waiting_time" : len(cmd_queue_waiting_times),
            "Min_cmd_queue_waiting_time" : min(cmd_queue_waiting_times, default=0),
            "Max_cmd_queue_waiting_time" : max(cmd_queue_waiting_times, default=0),
            "Avg_cmd_queue_waiting_time" : 0 if len(cmd_queue_waiting_times) == 0 else sum(cmd_queue_waiting_times)/len(cmd_queue_waiting_times),

            "len_cmd_queue_processing_time" : len(cmd_queue_processing_times),
            "Min_cmd_queue_processing_time" : min(cmd_queue_processing_times, default=0),
            "Max_cmd_queue_processing_time" : max(cmd_queue_processing_times, default=0),
            "Avg_cmd_queue_processing_time" : 0 if len(cmd_queue_processing_times) == 0 else sum(cmd_queue_processing_times)/len(cmd_queue_processing_times),

        }

    # Start simulation thread
    def run(self):
        # Init simulation
        self.initialize_network(network_config_file='/app/test/local/network_test.json', route_config_file='/app/test/local/route_test.json',
                                fleet_config_file='/app/test/local/fleet_test.json', product_config_file='/app/test/local/product_test.json', 
                                num_sorted_parcel_per_second=10, num_loaded_parcel_per_second=10, num_unloaded_parcel_per_second=10, 
                                vehicle_capacity=50000, vehicle_position_update_interval=1800)

        # Preload some parcels
        # parcels = [Parcel(f"{utils.generate_random_string(5)}", "00701", "60101", 10, 100)
                #    , Parcel(f"{utils.generate_random_string(5)}", "00701", "00121", 10, 100)
                #    , Parcel(f"{utils.generate_random_string(5)}", "00701", "60101", 10, 100)
                #    , Parcel(f"{utils.generate_random_string(5)}", "00701", "00121", 10, 100)
                #    , Parcel(f"{utils.generate_random_string(5)}", "00701", "00121", 10, 100)
                #    , Parcel(f"{utils.generate_random_string(5)}", "00701", "99999", 10, 100)
                # ]
        parcels = []
        for i in range(100):
            # parcels.append(Parcel(f"{utils.generate_random_string(10)}", "00701", "60101", 1, 100))
            parcels.append(Parcel(f"{uuid.uuid4()}", "00701", "60101", 1, 100))
            # parcels.append(Parcel(f"{utils.generate_random_string(5)}", "60101", "00701", 10, 100))
            # parcels.append(Parcel(f"{utils.generate_random_string(5)}", "00122", "60101", 10, 100))
        commands = self.load_init_parcels(parcels=parcels)

        print('Initialized...')
        self.seconds_from_start_date = 28790#27900 #28780
        commands.extend(self.run_simulation())
        return commands

    # Main simulation loop
    def run_simulation(self):
        self.seconds_from_start_date_external = self.seconds_from_start_date
        commands = []
        i = 0
        seconds_from_start_date_to_end_date = utils.difference_in_seconds(self.start_datetime, self.end_datetime)
        while self.seconds_from_start_date < seconds_from_start_date_to_end_date:
            if self.reset_flag.is_set():
                break
            if (not self.paused and self.auto_mode) or self.go_ahead:
                start_time = time.time()
                print(f"ITER: {i}")
                print(utils.get_time_from_seconds_passed(self.start_datetime, self.seconds_from_start_date ))
                while self.seconds_from_start_date < self.seconds_from_start_date_external + self.velocity:
                    # do stuff
                    commands.extend(self.facility_manager.do_work(start_datetime=self.start_datetime, seconds_from_starting_time=self.seconds_from_start_date))
                    commands.extend(self.route_manager.do_work(start_datetime=self.start_datetime, seconds_from_starting_time=self.seconds_from_start_date))
                    commands.extend(self.fleet_manager.do_work(start_datetime=self.start_datetime, seconds_from_starting_time=self.seconds_from_start_date))
                    self.seconds_from_start_date += 1
                end_time = time.time()
                elapsed_time = end_time - start_time
                if (1 - elapsed_time)  > 0:
                    time.sleep(1 - elapsed_time)
                print(f"Iter duration: {elapsed_time}")
                self.seconds_from_start_date_external += self.velocity
                self.seconds_from_start_date = self.seconds_from_start_date_external
                if self.seconds_from_start_date > seconds_from_start_date_to_end_date:
                    self.seconds_from_start_date = seconds_from_start_date_to_end_date
                i+=1
                self.go_ahead = False
            else:
                time.sleep(1)
        return commands
    
    # Init simulation
    def initialize_network(self, network_config_file, route_config_file, fleet_config_file, product_config_file,
                           num_sorted_parcel_per_second, num_loaded_parcel_per_second, num_unloaded_parcel_per_second, 
                           vehicle_capacity, vehicle_position_update_interval):
        print("Init Network...")
        with open(network_config_file, 'r') as json_file:
        # with open('./network.json', 'r') as json_file:
            print("Beofre load")
            data = json.load(json_file)
            # hub_sorting_strategy = HubSortingStrategy(facilities=self.facility_manager.facilities, routes=self.route_manager.routes)
            # branch_sorting_strategy = BranchSortingStrategy(facilities=self.facility_manager.facilities, routes=self.route_manager.routes)
            hub_sorting_strategy = HubSortingStrategyStatic(facilities=self.facility_manager.facilities, routes=self.route_manager.routes)
            branch_sorting_strategy = BranchSortingStrategyStatic(facilities=self.facility_manager.facilities, routes=self.route_manager.routes)
            for c in data:
                if c['node']['node_type'] == 'HUB':
                    self.facility_manager.add_facility(Hub(
                                                    id=c['node']['node_id'],
                                                    latitude=c['node']['coordinates']['lat'],
                                                    longitude=c['node']['coordinates']['long'],
                                                    sorting_machine=SortingMachine(id=c['sorting_machines'][0]['serial'], sorting_strategy=hub_sorting_strategy),
                                                    fleet_manager=self.fleet_manager,
                                                    route_manager=self.route_manager,
                                                    num_sorted_parcel_per_second=num_sorted_parcel_per_second,
                                                    num_loaded_parcel_per_second=num_loaded_parcel_per_second,
                                                    num_unloaded_parcel_per_second=num_unloaded_parcel_per_second,
                                                    send_commands_flag=self.send_commands_flag)
                                                )
                else:
                    self.facility_manager.add_facility(Branch(
                                                    id=c['node']['node_id'],
                                                    latitude=c['node']['coordinates']['lat'],
                                                    longitude=c['node']['coordinates']['long'],
                                                    served_zip_codes=c['served_zip_codes'],
                                                    sorting_machine=SortingMachine(id=c['sorting_machines'][0]['serial'], sorting_strategy=branch_sorting_strategy),
                                                    fleet_manager=self.fleet_manager,
                                                    route_manager=self.route_manager,
                                                    num_sorted_parcel_per_second=num_sorted_parcel_per_second,
                                                    num_loaded_parcel_per_second=num_loaded_parcel_per_second,
                                                    num_unloaded_parcel_per_second=num_unloaded_parcel_per_second,
                                                    send_commands_flag=self.send_commands_flag)
                                                )   
            # Load network to LB
            for item in data:
                if "served_zip_codes" in item:
                    del item["served_zip_codes"]
            print("Before request")
            if self.send_commands_flag:
                response = requests.post(f"{os.getenv(key='FUNCTIONAL_TESTS_BASE_API')}/v1/network/setup", 
                                        headers={'x-api-key': f"{os.getenv(key='FUNCTIONAL_TESTS_API_KEY')}", 'Content-Type': 'application/json', 'Accept': '*/*'}, 
                                        data=json.dumps(data))
                print(f"Network uploaded: {response}")
                assert response.status_code == 200
                print("Network uploaded")

        with open(route_config_file, 'r') as json_file: 
            data = json.load(json_file)
            for e in data:
                source_facility = [facility for facility in self.facility_manager.facilities if facility.id == e['source_node_id']][0]
                target_facility = [facility for facility in self.facility_manager.facilities if facility.id == e['destination_node_id']][0]
                cutoff_times_int = []
                for item in e['cutoff_time']:
                    cutoff_times_int.append(int(item.split(":")[0]))
                self.route_manager.add_route(Route(
                                                    id=f"{e['source_node_id'][:3]}-{e['destination_node_id'][:3]}",
                                                    source_facility_id=e['source_node_id'],
                                                    source_latitude=source_facility.latitude,
                                                    source_longitude=source_facility.longitude,
                                                    target_facility_id=e['destination_node_id'],
                                                    target_latitude=target_facility.latitude,
                                                    target_longitude=target_facility.longitude,
                                                    distance=e['distance'],
                                                    cut_off_times=cutoff_times_int,
                                                    fleet_manager=self.fleet_manager,
                                                    send_commands_flag=self.send_commands_flag)
                                                )
            # Load route to LB
            for item in data:
                if "distance" in item:
                    del item["distance"]
            if self.send_commands_flag:
                response = requests.post(f"{os.getenv(key='FUNCTIONAL_TESTS_BASE_API')}/v1/route/setup", 
                                        headers={'x-api-key': f"{os.getenv(key='FUNCTIONAL_TESTS_API_KEY')}", 'Content-Type': 'application/json', 'Accept': '*/*'}, 
                                        data=json.dumps(data))
                assert response.status_code == 200
                print("Route uploaded")

            hub_sorting_strategy.compute()
            branch_sorting_strategy.compute()
        
        with open(fleet_config_file, 'r') as json_file: 
            data = json.load(json_file)
            for facility in data:
                for v in facility["vehicles"]:
                    self.fleet_manager.add_vehicle(Vehicle(
                                                        id=v['license_plate'],
                                                        max_capacity=v['capacity'],
                                                        assigned_route_ids=v['routes'],
                                                        current_facility_id=facility['facility_id'],
                                                        position_update_interval=vehicle_position_update_interval,
                                                        send_commands_flag=self.send_commands_flag)
                                                    ) 
            # Load vehicle to LB
            for item in data:
                for vehicle in item["vehicles"]:
                    if "routes" in vehicle:
                        del vehicle["routes"]
            if self.send_commands_flag:
                response = requests.post(f"{os.getenv(key='FUNCTIONAL_TESTS_BASE_API')}/v1/fleet/setup", 
                                        headers={'x-api-key': f"{os.getenv(key='FUNCTIONAL_TESTS_API_KEY')}", 'Content-Type': 'application/json', 'Accept': '*/*'}, 
                                        data=json.dumps(data))
                assert response.status_code == 200  
                print("Fleet uploaded")    

        with open(product_config_file, 'r') as json_file: 
            data = json.load(json_file)
            # Load vehicle to LB
            if self.send_commands_flag:
                response = requests.post(f"{os.getenv(key='FUNCTIONAL_TESTS_BASE_API')}/v1/product/setup", 
                                        headers={'x-api-key': f"{os.getenv(key='FUNCTIONAL_TESTS_API_KEY')}", 'Content-Type': 'application/json', 'Accept': '*/*'}, 
                                        data=json.dumps(data))
                assert response.status_code == 200  
                print("Product uploaded") 
            
        #     # Example:
        #     #   If the following routes exist: Milano_Hub-Torino_Branch1 and Torino_Branch1-Milano_Hub (they are assumed as different routes),
        #     #   create 6 vehicles having assigned_route_ids=['Milano_Hub_to_Torino_Branch1', 'Torino_Branch1_to_Milano_Hub'];
        #     #   for 3 vehicles use 'Milano_Hub' as starting facility id, so put vehicle.current_facility_id='Milano_Hub'
        #     #   for 3 vehicles use 'Torino_Branch1' as starting facility id, so put vehicle.current_facility_id='Torino_Branch1'
        #     NUM_VEHICLE_PER_ROUTE = 3
        #     [self.fleet_manager.add_vehicle(Vehicle(
        #                                             id=vehicle['id'],
        #                                             max_capacity=vehicle['max_capacity'],
        #                                             assigned_route_ids=vehicle['assigned_route_ids'],
        #                                             current_facility_id=vehicle['current_facility_id'],
        #                                             position_update_interval=vehicle_position_update_interval,
        #                                             send_commands_flag=self.send_commands_flag)
        #                                         ) for vehicle in utils.generate_vehicles(routes=self.route_manager.routes, num_vehicle_per_route=NUM_VEHICLE_PER_ROUTE, capacity=vehicle_capacity)]
        # assert len(self.fleet_manager.vehicles) == len(self.route_manager.routes) * NUM_VEHICLE_PER_ROUTE
        print(len(self.fleet_manager.vehicles))

    # Preload parcels
    def load_init_parcels(self, parcels):
        commands = []
        for parcel in parcels:
            command, res = self.facility_manager.accept_parcel(parcel=parcel, start_datetime=self.start_datetime, accept_time=self.seconds_from_start_date)
            commands.extend(command)
        return commands

