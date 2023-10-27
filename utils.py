from datetime import datetime, timedelta, timezone
import networkx as nx
import random
import string

def get_time_from_seconds_passed(start_datetime, seconds_passed_from_start_date):
        # Add the given number of seconds to the start_date
        new_datetime = start_datetime + timedelta(seconds=seconds_passed_from_start_date)
        # Convert the new_datetime back to a string in the desired format
        new_date = new_datetime.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        # print(datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
        # new_date=new_datetime.isoformat().replace('+00:00', 'Z')
        return new_date
    
def difference_in_seconds(datetime1, datetime2):
    # Calculate the time difference as a timedelta object
    time_difference = datetime2 - datetime1
    # Get the total difference in seconds
    difference_seconds = time_difference.total_seconds()
    return difference_seconds

def add_seconds_to_date(start_date, seconds_to_add):
    given_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%S.%fZ')
    # Create a timedelta object with the specified number of seconds
    time_delta = timedelta(milliseconds=seconds_to_add*1000)
    # Add the timedelta to the original datetime
    new_date = given_date + time_delta
    # Format the new datetime object back into the desired string format
    new_date_string = new_date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    return new_date_string

# def get_time(seconds):
#     seconds = seconds % (24 * 3600)
#     hour = seconds // 3600
#     seconds %= 3600
#     minutes = seconds // 60
#     seconds %= 60
    
#     return "%d:%02d:%02d" % (hour, minutes, seconds)

def find_next_hop(source_facility_id, target_center, routes):
    path = shortest_path(source_facility_id, target_center, routes)
    if not path:
        return
    if len(path) >= 2:
        return path[1]

def shortest_path(source_facility_id, target_center, routes):
    # Crea un grafo dirigito da networkx
    G = nx.Graph()
    # Aggiungi gli archi al grafo con i pesi
    for route in routes:
        G.add_edge(route.source_facility_id, route.target_facility_id, weight=route.km)
    # Calcola il percorso più breve utilizzando l'algoritmo Dijkstra
    try:
        shortest_path = nx.shortest_path(G, source=source_facility_id, target=target_center.id, weight='weight')
        return shortest_path
    except nx.NetworkXNoPath:
        return None  # Ritorna None se non esiste un percorso tra i due centri
    except nx.NodeNotFound:
        return None
    
def generate_random_string(length):
    # characters = string.ascii_letters + string.digits  # You can also include other characters if needed
    characters = string.digits  # You can also include other characters if needed
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def generate_vehicles(routes, num_vehicle_per_route, capacity):
    generated_vehicles=[]
    for route in routes:
        opposite_route_id = [item.id for item in routes if item.source_facility_id == route.target_facility_id and item.target_facility_id == route.source_facility_id]
        for i in range(num_vehicle_per_route):
            generated_vehicles.append({
                'id': f"{route.source_facility_id[:3]}-{route.target_facility_id[:3]}-{i}",#-{generate_random_string(5)}",
                'max_capacity': capacity,
                'assigned_route_ids': [route.id, opposite_route_id[0]],
                'current_facility_id': route.source_facility_id
            })
    return generated_vehicles