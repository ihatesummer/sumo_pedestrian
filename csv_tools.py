import numpy as np
import pandas as pd
import os.path as osp
import xml.etree.ElementTree as Xet


def xml2csv(input_xml_name, out_path, max_time):
    xmlparse = Xet.parse(input_xml_name)
    root = xmlparse.getroot()
    rows = []
    for timestep in root:
        time = float(timestep.attrib['time'])
        if time > max_time:
            break
        for vehicle in timestep:
            id = int(float(vehicle.attrib['id']))
            pos_x = float(vehicle.attrib['x'])
            pos_y = float(vehicle.attrib['y'])
            # navigational standard
            # (0-360 degrees, going clockwise with 0
            # at the 12'o clock position)
            angle = float(vehicle.attrib['angle']) # degrees
            speed = float(vehicle.attrib['speed']) # [m/s]
            rows.append({"time [s]": time,
                        "id": id,
                        "pos_x": pos_x,
                        "pos_y": pos_y,
                        "angle [deg]": angle,
                        "speed [m/s]": speed})
    df = pd.DataFrame(rows)
    output_csv_name = input_xml_name[:-4] + ".csv"
    df.to_csv(osp.join(out_path, output_csv_name), index=False)
    return osp.join(out_path, output_csv_name)


def sort_by_time_and_id(input_csv_name):
    output_csv_name = input_csv_name[:-4] + "_sorted.csv"
    df = pd.read_csv(input_csv_name, delimiter=',')
    df = df.sort_values(["time [s]", "id"], ascending=[True, True])
    df.to_csv(output_csv_name, index=False)
    return output_csv_name


def survival_filter(input_csv_name, cumul_n_trips, trip_duration, time_step):
    output_csv_name = input_csv_name[:-4] + "_filtered.csv"
    df = pd.read_csv(input_csv_name, delimiter=',')
    last_time = df["time [s]"].iloc[-1]
    df_last_time = df.loc[df["time [s]"] == trip_duration-time_step]
    survivers = df_last_time["id"].tolist()
    n_survivers = len(survivers)
    df_filtered = df[df["id"].isin(survivers)]
    df_filtered = df_filtered[~df_filtered["time [s]"].between(0, 1-time_step)]

    new_id = np.linspace(0, n_survivers-1, n_survivers, dtype=int) + cumul_n_trips
    n_time_steps = (trip_duration-1) * (1/time_step)
    new_id_col = np.tile(new_id, int(n_time_steps))
    df_filtered["id"] = new_id_col

    df_filtered.to_csv(output_csv_name, index=False)
    return output_csv_name, n_survivers


def merge(merge_list):
    output_csv_name = "mobility_dataset.csv"

    df = pd.read_csv(merge_list[0], delimiter=',')
    for i in range(1, len(merge_list)):
        df2 = pd.read_csv(merge_list[i], delimiter=',')
        df = pd.concat([df, df2])
    df = df.sort_values(["time [s]", "id"], ascending=[True, True])
    df.to_csv(output_csv_name, index=False)
