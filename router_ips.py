import os
import re
from collections import defaultdict

# Function to parse IPv6 addresses from configuration files
def parse_ipv6_addresses(configs):
    ipv6_addresses = defaultdict(dict)
    ip_pattern = re.compile(r"ipv6 address (\S+)/(\d+)")
    interface_pattern = re.compile(r"interface (\S+)")

    for filename, content in configs.items():
        lines = content.splitlines()
        current_interface = None

        for line in lines:
            # Detect interface
            if match := interface_pattern.search(line):
                current_interface = match.group(1)

            # Detect IPv6 address
            elif current_interface and (match := ip_pattern.search(line)):
                ip_address = match.group(1)
                prefix = match.group(2)
                ipv6_addresses[filename][current_interface] = f"{ip_address}/{prefix}"

    return ipv6_addresses

# Function to load configurations from files
def load_config_files(directory):
    configs = {}
    for filename in os.listdir(directory):
        if filename.endswith("_startup-config.cfg"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as file:
                configs[filename] = file.read()
    return configs

# Function to determine AS from router name
def get_as_of_router(router_name):
    return "AS_X" if int(router_name.lstrip("R").split("_")[0]) <= 7 else "AS_Y"

# Main function to extract and save IPv6 addresses
def main():
    # Directory containing configuration files
    config_dir = "config_files"
    output_file = "router_address_mapping.txt"

    # Load configurations
    configs = load_config_files(config_dir)

    # Parse IPv6 addresses
    ipv6_addresses = parse_ipv6_addresses(configs)

    # Organize routers by AS
    as_x_routers = {}
    as_y_routers = {}

    for router, interfaces in ipv6_addresses.items():
        as_name = get_as_of_router(router)
        if as_name == "AS_X":
            as_x_routers[router] = interfaces
        else:
            as_y_routers[router] = interfaces

    # Write results to a text file
    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("==================================================\n\n")

        file.write("AS: AS_X\n")
        file.write("--------------------------------------------------\n")
        for router in sorted(as_x_routers, key=lambda x: int(re.search(r"\d+", x).group())):
            file.write(f"\nRouter: {router.split('_')[0]}\n")
            file.write("Interfaces:\n")
            for interface, ip in sorted(as_x_routers[router].items(), key=lambda x: (x[0] != "Loopback0", x[0])):
                file.write(f"  {interface}: {ip}\n")

        file.write("\nAS: AS_Y\n")
        file.write("--------------------------------------------------\n")
        for router in sorted(as_y_routers, key=lambda x: int(re.search(r"\d+", x).group())):
            file.write(f"\nRouter: {router.split('_')[0]}\n")
            file.write("Interfaces:\n")
            for interface, ip in sorted(as_y_routers[router].items(), key=lambda x: (x[0] != "Loopback0", x[0])):
                file.write(f"  {interface}: {ip}\n")

    print(f"Router address mapping has been saved to {output_file}")

if __name__ == "__main__":
    main()
