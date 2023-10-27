import json
from datetime import datetime, timezone
from cloudevents.conversion import to_structured
from cloudevents.http import CloudEvent
import requests
import os
from celeryapp_cmds import app as app_cmds
from celeryapp_groups import app as app_groups
import time
import redis

def generate_cloudevent(source, type, data):
    attributes = {
        "specversion": "1.0",
        "type": type,
        "source": source,
        "time": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "datacontenttype": "application/json",
        "subject": "Command",
    }
    event = CloudEvent(attributes, data)

    # Creates the HTTP request representation of the CloudEvent in structured content mode
    headers, body = to_structured(event)
    return headers, body


class BaseCommand:
    payload = None
    api_path = None

    def to_json(self):
        return json.loads(self.body)

    def send(self, base_api_url=os.getenv(key="FUNCTIONAL_TESTS_BASE_API"), api_key=os.getenv(key="FUNCTIONAL_TESTS_API_KEY")):
        headers = {
                'Content-type': 'application/json',
                'Connection': 'keep-alive'
            }
        if api_key is not None:
            headers['x-api-key'] = api_key 
        
        headers.update(self.headers)
        response = requests.post(
            f"{base_api_url}{self.api_path}", json=self.to_json(),
            headers=headers,
        )
        return response

class BaseModel:
    def to_json(self):
        return json.loads(json.dumps(self.__dict__))

class Empty(BaseModel):
    pass


class Parcel(BaseModel):
    def __init__(self, id, name, type):
        self.id = id
        self.name = name
        self.type = type



class Receiver(BaseModel):
    def __init__(self, name, city, nation, address, zipcode, number, email):
        self.name = name
        self.city = city
        self.nation = nation
        self.address = address
        self.zipcode = zipcode
        self.number = number
        self.email = email


class Sender(BaseModel):
    def __init__(self, name, city, nation, address, zipcode):
        self.name = name
        self.city = city
        self.nation = nation
        self.address = address
        self.zipcode = zipcode


class Location(BaseModel):
    def __init__(self, type, city, address, zipcode, nation, locationCode, attributes):
        self.type = type
        self.city = city
        self.address = address
        self.zipcode = zipcode
        self.nation = nation
        self.locationCode = locationCode
        self.attributes = attributes

class Carrier(BaseModel):
    def __init__(self, typeId, driverId, vehicleId, routeId):
        self.typeId = typeId
        self.driverId = driverId
        self.vehicleId = vehicleId
        self.routeId=routeId

class FromTo(BaseModel):
    def __init__(self, type, address, zipcode, city, nation):
        self.type = type
        self.address = address
        self.zipcode = zipcode
        self.city = city
        self.nation = nation


class Transport(BaseModel):
    def __init__(self, id, vehicle_id, driver_id, route_id):
        self.id = id 
        self.vehicleId = vehicle_id
        self.driverId = driver_id
        self.routeId = route_id

class Operator(BaseModel):
    def __init__(self, id):
        self.id = id

#### PARCEL EVENT #####
class ParcelAccepted(BaseCommand):

    def __init__(self, parcel=None, timestamp=None, receiver=None, sender=None, facility_id=None):
        self.payload = {}
        if receiver is not None:
            self.payload['receiver'] = receiver.to_json()
        if sender is not None:
            self.payload['sender'] = sender.to_json()
        if facility_id is not None:
            self.payload['facility_id'] = facility_id
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if parcel is not None:
            self.payload['parcel'] = parcel.to_json()
        self.api_path=f'/v1/parcel/{parcel.id}/accepted'
        
        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Parcel.Accepted',
            data=self.payload
        )
        
class ParcelDeliveryCompleted(BaseCommand):

    def __init__(self, parcel_id, timestamp=None):
        self.payload = {}
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if parcel_id is not None:
            self.payload['parcel_id'] = parcel_id

        self.api_path=f'/v1/parcel/{parcel_id}/delivery_completed'

        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Parcel.DeliveryCompleted',
            data=self.payload
    )

#### FACILITY EVENT #####
class ParcelProcessed(BaseCommand):

    def __init__(self, parcel_id=None, timestamp=None, facility_id=None, destination_facility_id=None,
                 sorting_machine_id=None):
        self.payload = {}
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if parcel_id is not None:
            self.payload['parcel_id'] = parcel_id
        if facility_id is not None:
            self.payload['facility_id'] = facility_id
        if sorting_machine_id is not None:
            self.payload['sorting_machine_id'] = sorting_machine_id
        if destination_facility_id is not None:
            self.payload['destination_facility_id'] = destination_facility_id
        
        self.api_path=f'/v1/facility/{facility_id}/sorting_machine/{sorting_machine_id}/parcel_processed'

        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Facility.ParcelProcessed',
            data=self.payload
        )

class ParcelProcessingFailed(BaseCommand):

    def __init__(self, parcel_id=None, timestamp=None, facility_id=None, err_msg=None,
                 sorting_machine_id=None):
        self.payload = {}
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if parcel_id is not None:
            self.payload['parcel_id'] = parcel_id
        if facility_id is not None:
            self.payload['facility_id'] = facility_id
        if err_msg is not None:
            self.payload['err_msg'] = err_msg
        if sorting_machine_id is not None:
            self.payload['sorting_machine_id'] = sorting_machine_id
        
        self.api_path=f'/v1/facility/{facility_id}/sorting_machine/{sorting_machine_id}/parcel_processing_failed'

        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Facility.ParcelProcessingFailed',
            data=self.payload
        )

#### FLEET EVENT #####
class TransportEnded(BaseCommand):
     
    def __init__(self, vehicle_license_plate=None, facility_id=None,transport_id=None, timestamp=None):
        self.payload = {}
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if transport_id is not None:
            self.payload['transport_id'] = transport_id
        if vehicle_license_plate is not None:
            self.payload['vehicle_license_plate'] = vehicle_license_plate
        if facility_id is not None:
            self.payload['facility_id'] = facility_id
        
        self.api_path=f'/v1/fleet/{vehicle_license_plate}/transport_ended'
        
        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Fleet.TransportEnded',
            data=self.payload
        )

class TransportStarted(BaseCommand):
    
    def __init__(self, vehicle_license_plate=None, source_facility_id=None,transport_id=None, destination_facility_id=None, timestamp=None):
        self.payload = {}
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if transport_id is not None:
            self.payload['transport_id'] = transport_id
        if vehicle_license_plate is not None:
            self.payload['vehicle_license_plate'] = vehicle_license_plate
        if source_facility_id is not None:
            self.payload['source_facility_id'] = source_facility_id
        if destination_facility_id is not None:
            self.payload['destination_facility_id'] = destination_facility_id

        self.api_path=f'/v1/fleet/{vehicle_license_plate}/transport_started'
        
        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Fleet.TransportStarted',
            data=self.payload
        )

class ParcelLoaded(BaseCommand):
    
    def __init__(self, parcel_id=None, vehicle_license_plate=None, facility_id=None, timestamp=None,transport_id=None):
        self.payload = {}
        if parcel_id is not None:
            self.payload['parcel_id'] = parcel_id
        if vehicle_license_plate is not None:
            self.payload['vehicle_license_plate'] = vehicle_license_plate
        if transport_id is not None:
            self.payload['transport_id'] = transport_id
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if facility_id is not None:
            self.payload['facility_id'] = facility_id
        
        self.api_path=f'/v1/fleet/{vehicle_license_plate}/parcel_loaded'
        
        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Fleet.ParcelLoaded',
            data=self.payload
        )

class ParcelUnloaded(BaseCommand):
     
    def __init__(self, parcel_id=None, vehicle_license_plate=None, facility_id=None, timestamp=None,transport_id=None):
        self.payload = {}
        if parcel_id is not None:
            self.payload['parcel_id'] = parcel_id
        if vehicle_license_plate is not None:
            self.payload['vehicle_license_plate'] = vehicle_license_plate
        if transport_id is not None:
            self.payload['transport_id'] = transport_id
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if facility_id is not None:
            self.payload['facility_id'] = facility_id
        
        self.api_path=f'/v1/fleet/{vehicle_license_plate}/parcel_unloaded'

        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Fleet.ParcelUnloaded',
            data=self.payload
        )

class PositionUpdated(BaseCommand):
     
    def __init__(self, vehicle_license_plate=None, latitude=None, longitute=None, timestamp=None, transport_id=None):
        self.payload = {}
        if vehicle_license_plate is not None:
            self.payload['vehicle_license_plate'] = vehicle_license_plate
        if latitude is not None:
            self.payload['latitude'] = latitude
        if longitute is not None:
            self.payload['longitute'] = longitute
        if timestamp is not None:
            self.payload['timestamp'] = timestamp
        if transport_id is not None:
            self.payload['transport_id'] = transport_id
        
        self.api_path=f'/v1/fleet/vehicle/{vehicle_license_plate}/position_updated'
     
        self.headers, self.body = generate_cloudevent(
            source='Simulator',
            type='Logistic.PCL.Fleet.PositionUpdated',
            data=self.payload
        )

@app_cmds.task(queue='cmds-queue')
def send_command(headers, body, api_path, time_sent):
    received_time = time.time()
    waiting_time = received_time-time_sent
    command = BaseCommand()
    command.api_path = api_path
    command.body = body
    command.headers = headers
    res = command.send()
    if res.status_code != 202:
        raise Exception(f"Error: {res.status_code}, {res.text}. Full response:{res}. Cannot send command {command.body} to api {command.api_path}")
    processing_time = time.time() - received_time
    redis_client = redis.StrictRedis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)
    redis_client.rpush('cmd_queue_waiting_times', str(waiting_time))
    redis_client.rpush('cmd_queue_processing_times', str(processing_time))


@app_groups.task(queue='group-cmds-queue')
def send_group(commands, time_sent):
    received_time = time.time()
    waiting_time = received_time-time_sent
    for command in commands:
        headers, body, api_path = command
        try:
            send_command.delay(headers, body, api_path, time.time())
        except Exception as e:
            # assert False
            print(f"Task error: {e}")
    processing_time = time.time()-received_time
    redis_client = redis.StrictRedis(host=os.environ.get("REDIS_HOST", "localhost"), port=6379, db=0)
    redis_client.rpush('group_queue_waiting_times', str(waiting_time))
    redis_client.rpush('group_queue_processing_times', str(processing_time))