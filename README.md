# AWS Discovery Utilities
Utilities for use with the AWS Discovery Service API to export and organise data for later analysis using Athena.

## Prerequisites

* Docker - [download](https://www.docker.com/community-edition#/download)
* Docker Compose - [notes](https://docs.docker.com/compose/install/)

## Services

### Mapped Ports

The following services are available as part of the Docker Compose stack.

|Service|Address|
|:--|:--|
|Spark Console|[http://localhost:8080](http://localhost:8080)|

### Mapped directories

|Host|Container|Notes|
|:--|:--|:--|
|`./conf/master`|`/conf/`|Spark config files|
|`./data`|`/tmp/data`|Data files|
|`./code`|`/code/`|Python code files|

## Docker building and running

### Build

Clone the repository and then from the cloned directory:

	$ make
	
This will take some time the first time as various Docker images are downloaded to your computer.

### Check

To check the containers are running as expected:

	$ docker-compose ps
	
This will show that both containers are running with their mapped ports as below:

```
    Name                  Command               State                                                                             Ports
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
aws_master_1   bin/spark-class org.apache ...   Up      0.0.0.0:4040->4040/tcp, 0.0.0.0:6066->6066/tcp, 7001/tcp, 7002/tcp, 7003/tcp, 7004/tcp, 7005/tcp, 7006/tcp, 0.0.0.0:7077->7077/tcp, 0.0.0.0:8080->8080/tcp
aws_worker_1   bin/spark-class org.apache ...   Up      7012/tcp, 7013/tcp, 7014/tcp, 7015/tcp, 7016/tcp, 0.0.0.0:8081->8081/tcp, 8881/tcp
```
	
### Cleaning up

Once you've finished

	$ make clean
	
Will shutdown the containers and generally clean things up.

### Running the commands

#### Running order
The tools within this repository are to be used based on where the data you want examine currently resides.

#### Data resides in the Application Discovery Tool:

* Export the data from the application discovery tool to a local directory:

```
$ docker-compose exec master python /code/export.py --directory /tmp/data
```

* Convert the exported data into Parquet for use in Athena:
	
```
$ docker-compose exec master python /code/convert_csv.py --directory /tmp/data --bucket-name [bucket-name] --region [region]
```
	
* Load data into Athena using `discovery_athena.ddl`
	
#### I have a zipfile of exported data:

* Unzip the zipfile and move / rename into the structure needed by `convert_csv.py`:

```
$ docker-compose exec master python /code/files.py --target_directory /tmp/data/source --zipfile /tmp/data/awsdiscovery.zip
```

* Convert the exported data into Parquet for use in Athena:
	
```
$ docker-compose exec master python /code/convert_csv.py --directory /tmp/data --bucket-name [bucket-name] --region [region]
```

* Load data into Athena using `discovery_athena.ddl`

## Tools

### Export Utility
Using the export.py script, you can collect and organize Discovery data to a specified local location.

#### Usage 
The script can be called by running `python export.py`. There are several optional command-line arguments you can pass in:

* `--directory [path to directory]` : Path to directory (as string) in which to store the exported data. If no directory is provided, the default is the current working directory. 
* `--start-time [start timestamp]` : The start timestamp from which to start exporting data. If no start timestamp is provided or an agent was registered after the start timestamp, data will be exported starting from registration time. Example format `(YYYY-MM-DDTHH:MM)`: `2017-05-10T12:00`.
* `--end-time [end timestamp]`: The end timestamp until which data will be exported. If no end timestamp is provided or an agent's last health ping was before the end timestamp, data will be exported until the time of last health ping. Datetime format same as `--start-time`. 
* `--filters [list of agentIds]` : If filters are enabled, discovery data will be exported for only agents with agentIds matching those provided in the list (as strings). If no filters are provided, exports will be run for all agents.
* `--log-file [file name]` : If this option is included, detailed logging of the export process is sent to the named file instead of the console.

#### Resulting file structure
After exporting is complete, an 'agentsExports' directory will be created, with subfolders for each agent. Within each subfolder will be more subfolders categorizing exported data by their types (e.g. osInfo, process, systemPerformance, etc.). The "results" subfolder contains metadata about each export task that was run. Inside these subfolders are the exported CSV files, with the start timestamp of the data export as part of the filename.

### Convert CSV Utility
Using the `convert_csv.py` script, you can convert the CSV output files from export.py to [Apache Parquet](https://parquet.apache.org/) files and upload them to the specified S3 bucket. Once in S3, you can create [Athena](https://aws.amazon.com/athena/) tables using discovery_athena.ddl.

#### Usage
Required parameters:

* `--bucket-name [S3 bucket name]` : Name of the S3 bucket where Parquet files will be written
* `--region [AWS region name]` : Region for the named S3 bucket, e.g., us-west-2

Optionally two additional paramters can be specified:

* `--directory [path to directory]` : Path to directory (as string) in which to find the exported CSV data files. If no directory is provided, the default is 'agentExports' from the current working directory.
* `--filters [list of agentIds]` : List of agentIds for which exported data will be converted.

### Files Utility
Using the `files.py` script you can take an already exported set of data from Application Discovery tool and move / rename the files into a structure that `convert_csv.py` can use to create the Parquet files.  The resultant file structure is the same as created by `export.py` and is described above.

#### Usage
Required parameters:

* `--target_directory [path to directory]` : Path to directory (as string) in which to create the exported CSV data files.
* `--zipfile [file location of source zipfile]` : File location (as string) to the location of the source zipfile on the docker container (likely to be `/tmp/data/zipfile.zip` if using the `./data` directory)

### Creating tables in Athena
Once the Parquet files are in S3, modify the statements in `discovery_athena.ddl` to reference the correct bucket. Run each command using the Athena console within a new or existing database, and you should be able to start querying your exported Discovery data.
