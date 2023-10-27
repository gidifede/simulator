from models.facility import Facility
from models.branch import Branch

class FacilityManager():
    def __init__(self):
        self.facilities = []

    def add_facility(self, facility: Facility):
        self.facilities.append(facility)

    def do_work(self, start_datetime, seconds_from_starting_time):
        commands = []
        for facility in self.facilities:
            commands.extend(facility.execute_sorting(start_datetime=start_datetime, time_now=seconds_from_starting_time))
            commands.extend(facility.load_vehicle(start_datetime=start_datetime, time_now=seconds_from_starting_time))
            commands.extend(facility.unload_vehicle(start_datetime=start_datetime, time_now=seconds_from_starting_time))
        return commands

    def accept_parcel(self, parcel, start_datetime, accept_time):
        facilities = [facility for facility in self.facilities if isinstance(facility, Branch) and parcel.sender_zip_code in facility.served_zip_codes]
        if len(facilities) == 0:
            return "KO"
        else:
            facility = facilities[0]
            # print("Adding parcel to facility ", facility.id)
            commands = facility.accept_parcel(parcel=parcel, start_datetime=start_datetime, accept_time=accept_time)
            return commands, "OK"