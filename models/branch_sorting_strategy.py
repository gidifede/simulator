import utils
from models.branch import Branch

class BranchSortingStrategy:
    def __init__(self, facilities, routes):
        self.facilities = facilities
        self.routes = routes

    def sort(self, source_facility_id, parcel):
        # return tuple: (delivered, dest_queue)
        source_facility = [facility for facility in self.facilities if facility.id == source_facility_id][0]
        facility_dest = next((x for x in self.facilities if isinstance(x, Branch) and parcel.receiver_zip_code in x.served_zip_codes ), None)
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