CREATE
        OR REPLACE VIEW valid_outbound_ips_helper AS
SELECT DISTINCT "source_ip"
FROM outbound_connection_agent;