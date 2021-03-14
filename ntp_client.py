import socket
import struct
from collections import defaultdict
import client_config
import datetime
import time

NTP_DELTA = (datetime.date(*time.gmtime(0)[0:3]) - datetime.date(1900, 1, 1)).days * 24 * 60 * 60


def _to_time(integ, frac, n=32):
    return integ + float(frac) / 2 ** n


def system_to_ntp_time(timestamp):
    return timestamp + NTP_DELTA


def print_time(t):
    print(t, "{0:.16f}".format(t))


def is_duplicate(obj, org_timestamp, rcv_timestamp, xmt_timestamp):
    if obj.org_timestamp in org_timestamp:
        if obj.rcv_timestamp in rcv_timestamp:
            if obj.xmt_timestamp in xmt_timestamp:
                print("duplicate message")
                return True
    return False


class NTPPacket:
    _PACKET_FORMAT = "!B B b b 3I 4d"

    def __init__(self, mode=3, xmt_timestamp=0):
        self.li = 0

        self.version = 4

        self.mode = mode

        self.stratum = 0

        self.poll = 0

        self.precision = 0

        self.root_delay = 0

        self.root_dispersion = 0

        self.reference_id = 0

        self.reference_timestamp = 0

        self.org_timestamp = 0

        self.rcv_timestamp = 0

        self.xmt_timestamp = xmt_timestamp


    def convert_to_bytes(self):

        byte_string = struct.pack(NTPPacket._PACKET_FORMAT,
                             (self.li << 6 | self.version << 3 | self.mode),
                             self.stratum,
                             self.poll,
                             self.precision,
                             self.root_delay,
                             self.root_dispersion,
                             self.reference_id,
                             self.reference_timestamp,
                             self.org_timestamp,
                             self.rcv_timestamp,
                             self.xmt_timestamp)
        return byte_string

    def convert_to_obj(self, data):
        unpacked = struct.unpack(NTPPacket._PACKET_FORMAT,
                                 data[0:struct.calcsize(NTPPacket._PACKET_FORMAT)])
        # except struct.error:
        #     raise NTPException("Invalid NTP packet.")
        # 111.110

        self.li = unpacked[0] >> 6 & 0x3
        self.version = unpacked[0] >> 3 & 0x7
        self.mode = unpacked[0] & 0x7
        self.stratum = unpacked[1]
        self.poll = unpacked[2]
        self.precision = unpacked[3]
        self.root_delay = unpacked[4]
        self.root_dispersion = unpacked[5]
        self.reference_id = unpacked[6]
        self.reference_timestamp = unpacked[7]
        self.org_timestamp = unpacked[8]
        self.rcv_timestamp = unpacked[9]
        self.xmt_timestamp = unpacked[10]


def received_message(sock):
    data, addr = sock.recvfrom(1024)
    current_rcv_timestamp = system_to_ntp_time(time.time())
    packet = NTPPacket()
    packet.convert_to_obj(data)
    return packet, current_rcv_timestamp


def plot_measurements(oi_di: dict):
    xvalues = []
    yvalues = []
    for key in oi_di:
        for ind in range(len(oi_di[key])):
            xvalues.append(str(key + 1) + '.' + str(ind + 1))
            yvalues.append(oi_di[key][ind])
    print(xvalues)
    print(yvalues)
    markers_on = []
    for key in oi_di:
        min_delay = float('inf')
        final_index = None
        for ind in range(len(oi_di[key])):
            yval = oi_di[key][ind]
            if yval[1] < min_delay:
                min_delay = yval[1]
                final_index = ind
        markers_on.append(key * 8 + final_index)
    print(markers_on)

    import matplotlib.pyplot as plt
    plt.plot(xvalues, yvalues, '-D', markevery=markers_on)
    plt.xlabel('burst_messages')
    plt.ylabel('offest_delay')
    plt.show()


def main():

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    burst_size = client_config.NTP_client_config.burst_size
    burst_counter = client_config.NTP_client_config.burst_counter
    burst_offset_delay_list = defaultdict(list)

    for counter in range(burst_counter):
        # loop :- pack
        org_timestamp = [0]
        rcv_timestamp = [0]
        xmt_timestamp = []
        message_pair = 0
        oi_di_list = []
        while message_pair < burst_size:
            packet = NTPPacket()
            packet.org_timestamp = org_timestamp[message_pair]
            packet.rcv_timestamp = rcv_timestamp[message_pair]
            packet.xmt_timestamp = system_to_ntp_time(time.time())
            message = packet.convert_to_bytes()
            sock.sendto(message, (client_config.conn_config.host, client_config.conn_config.port))

            duplicate = False
            end_time = time.time() + 1
            while time.time() < end_time:
                obj, current_rcv_timestamp = received_message(sock)
                duplicate = is_duplicate(obj, org_timestamp, rcv_timestamp, xmt_timestamp)
                if not duplicate:
                    break

            if duplicate:
                continue
            di = (current_rcv_timestamp - obj.org_timestamp) - (obj.xmt_timestamp - obj.rcv_timestamp)
            oi = ((obj.rcv_timestamp - obj.org_timestamp) + (obj.xmt_timestamp - current_rcv_timestamp)) / 2

            oi_di_list.append((oi * 1000, di * 1000))

            # print("bust message pair :- ", message_pair + 1)

            # print_time(obj.org_timestamp)
            # print_time(obj.rcv_timestamp)
            # print_time(obj.xmt_timestamp)
            print(datetime.datetime.fromtimestamp(obj.xmt_timestamp))
            # print_time(current_rcv_timestamp)

            # print("delay is :- ", di * 1000)
            # print("offset is :- ", oi * 1000)
            print("-------------------------------------------------")
            org_timestamp.append(obj.xmt_timestamp)
            rcv_timestamp.append(current_rcv_timestamp)
            xmt_timestamp.append(packet.xmt_timestamp)
            message_pair += 1
        burst_offset_delay_list[counter] = oi_di_list

        # print(org_timestamp, len(org_timestamp))
        # print(rcv_timestamp, len(rcv_timestamp))
        # print(xmt_timestamp, len(xmt_timestamp))
        time.sleep(client_config.NTP_client_config.burst_time_interval)
    print(burst_offset_delay_list)
    plot_measurements(burst_offset_delay_list)


if __name__ == '__main__':
    main()
