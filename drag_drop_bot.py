import os
import shutil

router_folder_corresp = {
    5 : "0cdfc724-c2af-4ebf-8da6-a9f2adb35c51",
	14 : "2afa751b-268b-4974-ba16-2bec9036dfef",
	1: "8d3e55f5-f7f3-4d21-9831-9d4a675795bc",
	10 : "13fc9f8b-3920-41f9-b198-c15bb6627c8c",
	3 : "284c438a-bbb6-4baf-83c6-fbe73b575d93",
	4 : "881e5b96-0fab-4ddd-9cb7-bf11b4c91459",
	13 : "30974b98-87ea-4f4c-b3b5-1511f964add5",
	9 : "94978ba0-84b5-466b-8d6a-2a80256d4744",
	7 : "a5bb323b-06e8-41e2-bd54-82f7cb27e8ca",
	8 : "b6194714-d95f-49dc-8564-37520e8c2868",
	11 : "d0347ac7-f0a2-469f-a8b9-604555db3a0c",
	6 : "dfb89e34-7823-4447-ade3-aa26347b1ea1",
	2 : "e30e197d-464f-4764-b50c-9c46200cf67a",
	12 : "fce06220-5b24-4eab-89c2-acdf0a798679"
	}

config_folder  = "config_files"
destination = "project-files/dynamips"

def move_configs():
    for router_number, folder_id in router_folder_corresp.items():
        src_file = os.path.join(config_folder, f"R{router_number}_startup.cfg")
        dest_folder = os.path.join(destination, folder_id, "configs")
        dest_file = os.path.join(dest_folder, f"R{router_number}_startup.cfg")

        if os.path.exists(src_file):
            shutil.move(src_file, dest_file)
            print(f"Moved {src_file} to {dest_file}")
        else:
            print(f"Source file not found: {src_file}")

if __name__ == "__main__":
    move_configs()