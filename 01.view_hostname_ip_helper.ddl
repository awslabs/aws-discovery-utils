CREATE
        OR REPLACE VIEW hostname_ip_helper AS
SELECT DISTINCT "os"."host_name" ,
         "nic"."agent_id" ,
         "nic"."ip_address"
FROM os_info_agent os , network_interface_agent nic
WHERE ("os"."agent_id" = "nic"."agent_id");