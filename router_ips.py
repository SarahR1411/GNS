import os
import re
from collections import defaultdict


# Function to parse IPv6 addresses from configuration files
def parse_ipv6_addresses(configs):
    """
    Parses the configuration files for IPv6 addresses and returns a dictionary with router names as keys,
    and their interfaces with corresponding IPv6 addresses as values.
    
    Arguments:
    configs -- a dictionary where keys are filenames, and values are the configuration contents (as strings).
    
    Returns:
    A dictionary of the form:
    {filename: {interface: 'ip_address/prefix'}}
    """
    ipv6_addresses = defaultdict(dict)  # To store IPv6 addresses for each router's interfaces
    ip_pattern = re.compile(r"ipv6 address (\S+)/(\d+)")    # Regex pattern for matching IPv6 address with prefix
    interface_pattern = re.compile(r"interface (\S+)")  # Regex pattern for matching interfaces

    # Iterate over each configuration file
    for filename, content in configs.items():
        lines = content.splitlines()    # Split the content into lines
        current_interface = None    # Placeholder for the current interface we are processing

        # Iterate over each line in the configuration file
        for line in lines:
            # Detect the interface name
            if match := interface_pattern.search(line):
                current_interface = match.group(1)

            # Detect IPv6 address and prefix for the current interface
            elif current_interface and (match := ip_pattern.search(line)):
                ip_address = match.group(1)
                prefix = match.group(2)
                # Store the IPv6 address with the corresponding interface in the dictionary
                ipv6_addresses[filename][current_interface] = f"{ip_address}/{prefix}"

    return ipv6_addresses


# Function to load configurations from files in a directory
def load_config_files(directory):
    """
    Loads configuration files from the specified directory and returns their contents as a dictionary.
    
    Arguments:
    directory -- the directory where configuration files are stored.
    
    Returns:
    A dictionary where keys are filenames and values are the file contents.
    """
    configs = {}
    for filename in os.listdir(directory):
        if filename.endswith("_startup-config.cfg"):    # Only process files with the given suffix
            filepath = os.path.join(directory, filename)    # Get the full file path
            with open(filepath, "r") as file:
                configs[filename] = file.read() # Read the file and store its content in the dictionary
    return configs


# Function to determine the AS (Autonomous System) of a router based on its name
def get_as_of_router(router_name):
    """
    Determines which Autonomous System (AS) a router belongs to based on its name.
    
    Arguments:
    router_name -- the name of the router (e.g., 'R1_startup-config.cfg').
    
    Returns:
    A string representing the AS ('AS_X' or 'AS_Y').
    """
    # If the router number is <= 7, it's in AS_X; otherwise, it's in AS_Y
    return "AS_X" if int(router_name.lstrip("R").split("_")[0]) <= 7 else "AS_Y"


# Main function to extract and save IPv6 addresses
def main():
    """
    Main function that:
    - Loads router configurations from files.
    - Parses IPv6 addresses from the configurations.
    - Organizes routers by their AS.
    - Saves the router address mapping to a text file.
    """
    # Directory containing configuration files
    config_dir = "config_files"
    output_file = "router_address_mapping.txt"  # File where the results will be saved

    # Load configurations
    configs = load_config_files(config_dir)

    # Parse the IPv6 addresses from the configurations
    ipv6_addresses = parse_ipv6_addresses(configs)

    # Organize routers by AS (AS_X or AS_Y)
    as_x_routers = {}   # Store routers in AS_X
    as_y_routers = {}   # Store routers in AS_Y

    for router, interfaces in ipv6_addresses.items():
        # Determine the AS of the router
        as_name = get_as_of_router(router)
        if as_name == "AS_X":
            as_x_routers[router] = interfaces
        else:
            as_y_routers[router] = interfaces

    # Write the results to the output file
    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("==================================================\n\n")

        # Write details for AS_X routers
        file.write("AS: AS_X\n")
        file.write("--------------------------------------------------\n")
        for router in sorted(as_x_routers, key=lambda x: int(re.search(r"\d+", x).group())):
            file.write(f"\nRouter: {router.split('_')[0]}\n")
            file.write("Interfaces:\n")
            # Sort interfaces with 'Loopback0' first, then by interface name
            for interface, ip in sorted(as_x_routers[router].items(), key=lambda x: (x[0] != "Loopback0", x[0])):
                file.write(f"  {interface}: {ip}\n")

        # Write details for AS_Y routers
        file.write("\nAS: AS_Y\n")
        file.write("--------------------------------------------------\n")
        for router in sorted(as_y_routers, key=lambda x: int(re.search(r"\d+", x).group())):
            file.write(f"\nRouter: {router.split('_')[0]}\n")
            file.write("Interfaces:\n")
            # Sort interfaces with 'Loopback0' first, then by interface name
            for interface, ip in sorted(as_y_routers[router].items(), key=lambda x: (x[0] != "Loopback0", x[0])):
                file.write(f"  {interface}: {ip}\n")

    # Notify the user that the mapping has been saved
    print(f"Router address mapping has been saved to {output_file}")

if __name__ == "__main__":
    main()  # Run the main function to process the configurations and generate the address mapping
