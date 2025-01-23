import json
import os 


script_dir = os.path.dirname(os.path.realpath(__file__))
file_path = os.path.join(script_dir, "intent.json")

with open(file_path, "r") as file:
    intent = json.load(file)

def generate_ip(interface_name, router_nbr, base_prefix):
    """
    Generate an IPv6 address for a given interface name and router number.
    """
    if interface_name.startswith("Loopback"):
        return f"{base_prefix}::{router_nbr}/128"
    elif interface_name.startswith("GigabitEthernet"):
        interface_parts = interface_name.split("/")
        main_interface = int(interface_parts[0][-1])
        sub_interface = int(interface_parts[1])
        return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::1/64"
    return None

def get_interface_subnet(router_name, interface_name, base_prefix):
    """
    Generate the IPv6 subnet for a given interface name and router number.
    """
    router_nbr = int(router_name.lstrip("R"))
    if interface_name.startswith("GigabitEthernet"):
        interface_parts = interface_name.split("/")
        main_interface = int(interface_parts[0][-1])  
        sub_interface = int(interface_parts[1]) 
        return f"{base_prefix}:{router_nbr}:{main_interface}:{sub_interface}::/64"
    return None


def generate_router_address_mapping(intent, base_prefixes, output_file="router_address_mapping.txt"):
    with open(output_file, "w") as file:
        file.write("Router Address Mapping:\n")
        file.write("=" * 50 + "\n")

        for as_entry in intent['network']:
            for as_name, as_data in as_entry.items():
                base_prefix = base_prefixes[as_name]
                file.write(f"\nAS: {as_name}\n")
                file.write("-" * 50 + "\n")

            
                for router_name, router_data in as_data["routers"].items():
                    file.write(f"Router: {router_name}\n")
                    file.write("Interfaces:\n")

                    # Generate addresses for each interface
                    for interface_name in router_data["interfaces"]:
                        ipv6_address = generate_ip(interface_name, int(router_name.lstrip("R")), base_prefix)
                        file.write(f"  {interface_name}: {ipv6_address}\n")

                    file.write("\n")
        print(f"Router address mapping written to {output_file}")


base_prefixes = {
    "AS_X": "2001:100:4",
    "AS_Y": "2001:200:4"
}


generate_router_address_mapping(intent, base_prefixes)



print(get_interface_subnet("R1", "GigabitEthernet1/0", "2001:100:4"))
print(get_interface_subnet("R1", "GigabitEthernet2/0", "2001:100:4"))
print(get_interface_subnet("R1", "GigabitEthernet1/1", "2001:100:4"))
