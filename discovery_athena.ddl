CREATE EXTERNAL TABLE IF NOT EXISTS process (
  `account_number` bigint,
  `agent_id` string,
  `agent_assigned_process_id` string,
  `is_system` boolean,
  `name` string,
  `cmd_line` string,
  `path` string,
  `agent_provided_timestamp` timestamp 
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://<BUCKET>/process/'
TBLPROPERTIES ('has_encrypted_data'='false');

CREATE EXTERNAL TABLE IF NOT EXISTS network_interface (
  `account_number` bigint,
  `agent_id` string,
  `name` string,
  `mac_address` string,
  `family` string,
  `ip_address` string,
  `gateway` string,
  `net_mask` string,
  `timestamp` timestamp 
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://<BUCKET>/networkInterface/'
TBLPROPERTIES ('has_encrypted_data'='false');

CREATE EXTERNAL TABLE IF NOT EXISTS os_info (
  `account_number` bigint,
  `agent_id` string,
  `os_name` string,
  `os_version` string,
  `cpu_type` string,
  `host_name` string,
  `hypervisor` string,
  `timestamp` timestamp 
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://<BUCKET>/osInfo/'
TBLPROPERTIES ('has_encrypted_data'='false');

CREATE EXTERNAL TABLE IF NOT EXISTS system_performance (
  `account_number` bigint,
  `agent_id` string,
  `total_disk_bytes_read_per_sec_in_kbps` bigint,
  `total_disk_bytes_written_per_sec_in_kbps` bigint,
  `total_disk_read_ops_per_sec_in_kbps` bigint,
  `total_disk_write_ops_per_sec_in_kbps` bigint,
  `total_network_bytes_read_per_sec_in_kbps` bigint,
  `total_network_bytes_written_per_sec_in_kbps` bigint,
  `total_num_cores` int,
  `total_num_cpus` int,
  `total_num_disks` int,
  `total_num_network_cards` int,
  `total_cpu_usage_pct` int,
  `total_disk_size_in_gb` bigint,
  `total_disk_free_size_in_gb` bigint,
  `total_ram_in_mb` bigint,
  `total_free_ram_in_mb` bigint,
  `timestamp` timestamp 
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://<BUCKET>/systemPerformance/'
TBLPROPERTIES ('has_encrypted_data'='false');

CREATE EXTERNAL TABLE IF NOT EXISTS destination_process_connection (
  `account_number` bigint,
  `agent_id` string,
  `source_ip` string,
  `source_port` int,
  `destination_ip` string,
  `destination_port` int,
  `ip_version` string,
  `transport_protocol` string,
  `agent_assigned_process_id` string,
  `agent_creation_date` timestamp
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://<BUCKET>/destinationProcessConnection/'
TBLPROPERTIES ('has_encrypted_data'='false');

CREATE EXTERNAL TABLE IF NOT EXISTS source_process_connection (
  `account_number` bigint,
  `agent_id` string,
  `source_ip` string,
  `source_port` int,
  `destination_ip` string,
  `destination_port` int,
  `ip_version` string,
  `transport_protocol` string,
  `agent_assigned_process_id` string,
  `agent_creation_date` timestamp
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe'
WITH SERDEPROPERTIES (
  'serialization.format' = '1'
) LOCATION 's3://<BUCKET>/sourceProcessConnection/'
TBLPROPERTIES ('has_encrypted_data'='false');
