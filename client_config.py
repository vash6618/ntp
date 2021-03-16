class conn_config:
    # for local ntp server
    # host = '127.0.0.1'
    # port = 5005


    # for public ntp server
    host = '0.pool.ntp.org'
    port = 123

    # for cloud ntp server
    # host = '34.106.133.20'
    # port = 5005


class NTP_client_config:
    burst_size = 8
    burst_counter = 16