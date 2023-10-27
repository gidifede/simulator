import utils
from models.branch import Branch

class BranchSortingStrategyStatic:
    def __init__(self, facilities, routes):
        self.facilities = facilities
        self.routes = routes
        self.next_hop_map = {}  #{facility_id_dest_zip_code: (delivered, next_hop_id)}

    def compute(self):
        zip_code_list = []
        for facility in self.facilities:
            if isinstance(facility, Branch):
                zip_code_list.extend(facility.served_zip_codes)

        for facility in self.facilities:
            for zip_code in zip_code_list:
                delivered, next_hop_id = self.next_hop(facility.id, zip_code)
                self.next_hop_map[f"{facility.id}_{zip_code}"] = (delivered, next_hop_id)


    def next_hop(self, source_facility_id, zip_code):
        # return tuple: (delivered, dest_queue)
        source_facility = [facility for facility in self.facilities if facility.id == source_facility_id][0]
        facility_dest = next((x for x in self.facilities if isinstance(x, Branch) and zip_code in x.served_zip_codes ), None)
        if facility_dest is None:
            return False, None
        else:
            if facility_dest.id == source_facility.id:
                return True, None
            else: 
                next_hop = utils.find_next_hop(source_facility_id=source_facility_id, target_center=facility_dest, routes=self.routes)
                if next_hop:
                    return False, next_hop
                else:
                    return False, None 

    def sort(self, source_facility_id, parcel):
        # return tuple: (delivered, dest_queue)
        return self.next_hop_map.get(f"{source_facility_id}_{parcel.receiver_zip_code}", (False, None))