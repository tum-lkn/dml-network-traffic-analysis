import os
import subprocess
import argparse

BASIC_TSHARK_COMMAND = [
    '-T', 'fields',
    '-E', 'header=y',
    '-e', 'frame.time',
    '-e', 'ip.src',
    '-e', 'ip.dst',
    '-e', 'tcp.srcport',
    '-e', 'tcp.dstport',
    '-e', 'frame.interface_name',
    '-e', 'frame.len'
]


def find_unparsed_pcap_files(path):
    files_to_parse = list()

    parsed_path = path + "parsed-files/"
    main_files = os.listdir(path)

    if not os.path.exists(parsed_path):
        os.mkdir(parsed_path)
        for file in main_files:
            if f'.pcap' in file:
                files_to_parse.append(file)
    else:
        parsed_files = os.listdir(parsed_path)
        for file in main_files:
            if f'.pcap' in file:
                if f'{file[:-5]}.csv' not in parsed_files:
                    files_to_parse.append(file)

    return files_to_parse


def parse_pcap_file(pcap_file):
    """
    Takes a pcap file and parses it to a csv file.

    Args:
        pcap_file: the absolute file path

    Returns:
        None
    """

    filename = pcap_file[:-5]

    csv_file = open("{}.csv".format(filename), "w")
    subprocess.call(
        [
            'tshark',
            '-r', "{}".format(pcap_file)
        ] + BASIC_TSHARK_COMMAND,
        stdout=csv_file
    )
    csv_file.close()


if __name__ == "__main__":
    # Give the main folder!
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=None)
    args = parser.parse_args()

    if args.path is None:
        raise RuntimeError("No path provided")

    dirs = [d for d in os.listdir(args.path) if os.path.isdir(os.path.join(args.path, d))]
    print(f'Found {len(dirs)} directories.')

    for i in range(len(dirs)):
        new_path = args.path + dirs[i] + "/"
        print(f'Starting with directory {new_path}')

        pcap_files = find_unparsed_pcap_files(new_path)
        print(f'Found {len(pcap_files)} files to parse in this directory.')

        for file in pcap_files:
            parse_pcap_file(f"{new_path}{file}")
            print(f'Finished parsing {file}.')

        os.system(f"mv {new_path}*.csv {new_path}parsed-files/")

    print('Done.')
