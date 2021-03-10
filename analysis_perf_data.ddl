SELECT "OS"."os_name" "OS Name" ,
         "OS"."os_version" "OS Version" ,
         "OS"."host_name" "Host Name" ,
         "SP"."agent_id" ,
         "SP"."total_num_cores" "Number of Cores" ,
         "SP"."total_num_cpus" "Number of CPU" ,
         "SP"."total_cpu_usage_pct" "CPU Percentage" ,
         "SP"."total_disk_size_in_gb" "Total Storage (GB)" ,
         "SP"."total_disk_free_size_in_gb" "Free Storage (GB)" ,
         ("SP"."total_disk_size_in_gb" - "SP"."total_disk_free_size_in_gb") "Used Storage" ,
         "SP"."total_ram_in_mb" "Total RAM (MB)" ,
         ("SP"."total_ram_in_mb" - "SP"."free_ram_in_mb") "Used RAM (MB)" ,
         "SP"."free_ram_in_mb" "Free RAM (MB)" ,
         "SP"."total_disk_read_ops_per_sec" "Disk Read IOPS" ,
         "SP"."total_disk_bytes_written_per_sec_in_kbps" "Disk Write IOPS" ,
         "SP"."total_network_bytes_read_per_sec_in_kbps" "Network Reads (kbps)" ,
         "SP"."total_network_bytes_written_per_sec_in_kbps" "Network Write (kbps)"
FROM "sys_performance_agent" "SP" , "OS_INFO_agent" "OS"
WHERE ("SP"."agent_id" = "OS"."agent_id") limit 10;