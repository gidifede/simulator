class SortingMachine():
    def __init__(self, id, sorting_strategy):
        self.id = id
        self.sorting_strategy = sorting_strategy

    def sort_parcel(self, source_facility_id, parcel):
        return self.sorting_strategy.sort(source_facility_id, parcel)
