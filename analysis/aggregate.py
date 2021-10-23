import argparse
import pandas as pd
import numpy as np
import glob
import json
import os
import time


def get_aggregatable_dirs(dirs):
    directories = list()
    # remove directory if parsed-files directory does not exist in it
    for directory in dirs:
        if os.path.isdir(os.path.join(args.path, directory, "parsed-files")):
            directories.append(directory)
    return directories


def read_parsed_data(path):
    all_files = glob.glob(path + "/*.csv")

    li = []

    for filename in all_files:
        df = pd.read_csv(filename, sep='\t')
        li.append(df)

    df = pd.concat(li, axis=0, ignore_index=True)
    df = df.sort_values(by=['frame.time'])
    return df


def get_bytes_sent(dataframe, directory):
    src = dataframe.groupby("ip.src")['frame.len'].sum().reset_index(name=directory).set_index('ip.src')
    return src


def get_bytes_received(dataframe, directory):
    dst = dataframe.groupby("ip.dst")['frame.len'].sum().reset_index(name=directory).set_index('ip.dst')
    return dst


def create_parsed_sent(path_arg, dirs):
    if os.path.exists("{}bytes_sent.json".format(path_arg)):
        source_addresses = pd.read_json(path_or_buf="{}bytes_sent.json".format(path_arg))
        for col in source_addresses.columns:
            try:
                dirs.remove(col)
            except ValueError:
                continue
        os.system("rm {}bytes_sent.json".format(path_arg))
    else:
        source_addresses = pd.DataFrame()

    for i in range(len(dirs)):
        df = read_parsed_data("{}{}/parsed-files/".format(path_arg, dirs[i]))
        src = get_bytes_sent(df, dirs[i])
        source_addresses = pd.concat([source_addresses, src], axis=1)

    source_addresses.to_json(path_or_buf="{}bytes_sent.json".format(path_arg))


def create_joint_sent_received(path_arg, dirs):
    for directory in dirs:
        if os.path.exists(os.path.join(path_arg, directory, "parsed-files", "joint_sent_received.json")):
            continue
        else:
            df = read_parsed_data(os.path.join(path_arg, directory, "parsed-files"))
            table = df.groupby(["ip.src", "ip.dst"])['frame.len'].sum().reset_index()
            table.to_json(path_or_buf=os.path.join(path_arg, directory, "parsed-files", "joint_sent_received.json"))


def create_bytes_per_sec(path_arg, dirs):
    for directory in dirs:
        if os.path.exists(os.path.join(path_arg, directory, "parsed-files", "bytes_per_sec.json")):
            continue
        else:
            df = read_parsed_data(os.path.join(path_arg, directory, "parsed-files"))
            try:
                df['frame.time'] = pd.to_datetime(df['frame.time'], format='%b %d, %Y %H:%M:%S.%f CEST')
            except ValueError:
                df['frame.time'] = pd.to_datetime(df['frame.time'], format='%b %d, %Y %H:%M:%S.%f CET')
            bytes_per_sec = df.resample("0.001S", on='frame.time').sum()
            bytes_per_sec = bytes_per_sec[['frame.len']]
            bytes_per_sec.reset_index(level=0, inplace=True)
            bytes_per_sec.to_json(path_or_buf=os.path.join(path_arg, directory, "parsed-files", "bytes_per_sec.json"))
            util = df.set_index('frame.time').groupby(["ip.src", "ip.dst"]).resample('0.001S').sum().reset_index()
            util_pvt = pd.pivot_table(util, values="frame.len", index=["frame.time"], columns=["ip.src", "ip.dst"],
                                      fill_value=0)
            util_pvt.to_json(path_or_buf=os.path.join(path_arg, directory, "parsed-files", "utilization.json"))


def create_number_flows(path_arg, dirs):
    no_flows = dict()
    flows = pd.DataFrame()
    if os.path.exists(os.path.join(path_arg, "number_flows.json")):
        flows = pd.read_json(path_or_buf=os.path.join(path_arg, "number_flows.json"))
        for index in flows.index:
            try:
                dirs.remove(index)
            except ValueError:
                continue
        os.system("rm {}number_flows.json".format(path_arg))
    for directory in dirs:
        df = read_parsed_data(os.path.join(path_arg, directory, "parsed-files"))
        no_flows[directory] = len(
            df.groupby(['ip.src', 'ip.dst', 'tcp.srcport', 'tcp.dstport']).size().to_frame(name='size').reset_index())

    flow_df = pd.DataFrame.from_dict(no_flows, orient='index', columns=["flows"])
    flow_df = pd.concat([flows, flow_df])
    flow_df.to_json(path_or_buf=os.path.join(path_arg, "number_flows.json"))


def create_flow_cdf(path_arg, dirs):
    for directory in dirs:
        if os.path.exists(os.path.join(path_arg, directory, "parsed-files", "flow_cdf.json")):
            continue
        else:
            df = read_parsed_data(os.path.join(path_arg, directory, "parsed-files"))
            stat = df.groupby(['ip.src', 'ip.dst', 'tcp.srcport', 'tcp.dstport'])['frame.len'].sum().to_frame(
                name='value').reset_index()
            stats_df = stat.groupby('value')['value'].agg('count').pipe(pd.DataFrame).rename(
                columns={'value': 'frequency'})
            stats_df['pdf'] = stats_df['frequency'] / sum(stats_df['frequency'])
            stats_df['cdf'] = stats_df['pdf'].cumsum()
            stats_df = stats_df.reset_index()
            stats_df.to_json(path_or_buf=os.path.join(path_arg, directory, "parsed-files", "flow_cdf.json"))


def create_flow_arrrival_times(path_arg, dirs):
    for directory in dirs:
        if os.path.exists(os.path.join(path_arg, directory, "parsed-files", "flow_arrival.json")):
            continue
        else:
            df = read_parsed_data(os.path.join(path_arg, directory, "parsed-files"))
            x = df.groupby(['ip.src', 'ip.dst', 'tcp.srcport', 'tcp.dstport'])['frame.len'].sum().to_frame(
                name='value').reset_index()
            out = pd.DataFrame()
            for (ip1, ip2, p1, p2, val) in zip(x["ip.src"], x["ip.dst"], x["tcp.srcport"], x["tcp.dstport"],
                                               x["value"]):
                idx = np.where((df["ip.src"] == ip1) & (df["ip.dst"] == ip2) & (df['tcp.srcport'] == p1) & (
                        df['tcp.dstport'] == p2))
                out = out.append({'value': val, 'ip.src': ip1, 'ip.dst': ip2, 'tcp.srcport': p1, 'tcp.dstport': p2,
                                  'arrival.time': df["frame.time"][idx[0][0]],
                                  'departure.time': df["frame.time"][idx[0][-1]]}, ignore_index=True)
            out.to_json(path_or_buf=os.path.join(path_arg, directory, "parsed-files", "flow_arrival.json"))


def create_temporal_flows(path_arg, dirs):
    for directory in dirs:
        if os.path.exists(os.path.join(path_arg, directory, "parsed-files", "temporal_flow.json")):
            continue
        else:
            df = read_parsed_data(os.path.join(path_arg, directory, "parsed-files"))
            df['frame.time'] = pd.to_datetime(df['frame.time'], format='%b %d, %Y %H:%M:%S.%f CEST')
            t0 = df['frame.time'].min()
            df['frame.time'] -= t0
            x = df.groupby(['ip.src', 'ip.dst', 'tcp.srcport', 'tcp.dstport']).resample('10S', on='frame.time').sum()
            x = x["frame.len"]
            x = x.reset_index(level="frame.time")
            out = dict()
            i = 1
            for index in x.index.unique():
                out[f"flow{i}"] = x.loc[index]
                out[f"flow{i}"].reset_index(inplace=True)
                out[f"flow{i}"]["frame.time"] = out[f"flow{i}"]["frame.time"].dt.floor('S')
                out[f"flow{i}"]["frame.time"] = out[f"flow{i}"]["frame.time"].dt.seconds
                out[f"flow{i}"] = out[f"flow{i}"][["frame.time", "frame.len"]]
                out[f"flow{i}"].set_index("frame.time", inplace=True)
                out[f"flow{i}"] = out[f"flow{i}"].to_json()
                i += 1
        with open(os.path.join(path_arg, directory, "parsed-files", "temporal_flow.json"), 'w') as outfile:
            json.dump(out, outfile)


if __name__ == "__main__":
    # Give the main folder! ("/mnt/nas-dml/new-runs/")
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=None, required=True)
    args = parser.parse_args()

    # TODO REFACTOR for efficiency (read data only once)
    t1 = time.time()

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_parsed_sent(args.path, directories)

    t2 = time.time()
    print('stage 1: {} sec'.format(t2 - t1))

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_joint_sent_received(args.path, directories)

    t3 = time.time()
    print('stage 4: {} sec'.format(t3 - t2))

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_bytes_per_sec(args.path, directories)

    t4 = time.time()
    print('stage 5: {} sec'.format(t4 - t3))

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_number_flows(args.path, directories)

    t5 = time.time()
    print('stage 6: {} sec'.format(t5 - t4))

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_flow_cdf(args.path, directories)

    t6 = time.time()
    print('stage 7: {} sec'.format(t6 - t5))

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_flow_arrrival_times(args.path, directories)

    t7 = time.time()
    print('stage 8: {} sec'.format(t7 - t6))

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    directories = get_aggregatable_dirs(dirs)
    create_temporal_flows(args.path, directories)

    t_final = time.time()
    print('all: {} sec'.format(t_final - t1))
