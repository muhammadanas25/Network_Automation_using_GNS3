from netmiko import ConnectHandler
from pymongo import MongoClient
import time
import sys

MONGODB_IP= 'mongodb://localhost:27017/'
# MongoDB connection
def connect_mongodb():
    try:
        client = MongoClient(MONGODB_IP)  
        db = client['gns3']
        collection = db['device_configurations']
        print("Connected to MongoDB successfully.")
        return collection
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")
        sys.exit(1)

# SSH connection to the network device
def connect_device(device_info):
    try:
        connection = ConnectHandler(**device_info)
        return connection
    except Exception as e:
        print(f"Connection failed to {device_info['host']} on port {device_info['port']}: {e}")
        return None

# Retrieve configuration from the device
def get_device_config(connection):
    try:
        config = connection.send_command("show running-config")
        return config
    except Exception as e:
        print(f"Failed to retrieve configuration: {e}")
        return None

# Store configuration in MongoDB
def store_configuration(collection, device_name, device_ip, config):
    try:
        document = {
            "device_name": device_name,
            "device_ip": device_ip,
            "configuration": config,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
        }
        collection.insert_one(document)
        print(f"Configuration stored for {device_name}.")
    except Exception as e:
        print(f"Failed to store configuration in MongoDB: {e}")

# Display the contents of MongoDB
def display_mongodb_contents(collection):
    print("\n--- MongoDB: Device Configurations ---")
    try:
        configurations = collection.find()
        for config in configurations:
            print(f"Device: {config['device_name']}, IP: {config['device_ip']}")
            print(f"Timestamp: {config['timestamp']}")
            print(f"Configuration: {config['configuration']}\n")
    except Exception as e:
        print(f"Failed to retrieve configurations from MongoDB: {e}")


def main():
    # MongoDB connection
    config_collection = connect_mongodb()

    # Device details for both R1 and R2
    devices = [
        {
            'device_type': 'cisco_ios_telnet',  
            'host': 'localhost',
            'port': 5002,  # Port for R1
            'username': 'admin',  
            'password': 'admin', 
            'secret': 'secret',  
        },
        {
            'device_type': 'cisco_ios_telnet', 
            'host': 'localhost',
            'port': 5003, 
            'username': 'admin', 
            'password': 'admin',  
            'secret': 'secret', 
        }
    ]

    # Loop over each device
    for device in devices:
        print(f"Connecting to {device['host']} on port {device['port']}...")
        connection = connect_device(device)
        if connection:
            # Enter enable mode 
            connection.enable()

            # Retrieve configuration
            config = get_device_config(connection)
            if config:
                # Store the configuration in MongoDB
                store_configuration(config_collection, device['host'], device['host'], config)

            # Disconnect from the device
            connection.disconnect()
        # Display the contents of MongoDB at the end
    display_mongodb_contents(config_collection)


if __name__ == "__main__":
    main()
