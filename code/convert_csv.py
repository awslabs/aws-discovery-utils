import os
import sys
import argparse
import shutil
from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext
from pyspark.sql.types import *
import time
import csv
import datetime
import boto3
import glob
import re

# Network interface schema
NETWORK_SCHEMA = StructType([
    StructField("account_number", LongType(), True),
    StructField("agent_id", StringType(), True),
    StructField("name", StringType(), True),
    StructField("mac_address", StringType(), True),
    StructField("family", StringType(), True),
    StructField("ip_address", StringType(), True),
    StructField("gateway", StringType(), True),
    StructField("net_mask", StringType(), True),
    StructField("timestamp", TimestampType(), True)])

# Process Connection schema (for both source/destination)
PC_SCHEMA = StructType([
    StructField("account_number", LongType(), True),
    StructField("agent_id", StringType(), True),
    StructField("source_ip", StringType(), True),
    StructField("source_port", IntegerType(), True),
    StructField("destination_ip", StringType(), True),
    StructField("destination_port", IntegerType(), True),
    StructField("ip_version", StringType(), True),
    StructField("transport_protocol", StringType(), True),
    StructField("agent_assigned_process_id", StringType(), True),
    StructField("agent_creation_date", TimestampType(), True)])

# OS Info schema
OS_SCHEMA = StructType([
    StructField("account_number", LongType(), True),
    StructField("agent_id", StringType(), True),
    StructField("os_name", StringType(), True),
    StructField("os_version", StringType(), True),
    StructField("cpu_type", StringType(), True),
    StructField("host_name", StringType(), True),
    StructField("hypervisor", StringType(), True),
    StructField("timestamp", TimestampType(), True)])

PROCESS_SCHEMA = StructType([
    StructField("account_number", LongType(), True),
    StructField("agent_id", StringType(), True),
    StructField("agent_assigned_process_id", StringType(), True),
    StructField("is_system", BooleanType(), True),
    StructField("name", StringType(), True),
    StructField("cmd_line", StringType(), True),
    StructField("path", StringType(), True),
    StructField("agent_provided_timestamp", TimestampType(), True)])

# System performance schema
PERF_SCHEMA = StructType([
    StructField("account_number", LongType(), True),
    StructField("agent_id", StringType(), True),
    StructField("total_disk_bytes_read_per_sec_in_kbps", DoubleType(), True),
    StructField("total_disk_bytes_written_per_sec_in_kbps", DoubleType(), True),
    StructField("total_disk_read_ops_per_sec", DoubleType(), True),
    StructField("total_disk_write_ops_per_sec", DoubleType(), True),
    StructField("total_network_bytes_read_per_sec_in_kbps", DoubleType(), True),
    StructField("total_network_bytes_written_per_sec_in_kbps", DoubleType(), True),
    StructField("total_num_logical_processors", IntegerType(), True),
    StructField("total_num_cores", IntegerType(), True),
    StructField("total_num_cpus", IntegerType(), True),
    StructField("total_num_disks", IntegerType(), True),
    StructField("total_num_network_cards", IntegerType(), True),
    StructField("total_cpu_usage_pct", DoubleType(), True),
    StructField("total_disk_size_in_gb", DoubleType(), True),
    StructField("total_disk_free_size_in_gb", DoubleType(), True),
    StructField("total_ram_in_mb", DoubleType(), True),
    StructField("total_free_ram_in_mb", DoubleType(), True),
    StructField("timestamp", TimestampType(), True)])

# Maps export types to their schema for pyspark
EXPORT_TYPES = {
    "destinationProcessConnection" : PC_SCHEMA,
    "networkInterface": NETWORK_SCHEMA,
    "osInfo": OS_SCHEMA,
    "process": PROCESS_SCHEMA,
    "sourceProcessConnection": PC_SCHEMA,
    "systemPerformance": PERF_SCHEMA
}

def get_subdirs(directory):
    return [name for name in os.listdir(directory) if os.path.isdir(os.path.join(directory, name))]

# Returns pyspark dataframe for given file and export type, pruning the header
def get_dataframe(filename, export_type):
    split_filename = filename.split('/')
    print("Converting " + split_filename[-1] + " for agent " + split_filename[-3] + "...")
    text_file = sc.textFile(filename)
    header = text_file.first()
    headerless_file = text_file.filter(lambda x: x != header)
    rdd = headerless_file.map(lambda line: parse_line(line, export_type))
    return sqlContext.createDataFrame(rdd, EXPORT_TYPES[export_type])

def is_agent_id(maybe_agent_id):
    return re.match("[io]-[0-9a-z]{17}$", maybe_agent_id)

def get_parquet_files(dir_path):
    # Concatenates same csv file types as parquet files within agentsExports folder, under "parquetExports" subdir
    try:
        os.makedirs(target_dir)
    except OSError: # already exists
        pass
    dfs = {}
    # get directory listing we will iterate over
    if filters:
        agent_dirs = [x for x in get_subdirs(dir_path) if x in filters]
    else:
        agent_dirs = get_subdirs(dir_path)

    # build a single parquet file for each export type for each agent
    for agent in agent_dirs:
        if not is_agent_id(agent):
            continue
        # Initialize empty data frames to load in csv files for all export types
        for export_type in EXPORT_TYPES:
            empty_df = sqlContext.createDataFrame(sc.emptyRDD(), EXPORT_TYPES[export_type])
            dfs[export_type] = empty_df

        agent_export_types = [export_type for export_type in get_subdirs(os.path.join(dir_path, agent)) if export_type != "results"]
        for export_type in agent_export_types:
            exports = sorted(os.listdir(os.path.join(dir_path, agent, export_type)))
            date = exports[0][:18] # export files are of the form 2017-11-04T000100Z_<accountNumber>_<type>.csv
            print(str.format("Loading {} exported CSV files of type {} for agent {}, will be labeled with {}", len(exports), export_type, agent, date))
            for export in exports:
                # Remove colons if necessary from filename for compatibility with Spark
                export_file = os.path.join(dir_path, agent, export_type, export)
                if ":" in export_file:
                    new_name = export_file.replace(":", "")
                    os.rename(export_file, new_name)
                    export_file = new_name
                # Get dataframe for non-hidden CSV files
                if '.csv' in export_file:
                    df = sqlContext.read.format('com.databricks.spark.csv').options(header='true').schema(EXPORT_TYPES[export_type]).load(export_file)
                    dfs[export_type] = dfs[export_type].unionAll(df)

            # Write the dataframe for each export type to a subdirectory of the target directory
            print(" Converting to parquet...")
            new_name = str.format("{}_{}.parquet", date, agent)
            subfolder_dir = os.path.join(target_dir, export_type + "-" + new_name)
            if os.path.isdir(subfolder_dir):
                shutil.rmtree(subfolder_dir) # an empty target directory is required by spark to write out the dataframe
            #dfs[export_type].toPandas().to_csv(os.path.join(target_dir, export_type + ".csv"))
            dfs[export_type].coalesce(1).write.parquet(subfolder_dir)
            parquet_file = glob.glob(os.path.join(subfolder_dir, "part-*"))[0]
            os.rename(parquet_file, os.path.join(subfolder_dir, new_name))

            # Upload to S3
            print("   Uploading to S3...")
            for parquet_file in os.listdir(subfolder_dir):
                if not parquet_file.startswith('.') and not parquet_file.startswith('_'):
                    s3.upload_file(os.path.join(subfolder_dir, parquet_file), bucket_name, os.path.join(export_type, parquet_file))
            print("    Successful!")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", help="Path to directory containing agentExports folder. Default set to current directory.",
                        type=str, default=os.getcwd())
    parser.add_argument("--filters", help="List of agentIds for which exported data will be collected.", nargs='+', type=str)
    parser.add_argument("bucket_name", metavar="bucket-name", help="Name of S3 bucket where exports converted to parquet format will be stored.", type=str)
    parser.add_argument("region", help="Region for S3 bucket.", type=str)
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    dir_path = os.path.join(args.directory, "agentExports")
    filters = args.filters
    bucket_name = args.bucket_name
    region = args.region
    if not os.path.isdir(dir_path):
        print("Cannot find agentExports in given directory.")
        sys.exit(0)

    # Set memory as needed
    conf = (SparkConf()
            .setMaster("local")
            .setAppName("CSV2Parquet")
            .set("spark.executor.memory", "3g"))
    sc = SparkContext(conf=conf)
    sqlContext = SQLContext(sc)

    target_dir = os.path.join(dir_path, "parquetExports")
    #s3 = boto3.client('s3', aws_access_key_id="ACCESSKEY", aws_secret_access_key="SECRETACCESSKEY")
    s3 = boto3.client('s3')
    try:
        s3.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': region})
    except Exception as e:
        if (type(e).__name__ == "BucketAlreadyOwnedByYou"):
            pass
        else:
            raise(e)
    get_parquet_files(dir_path)
