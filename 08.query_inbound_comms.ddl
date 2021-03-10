SELECT DISTINCT "hin1"."host_name" "Source Host Name" ,
         "hin2"."host_name" "Destination Host Name" ,
         "i"."source_ip" "Source IP Address" ,
         "i"."destination_ip" "Destination IP Address" ,
         "i"."frequency" "Connection Frequency" ,
         "i"."destination_port" "Destination Communication Port" ,
         "p"."name" "Process Name" ,
         "ianap"."servicename" "Process Service Name" ,
         "ianap"."description" "Process Service Description"
FROM inbound_query_helper i , hostname_ip_helper hin1 , hostname_ip_helper hin2 , processes_agent p , iana_service_ports_import ianap
WHERE ((((("i"."source_ip" = "hin1"."ip_address")
        AND ("i"."destination_ip" = "hin2"."ip_address"))
        AND ("p"."agent_assigned_process_id" = "i"."agent_assigned_process_id"))
        AND ("hin1"."host_name" <> "hin2"."host_name"))
        AND (("i"."destination_port" = TRY_CAST("ianap"."portnumber" AS integer))
        AND ("ianap"."transportprotocol" = 'tcp')))
ORDER BY  "hin1"."host_name" ASC, "i"."frequency" DESC;