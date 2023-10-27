from datetime import datetime
from logistic_environment import LogisticsEnvironment
import json
from models.parcel import Parcel
import utils

PARCEL_ACCEPTED='Logistic.PCL.Parcel.Accepted'
PARCEL_PROCESSED='Logistic.PCL.Facility.ParcelProcessed'
PARCEL_PROCESSING_FAILED='Logistic.PCL.Facility.ParcelProcessingFailed'
# PARCEL_READY_TBD='Logistic.PCL.Parcel.ReadyToBeDelivered'
PARCEL_DELIVERY_COMPLETED='Logistic.PCL.Parcel.DeliveryCompleted'
FLEET_LOADED='Logistic.PCL.Fleet.ParcelLoaded'
FLEET_UNLOADED='Logistic.PCL.Fleet.ParcelUnloaded'
FLEET_TRANSPORT_STARTED='Logistic.PCL.Fleet.TransportStarted'
FLEET_TRANSPORT_ENDED='Logistic.PCL.Fleet.TransportEnded'
FLEET_POSITION_UPDATED='Logistic.PCL.Fleet.PositionUpdated'

def verify_num_of_expected_cmds(commands, cmd_type, num_expected):
        cmds = [x for x in commands if json.loads(x[1])['type'] == cmd_type]
        assert(len(cmds) == num_expected)  

def test_scenario_1():
    commands = []
    NUM_SORTED_PARCEL_PER_SECOND = 10
    NUM_LOADED_PARCEL_PER_SECOND = 1
    NUM_UNLOADED_PARCEL_PER_SECOND = 1
    # send_commands_flag = True
    send_commands_flag = False
    logistics_env = LogisticsEnvironment(velocity=3600, send_commands_flag=send_commands_flag)#86400)
    logistics_env.initialize_network(config_file='./test/config.json', num_sorted_parcel_per_second=NUM_SORTED_PARCEL_PER_SECOND, 
                                     num_loaded_parcel_per_second=NUM_LOADED_PARCEL_PER_SECOND, num_unloaded_parcel_per_second=NUM_UNLOADED_PARCEL_PER_SECOND, 
                                     vehicle_capacity=50000, vehicle_position_update_interval=1800)
    parcels = [Parcel(f"{utils.generate_random_string(5)}", "00701", "60101", 10, 100)
                   , Parcel(f"{utils.generate_random_string(5)}", "00701", "00121", 10, 100)
                   , Parcel(f"{utils.generate_random_string(5)}", "00701", "60101", 10, 100)
                   , Parcel(f"{utils.generate_random_string(5)}", "00701", "00121", 10, 100)
                   , Parcel(f"{utils.generate_random_string(5)}", "00701", "00121", 10, 100)
                   , Parcel(f"{utils.generate_random_string(5)}", "00701", "99999", 10, 100)
                ]
    commands.extend(logistics_env.load_init_parcels(parcels=parcels))
    logistics_env.toggle_paused()
    logistics_env.start_datetime = datetime.strptime('2023-07-31 00:00:00', '%Y-%m-%d %H:%M:%S')
    logistics_env.end_datetime = datetime.strptime('2023-08-01 12:00:00', '%Y-%m-%d %H:%M:%S')
    commands.extend(logistics_env.run_simulation())
    assert len(commands) > 0
    print(len(commands))

    verify_num_of_expected_cmds(commands=commands, cmd_type=PARCEL_ACCEPTED, num_expected = 6)
    verify_num_of_expected_cmds(commands=commands, cmd_type=PARCEL_PROCESSED, num_expected = (5 + 5 + 3 + 2))
    verify_num_of_expected_cmds(commands=commands, cmd_type=PARCEL_PROCESSING_FAILED, num_expected = 1)
    # verify_num_of_expected_cmds(commands=commands, cmd_type=PARCEL_READY_TBD, num_expected = 5)
    verify_num_of_expected_cmds(commands=commands, cmd_type=PARCEL_DELIVERY_COMPLETED, num_expected = 5)
    verify_num_of_expected_cmds(commands=commands, cmd_type=FLEET_LOADED, num_expected = (5 + 5 + 3 + 2))
    verify_num_of_expected_cmds(commands=commands, cmd_type=FLEET_UNLOADED, num_expected = (5 + 5 + 3 + 2))
    verify_num_of_expected_cmds(commands=commands, cmd_type=FLEET_TRANSPORT_STARTED, num_expected = (1 + 2 + 1 + 1)*2)
    verify_num_of_expected_cmds(commands=commands, cmd_type=FLEET_TRANSPORT_ENDED, num_expected = (1 + 1 + 1 + 1 + 1)*2)
    verify_num_of_expected_cmds(commands=commands, cmd_type=FLEET_POSITION_UPDATED, num_expected = (2 + 16 + 12 + 2 + 2)*2)   

    # parcel 1
    parcel_1_accepted = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == PARCEL_ACCEPTED and json.loads(x[1])['data']['parcel']['id'] == parcels[0].id]
    parcel_1_processed = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == PARCEL_PROCESSED and json.loads(x[1])['data']['parcel_id'] == parcels[0].id]
    parcel_1_loaded = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == FLEET_LOADED and (x[2].split('/'))[len(x[2].split('/'))-1] == parcels[0].id]
    transport_started = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == FLEET_TRANSPORT_STARTED]
    transport_ended = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == FLEET_TRANSPORT_ENDED]
    parcel_1_unloaded = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == FLEET_UNLOADED and (x[2].split('/'))[len(x[2].split('/'))-1] == parcels[0].id]
    
    assert(parcel_1_accepted[0]['data']['timestamp'] == '2023-07-31T00:00:00.000000Z')
    
    assert(parcel_1_processed[0]['data']['timestamp'] == '2023-07-31T00:00:00.100000Z')
    assert(parcel_1_loaded[0]['data']['timestamp'] == '2023-07-31T00:00:01.000000Z')
    assert(transport_started[0]['data']['timestamp'] == '2023-07-31T09:00:00.000000Z')
    assert(transport_ended[0]['data']['timestamp'] == '2023-07-31T10:00:00.000000Z')
    assert(parcel_1_unloaded[0]['data']['timestamp'] == '2023-07-31T10:00:01.000000Z')

    assert(parcel_1_processed[1]['data']['timestamp'] == '2023-07-31T10:00:01.100000Z')
    assert(parcel_1_loaded[1]['data']['timestamp'] == '2023-07-31T10:00:02.000000Z')
    assert(transport_started[2]['data']['timestamp'] == '2023-07-31T11:00:00.000000Z')
    assert(transport_ended[2]['data']['timestamp'] == '2023-07-31T16:43:06.000000Z')
    assert(parcel_1_unloaded[1]['data']['timestamp'] == '2023-07-31T16:43:07.000000Z')

# def test_scenario_2():
#     commands = []
#     NUM_SORTED_PARCEL_PER_SECOND = 1
#     NUM_LOADED_PARCEL_PER_SECOND = 1
#     NUM_UNLOADED_PARCEL_PER_SECOND = 1
#     logistics_env.initialize_network(config_file='./test/config.json', num_sorted_parcel_per_second=NUM_SORTED_PARCEL_PER_SECOND, 
#                                      num_loaded_parcel_per_second=NUM_LOADED_PARCEL_PER_SECOND, num_unloaded_parcel_per_second=NUM_UNLOADED_PARCEL_PER_SECOND, 
#                                      vehicle_capacity=50000, vehicle_position_update_interval=1800)
#     parcels = []
#     for _ in range(100000):
#         parcels.append(Parcel(f"{utils.generate_random_string(5)}", "00701", "60101", 1, 100))
#     commands.extend(logistics_env.load_init_parcels(parcels=parcels))
#     logistics_env.toggle_paused()
#     logistics_env.start_datetime = '2023-07-31 07:59:50'
#     logistics_env.end_date_string = '2023-08-05 00:00:00'
#     commands.extend(logistics_env.run_simulation())
#     assert len(commands) > 0
#     print(len(commands))

#     ready_tbd_cmds = [json.loads(x[1]) for x in commands if json.loads(x[1])['type'] == PARCEL_READY_TBD and json.loads(x[1])['data']['location']['zipcode'] == '60101']
#     assert (len(ready_tbd_cmds) == 18010)