import os
import re
import json
from collections import defaultdict

def parse_ipv6_addresses(configs):
    """Parse IPv6 addresses from router configuration files"""
    ipv6_addresses = defaultdict(dict)
    ip_pattern = re.compile(r"ipv6 address (\S+)/(\d+)")
    interface_pattern = re.compile(r"interface (\S+)")

    for filename, content in configs.items():
        lines = content.splitlines()
        current_interface = None

        for line in lines:
            if match := interface_pattern.search(line):
                current_interface = match.group(1)
            elif current_interface and (match := ip_pattern.search(line)):
                ip_address = match.group(1)
                prefix = match.group(2)
                ipv6_addresses[filename][current_interface] = f"{ip_address}/{prefix}"

    return ipv6_addresses

def load_config_files(directory):
    """Load all router configuration files from directory"""
    configs = {}
    for filename in os.listdir(directory):
        if filename.endswith("_startup-config.cfg"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as file:
                configs[filename] = file.read()
    return configs

def load_as_mapping():
    """Load AS-to-router mapping from intent.json"""
    import os

    script_dir = os.path.dirname(os.path.abspath(__file__))
    intent_path = os.path.join(script_dir, "intent.json")

    with open(intent_path, "r") as f:
        intent = json.load(f)
    
    as_mapping = {}
    for as_entry in intent["network"]:
        for as_name, as_data in as_entry.items():
            for router in as_data["routers"]:
                as_mapping[router] = as_name
    return as_mapping

def get_as_of_router(router_name, as_mapping):
    """Determine which AS a router belongs to"""
    # Extract base router name from filename
    base_name = re.match(r"^(R\d+)_.+", router_name).group(1)
    return as_mapping.get(base_name, "Unknown_AS")

def main():
    config_dir = "config_files"
    output_file = "router_address_mapping.txt"
    
    # Load required data
    configs = load_config_files(config_dir)
    as_mapping = load_as_mapping()
    ipv6_addresses = parse_ipv6_addresses(configs)

    # Organize routers by AS
    as_routers = defaultdict(dict)
    for router_file, interfaces in ipv6_addresses.items():
        as_name = get_as_of_router(router_file, as_mapping)
        router_id = re.search(r"^(R\d+)_.+", router_file).group(1)
        as_routers[as_name][router_id] = interfaces

    # Write results to file
    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("==================================================\n\n")
        
        # Sort ASes alphabetically
        for as_name in sorted(as_routers.keys()):
            file.write(f"AS: {as_name}\n")
            file.write("--------------------------------------------------\n")
            
            # Sort routers numerically within AS
            routers = sorted(as_routers[as_name].items(), 
                           key=lambda x: int(x[0][1:]))  # Sort by router number
            
            for router, interfaces in routers:
                file.write(f"\nRouter: {router}\n")
                file.write("Interfaces:\n")
                
                # Sort interfaces: Loopback0 first, then others alphabetically
                sorted_interfaces = sorted(interfaces.items(), 
                                         key=lambda x: (x[0] != "Loopback0", x[0]))
                
                for interface, ip in sorted_interfaces:
                    file.write(f"  {interface}: {ip}\n")
                
            file.write("\n")  # Add space between AS sections

    print(f"Router address mapping has been saved to {output_file}")

if __name__ == "__main__":
    main()