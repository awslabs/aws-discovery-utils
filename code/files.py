import sys
import os
import re
import glob
import argparse
import logging
import zipfile
import datetime as DT
import shutil

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zipfile", help="Zipfile to extract (fullpath).",
                         type=str)
    parser.add_argument("--target_directory", help="Path to directory in which to store the exported data. Default is current directory.",
                         type=str, default=os.getcwd())
    return parser.parse_args()

def extract_zip(zippedFile, toFolder, remove=False):
    logging.info(str.format("Extracting zipfile:{}", os.path.basename(zippedFile)))
    with zipfile.ZipFile(zippedFile, 'r') as zfile:
        zfile.extractall(path=toFolder)

    if remove:
        os.remove(zippedFile)

    for root, dirs, files in os.walk(toFolder):
        for filename in files:
            if re.search(r'\.zip$', filename):
                fileSpec = os.path.join(root, filename)
                if os.path.isfile(fileSpec):
                    extract_zip(fileSpec, root, True)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')
    args = parse_args()

    target_directory = os.path.join(args.target_directory)
    agent_datetime = os.path.getmtime(args.zipfile)
    iso_datetime = DT.datetime.utcfromtimestamp(agent_datetime).isoformat().replace(":", "") + "Z"  # maybe find the correct timezone later

    extract_zip(args.zipfile, target_directory)

    directories = ["destinationProcessConnection", "networkInterface", "osInfo", "process", "sourceProcessConnection", "systemPerformance"]

    # All directories have a results.json file
    for filename in glob.glob(target_directory + '/**/Agents/**/*.json', recursive=True):
        directory = os.path.dirname(filename)

        for d in directories:
            # Create the directories we need
            new_directory = os.path.join(directory, d)
            if not os.path.isdir(new_directory):
                try:
                    os.mkdir(new_directory)
                except OSError as e:
                    logging.info(str.format("Failed to create directory:{} - {}", dir, e))\

    for filename in glob.glob(target_directory + '/**/Agents/**/*.csv', recursive=True):
 
        directory = os.path.dirname(filename)
        file = os.path.basename(filename)
        name = os.path.splitext(file)[0]

        (agent, filetype) = name.split("_")

        if filetype in directories:
            if os.path.isdir(os.path.join(directory, filetype)):
                new_filename = os.path.join(directory, filetype, iso_datetime + "_" + agent + "_" + filetype + ".csv")

                logging.info(str.format("Moving :{} - {}", os.path.basename(filename), os.path.basename(new_filename)))
                shutil.move(filename, new_filename)
