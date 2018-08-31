"""
Copyright 2017-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.

Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance with the License. A copy of the License is located at

    http://aws.amazon.com/apache2.0/
    
or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
"""
import boto3
import datetime
import sys
import os
from urllib.request import urlopen, URLError, HTTPError
from zipfile import ZipFile
import shutil
import json
import time
import argparse
import logging
from io import StringIO

MAX_EXPORTS = 5         # Max number of concurrent export tasks
MAX_DESCRIBE_AGENTS = 100   # Max number of results from describe agents

# Returns datetime of given time string; space = True for space between days and hours
def get_time(time, space=False):
    if space:
        return datetime.datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
    return datetime.datetime.strptime(time,'%Y-%m-%dT%H:%M:%SZ')


# Begins export task for up to MAX_EXPORTS agents
def start_exporting(count):
    logging.debug(str.format("start_exporting - count={}, len(exporting_agents)={} (MAX_EXPORTS={}), len(agents_queue)={}", count, len(exporting_agents), MAX_EXPORTS, len(agents_queue)))
    while len(exporting_agents) < MAX_EXPORTS and len(agents_queue) > 0:
        agent = agents_queue.pop(0)
        count += 1
        logging.info(str.format("Starting export for agent {} ({}/{})", agent['agentId'], str(count), str(total_exports)))
        reg_time = get_time(agent['registeredTime'])
        last_health_time = get_time(agent['lastHealthPingTime'])
        if start_input != None:
            start_time = max(reg_time, start_input)
        else:
            start_time  = reg_time
        if end_input != None:
            final_end_time = min(last_health_time, end_input)
        else:
            final_end_time = last_health_time

        if start_time >= final_end_time:
            logging.info(str.format("Nothing to export for agent {} since registeredTime={} and lastHealthPingTime={}", agent['agentId'], reg_time, last_health_time))
            continue

        logging.info(str.format("Export for agent {} will start at {} (registeredTime={}) and end at {} (lastHealthPingTime={})", agent['agentId'], start_time, reg_time, final_end_time, last_health_time))
        try:
            response = client.start_export_task(filters=[{'name': 'agentIds', 'values': [agent['agentId']], 'condition': 'EQUALS'}], 
                                    startTime = start_time, endTime = min(start_time + datetime.timedelta(days=3), final_end_time))
            exporting_agents[agent['agentId']] = [start_time, final_end_time, response['exportId']]
        except Exception as e:
            if (type(e).__name__ == "OperationNotPermittedException"):
                last_word = e.message.split()[-1]
                if last_word == "another.":
                    # Full message: You have reached limit of maximum allowed concurrent exports. Please wait for current export tasks to finish before starting another.
                    agents_queue.insert(0, agent)
                    count -= 1
                    logging.info(str.format("start_exporting - Maximum number of concurrent exports exceeded. Requeuing agent {} and waiting...", agent['agentId']))
                    time.sleep(8)
                else:
                    # Full message: An error occurred (OperationNotPermittedException) when calling the StartExportTask operation: A successful export is already present Export ID: <export id>
                    logging.info(str.format("start_exporting - OperationNotPermittedException for agent {}: {}", agent['agentId'], e.message))
                    exporting_agents[agent['agentId']] = [start_time, final_end_time, last_word]
            else:
                raise(e)
    return count

def poll_exports(dir_name):
    done = []
    for agent_id in exporting_agents:
        logging.info("Trying to export data for " + agent_id + " from " + str(exporting_agents[agent_id][0]))
        export_response = client.describe_export_tasks(exportIds=[exporting_agents[agent_id][2]], filters=[{'name': 'agentIds', 'values': [agent_id], 'condition': 'EQUALS'}])
        if len(export_response['exportsInfo']) > 0:
            exports_info = export_response['exportsInfo'][0]
        else:
            continue

        # Extract data on successful export task
        if exports_info['exportStatus'] in ["SUCCEEDED", "FAILED"]:
            logging.info(str.format("    export {}", exports_info['exportStatus']))
            if exports_info['exportStatus'] == "SUCCEEDED":
                (actual_start, actual_end) = extract_exports(exports_info, agent_id, dir_name)
            else:
                logging.info(str.format("exportId {}: {} - {}", exports_info['exportId'], exports_info['exportStatus'], exports_info['statusMessage']))
                actual_end = exports_info['requestedEndTime'] if 'requestedEndTime' in exports_info else None
            # Set new start time to be end time of completed export
            exporting_agents[agent_id][0] = actual_end
            # If actual end time past final end time or start/end times equal, export is done for agent
            if exports_info['exportStatus'] == "FAILED" or actual_end == actual_start or actual_end >= exporting_agents[agent_id][1]:
                logging.info("Finished exporting agent " + agent_id)
                done.append(agent_id)
            # Otherwise, go to next export
            else:
                next_start_time = actual_end
                next_end_time = min(next_start_time + datetime.timedelta(days=3), exporting_agents[agent_id][1])
                logging.info(str.format("Next export for agent {} will continue at {} and end at {}", agent_id, next_start_time, next_end_time))
                try:
                    response = client.start_export_task(filters=[{'name': 'agentIds', 'values': [agent_id], 'condition': 'EQUALS'}], 
                                            startTime = next_start_time, endTime = next_end_time)
                    exporting_agents[agent_id][2] = response['exportId']
                # If successful export already exists, use exportId of existing export
                except Exception as e:
                    if (type(e).__name__ == "OperationNotPermittedException"):
                        last_word = e.message.split()[-1]
                        if (last_word == "another."): # Too many concurrent exports
                            logging.info("poll_exports - Maximum number of concurrent exports exceeded. Waiting...")
                            time.sleep(8)
                        else: # Export already exists
                            logging.info(str.format("poll_exports - OperationNotPermittedException for agent {}: {}", agent_id, e.message))
                            exporting_agents[agent_id][2] = last_word
                    else:
                        raise(e)
        elif exports_info['exportStatus'] == "IN_PROGRESS":
                        logging.info("    In progress; waiting...")
        else:
            logging.info(str.format("ERROR: Unknown status for exportId {}: {} - {}", exports_info['exportId'], exports_info['exportStatus'], exports_info['statusMessage']))
    for agent_id in done:
        del exporting_agents[agent_id]
    logging.debug(str.format("Exiting poll_exports - {} agents were done exporting, {} still exporting", len(done), len(exporting_agents)))

def download_with_retry(url, num_retries=5):
    for num_retry in range(num_retries):
        try:
            time.sleep(num_retry**2) # exponential backoff
            response = urlopen(url)
        except(HTTPError, e):
            logging.error(str.format("download of {} failed on {}th retry with HTTP Error: {}", url, num_retry, e.code))
        except(URLError, e):
            logging.error(str.format("download of {} failed on {}th retry with URL Error: {}", url, num_retry, e.reason))
        else:
            return response.read()

# Returns actual end time
def extract_exports(exports_info, agent_id, dir_name):
    logging.debug(str.format("extracting {}, url={}", exports_info['exportId'], exports_info['configurationsDownloadUrl']))
    zipped = download_with_retry(exports_info['configurationsDownloadUrl'])
    if zipped is None:
        msg = str.format("Unable to download {}", exports_info['configurationsDownloadUrl'])
        logging.error(msg)
        raise Exception(msg)
    # String representing start time of export
    actual_start = None
    actual_end = None
    export_meta = exporting_agents[agent_id]
    start_time, end_time, curr_id = export_meta[0], export_meta[1], export_meta[2]
    start_str = start_time.strftime('%Y-%m-%dT%H%M%SZ') + "_"
    with ZipFile(StringIO(zipped)) as zip_ref:
        for name in zip_ref.namelist():
            basename = os.path.basename(name)
            subdir = basename.split("_").pop().split(".")[0]
            if subdir == "results":
                json_file = zip_ref.open(name)
                d = json.load(json_file)
                if 'ActualEndTime' in d['ExportSummary']:
                    actual_start = get_time(d['ExportSummary']['ActualStartTime'], True)
                    actual_end = get_time(d['ExportSummary']['ActualEndTime'], True)
                # If 0 result files exported, may not have elements in ExportSummary so take requested as actual
                else:
                    actual_start = get_time(d['RequestedStartTime'], True)
                    actual_end = get_time(d['RequestedEndTime'], True)
            target_dir = os.path.join(dir_name, "agentExports", agent_id, subdir)
            try:
                os.makedirs(target_dir)
            except OSError: # already exists
                pass
            source = zip_ref.open(name)
            with open(os.path.join(target_dir, start_str + basename), 'w') as target:
                shutil.copyfileobj(source, target)
    return (actual_start, actual_end)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", help="Path to directory in which to store the exported data. Default is current directory.",
                         type=str, default=os.getcwd())
    parser.add_argument("--start-time", help="The start timestamp from which to start collecting exported data. Format: YYYY-MM-DDTHH:MM", 
                        type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M'))
    parser.add_argument("--end-time", help="The end timestamp until which exported data will be collected. Format: YYYY-MM-DDTHH:MM", 
                        type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%dT%H:%M'))
    parser.add_argument("--filters", help="List of agentIds for which exported data will be collected.", nargs='+', type=str)
    parser.add_argument("--log-file", help="File name where logs will be written, instead of the console", dest="log_file")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    dir_name = args.directory
    start_input = args.start_time
    end_input = args.end_time
    filters = args.filters
    log_file = args.log_file

    if log_file:
        print(str.format("Debug log file {} configured; this will be the last message to the console.", log_file))
        logging.basicConfig(filename=log_file, level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(name)s: %(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

    client = boto3.client('discovery')

    logging.info(str.format("Querying Discovery Service for agents to export. directory={}, start_time={}, end_time={}, filters={}", dir_name, start_input, end_input, filters))
    agents_queue = []
    moreAgents = True
    nextToken=""
    while moreAgents:
        response = client.describe_agents(maxResults=MAX_DESCRIBE_AGENTS, nextToken=nextToken)
        if filters:
            agents_queue += [agent for agent in response['agentsInfo'] if agent['agentId'] in filters and 
                        "connector" not in agent['agentType'].lower()]
        else:
            agents_queue += [agent for agent in response['agentsInfo'] if "connector" not in agent['agentType'].lower()]
        if 'nextToken' in response:
            nextToken = response['nextToken']
        else:
            moreAgents = False

    #Maps each currently exporting agent to [next start time, final end time, current exportId]
    exporting_agents = {}
    total_exports = len(agents_queue)
    logging.info("Beginning export for " + str(total_exports) + " agents.")
    count = 0
    count = start_exporting(count)
    while len(agents_queue) > 0 or len(exporting_agents) > 0:
        logging.debug(str.format("Main export loop - {} agents in export queue, {} agents currently waiting to export, count={}", len(agents_queue), len(exporting_agents), count))
        poll_exports(dir_name)
        time.sleep(2)
        count = start_exporting(count)
    logging.info("Finished exporting all agents.")

