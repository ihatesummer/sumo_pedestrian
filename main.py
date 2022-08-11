import subprocess
import csv_tools
import os
import os.path as osp
import argparse

parser = argparse.ArgumentParser(description="Arguments for generating mobility")
parser.add_argument("--input_map", "-i", help="Map file (*.net.xml)")
parser.add_argument("--duration", "-d", type=float, help="Trip duration")
parser.add_argument("--no_vehicle", "-n", type=int, help="Total number of vehicles")
parser.add_argument("--batch_size", "-b", type=int, help="Number of vehicles per batch")
parser.add_argument("--step_size", "-s", type=float, help="Simulation time step (e.g. 0.01 for 10ms)")
args = parser.parse_args()
FILE_PATH = "outputs"
INPUT_MAP = args.input_map
TRIP_DURATION = args.duration
N_TRIPS = args.no_vehicle
BATCH_SIZE = args.batch_size
TIME_STEP = args.step_size

def main():
    write_config_file()
    if not osp.exists(FILE_PATH):
        os.mkdir(FILE_PATH)
    n_cumulated_trips = 0
    batch_no = 0
    merge_list = []
    while n_cumulated_trips < N_TRIPS:
        print("*"*10 + f"Batch {batch_no}" + "*"*10)
        script_trip_gen = get_script_trip_generation(batch_no)
        script_router = get_script_router(batch_no)
        script_rerouter = get_script_rerouter()
        script_run_sumo = get_script_run_sumo(batch_no)
        subprocess.run(script_trip_gen, shell=True)
        subprocess.run(script_router, shell=True)
        subprocess.run(script_rerouter, shell=True)
        subprocess.run(script_run_sumo, shell=True)
        csv_file = csv_tools.xml2csv(f"mobility_{batch_no}.xml", FILE_PATH, TRIP_DURATION)
        move_to_folder(f"trip_{batch_no}.xml", FILE_PATH)
        move_to_folder(f"mobility_{batch_no}.xml", FILE_PATH)
        
        sorted = csv_tools.sort_by_time_and_id(csv_file)
        filtered, n_trips = csv_tools.survival_filter(sorted, n_cumulated_trips, TRIP_DURATION, TIME_STEP)
        n_cumulated_trips += n_trips
        merge_list.append(filtered)
        print(f"{n_cumulated_trips} trips generated.")
        batch_no += 1
    csv_tools.merge(merge_list)


def move_to_folder(file, folder):
    os.replace(file, osp.join(folder, file))


def get_script_trip_generation(batch_no):
    p = 1/BATCH_SIZE
    return ["randomTrips.py",
            "-n", f"{INPUT_MAP}",
            "-o", f"trip_{batch_no}.xml",
            "-b", "0", "-e", "1", "-p", f"{p}",
            "--pedestrians", "--random"]


def get_script_router(batch_no):
    return ["duarouter", "-n", f"{INPUT_MAP}",
            "--route-files", f"trip_{batch_no}.xml",
            "-o", "osm.rou.xml", "-e", f"{TRIP_DURATION}"]


def get_script_rerouter():
    return ["generateContinuousRerouters.py",
            "-n", f"{INPUT_MAP}", "-o", "rerouter.add.xml",
            "-e", f"{TRIP_DURATION}"]


def get_script_run_sumo(batch_no):
    return ["sumo", "-c", "custom.sumocfg",
            "--step-length", f"{TIME_STEP}",
            "--fcd-output", f"mobility_{batch_no}.xml"]


def write_config_file():
    with open("custom.sumocfg", "w") as f:
        f.write('<configuration>\n')
        f.write('\t<input>\n')
        f.write(f'\t\t<net-file value="{INPUT_MAP}"/>\n')
        f.write('\t\t<route-files value="osm.rou.xml"/>\n')
        f.write('\t\t<additional-files value="rerouter.add.xml"/>\n')
        f.write('\t</input>\n') 
        f.write('\t<time>\n') 
        f.write('\t\t<begin value="0"/>\n')
        f.write(f'\t\t<end value="{TRIP_DURATION}"/>\n')
        f.write('\t</time>\n')
        f.write('\t<output>\n')
        f.write('\t\t<fcd-output value="custom.output.xml"/>\n')
        f.write('\t</output>\n')
        f.write('</configuration>\n')


def move_files():
    for file in os.listdir():
        if file[:4] == "trip" or file[:8] == "mobility":
            os.replace(file, osp.join(FILE_PATH, file))


if __name__=="__main__":
    main()
