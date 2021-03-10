SELECT DISTINCT "hin1"."host_name" "Source Host Name" ,
         "hin2"."host_name" "Destination Host Name" ,
         "o"."source_ip" "Source IP Address" ,
         "o"."destination_ip" "Destination IP Address" ,
         "o"."frequency" "Connection Frequency" ,
         "o"."destination_port" "Destination Communication Port" ,
         "p"."name" "Process Name" ,
         "ianap"."servicename" "Process Service Name" ,
         "ianap"."description" "Process Service Description"
FROM outbound_query_helper o , hostname_ip_helper hin1 , hostname_ip_helper hin2 , processes_agent p , iana_service_ports_import ianap
WHERE ((((("o"."source_ip" = "hin1"."ip_address")
        AND ("o"."destination_ip" = "hin2"."ip_address"))
        AND ("p"."agent_assigned_process_id" = "o"."agent_assigned_process_id"))
        AND ("hin1"."host_name" <> "hin2"."host_name"))
        AND (("o"."destination_port" = TRY_CAST("ianap"."portnumber" AS integer))
        AND ("ianap"."transportprotocol" = 'tcp')))
ORDER BY  "hin1"."host_name" ASC, "o"."frequency" DESC; 