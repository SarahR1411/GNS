# GNS
# Network Automation Tools

This repository contains Python scripts designed for automating the configuration and management of network routers in a multi-AS environment. The tools provide capabilities for generating configurations, assigning IP addresses, and organizing configuration files. Below is a detailed overview of the main files and their functionalities.

## File Descriptions

### 1. 'create_config.py'
This script is responsible for automating the creation of router configurations, including the assignment of IP addresses and protocol configurations.

#### Key Features:
- **Extract AS and Router Information**:
  - Opens an intent file to identify AS numbers (e.g., '1' for 'ASX' and '2' for 'ASY') and the routers belonging to them.
- **Automated IP Generation**:
  - Derives base prefix for the AS.
  - Extracts router numbers and locates routers and their links.
  - Verifies if an interface belongs to a link and creates unique keys for each link.
  - Ensures each link is assigned a unique subnet and shared prefix.
  - Assigns '::1 or '::2' to interfaces based on the router's role in the link.
- **Protocol Assignment**:
  - Automates the protocol-specific assignment of IP addresses.

---

### 2. 'router_ips.py'
This script handles the generation of IPv6 addresses for router interfaces and manages router address mappings.

#### Key Features:
- **Intent File Loading**:
  - Reads the intent file to determine router and AS configurations.
- **IP Address Generation**:
  - Creates unique IPv6 addresses for router interfaces, accounting for both peer links and standalone interfaces.
  - Base prefix for IPv6 addresses:
    - '2001:100:4::/64' for 'ASX'
    - '2001:200:4::/64' for 'ASY'
- **Router Address Mapping**:
  - Generates a mapping of router addresses based on the network topology and intent file.

---

### 3. 'drag_drop_bot.py'
This script manages the organization of configuration files and ensures that outdated files are cleaned up.

#### Key Features:
- **Folder Identification**:
  - Locates the folder corresponding to each router based on its name.
- **Configuration Cleanup**:
  - Deletes existing configuration files ('.cfg') and 'nvram' files.
- **File Management**:
  - Moves the newly generated configuration files into the appropriate router folders.

---

### 4. 'intent.json'
This is the input file that defines the network topology and configuration intent. It specifies the routers, their interfaces, links, and protocols.

#### Example Structure:
'''json
{
  "ASX": {
    "R1": {
      "interfaces": [...],
      "links": [
        {
          "interface": "...",
          "target_router": "...",
          "target_interface": "..."
        }
      ],
      "protocols": [...]
    }
  },
  "ASY": {
    "R9": {
      "interfaces": [...],
      "links": [...],
      "protocols": [...]
    }
  }
}
