import threading

class Parcel():
    def __init__(self, id, sender_zip_code, receiver_zip_code, weight, size):
        self.id = id
        self.sender_zip_code = sender_zip_code
        self.receiver_zip_code = receiver_zip_code
        self.weight = weight
        self.size = size
        self.type = "Poste Delivery Web Express"
        
    def json(self):
        return f"{self.id}-{self.sender_zip_code}-{self.receiver_zip_code}"