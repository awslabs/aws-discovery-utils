# AWS Discovery Utilities
Utilities for use with the AWS Discovery Service API.
## Export Utility
Using the export.py script, you can collect and organize Discovery data to a specified local location.

### Set up
Before running the export script, make sure you have boto3 installed with `pip install boto3` and have the proper AWS credentials set according to the instructions [here](http://boto3.readthedocs.io/en/latest/guide/quickstart.html). Please refer to the boto3 documentation for any related installation issues. 

### Usage 
The script can be called by running `python export.py`. There are several optional command-line arguments you can pass in:
* `--directory [path to directory]` : Path to directory (as string) in which to store the exported data. If no directory is provided, the default is the current working directory. 
* `--start-time [start timestamp]` : The start timestamp from which to start exporting data. If no start timestamp is provided or an agent was registered after the start timestamp, data will be exported starting from registration time. Example format `(YYYY-MM-DDTHH:MM)`: `2017-05-10T12:00`.
* `--end-time [end timestamp]`: The end timestamp until which data will be exported. If no end timestamp is provided or an agent's last health ping was before the end timestamp, data will be exported until the time of last health ping. Datetime format same as `--start-time`. 
* `--filters [list of agentIds]` : If filters are enabled, discovery data will be exported for only agents with agentIds matching those provided in the list (as strings). If no filters are provided, exports will be run for all agents.
* `--sparse-logging` : If this option is included, disables detailed logging of export process.

### Resulting file structure
After exporting is complete, an 'agentsExports' directory will be created, with subfolders for each agent. Within each subfolder will be more subfolders categorizing exported data by their types (e.g. osInfo, process, systemPerformance, etc.). The "results" subfolder contains metadata about each export task that was run. Inside these subfolders are the exported CSV files, with the start timestamp of the data export as part of the filename. 
