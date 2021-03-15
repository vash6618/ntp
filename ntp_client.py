import socket
import struct
from collections import defaultdict
import client_config
import datetime
import time
import csv

NTP_DELTA = (datetime.date(*time.gmtime(0)[0:3]) - datetime.date(1900, 1, 1)).days * 24 * 60 * 60


def convert_to_ntp_time(timestamp):
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


def save_observations_to_file(dw, burst_counter, message_pair, t1, t2, t3, t4, oi, di):
    dw.writerow({"burst_counter": burst_counter, "message_pair": message_pair,
                 "T1": t1, "T2": t2, "T3": t3, "T4": t4, "offset": oi, "delay": di})


class NTPPacket:
    _PACKET_FORMAT = "!B B b b 11I"

    def __init__(self, mode=3):
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

        self.xmt_timestamp = 0

    def convert_to_bytes(self):

        byte_string = struct.pack(NTPPacket._PACKET_FORMAT,
                                  (self.li << 6 | self.version << 3 | self.mode),
                                  self.stratum,
                                  self.poll,
                                  self.precision,
                                  self.root_delay,
                                  self.root_dispersion,
                                  self.reference_id,
                                  int(self.reference_timestamp),
                                  int((self.reference_timestamp - int(self.reference_timestamp)) * pow(2, 32)),
                                  int(self.org_timestamp),
                                  int((self.org_timestamp - int(self.org_timestamp)) * pow(2, 32)),
                                  int(self.rcv_timestamp),
                                  int((self.rcv_timestamp - int(self.rcv_timestamp)) * pow(2, 32)),
                                  int(self.xmt_timestamp),
                                  int((self.xmt_timestamp - int(self.xmt_timestamp)) * pow(2, 32)))
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
        self.reference_timestamp = unpacked[7] + float(unpacked[8]) / pow(2, 32)
        self.org_timestamp = unpacked[9] + float(unpacked[10]) / pow(2, 32)
        self.rcv_timestamp = unpacked[11] + float(unpacked[12]) / pow(2, 32)
        self.xmt_timestamp = unpacked[13] + float(unpacked[14]) / pow(2, 32)



def received_message(sock):
    data, addr = sock.recvfrom(1024)
    current_rcv_timestamp = convert_to_ntp_time(time.time())
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

    if client_config.conn_config.port == 123:
        file = '/Users/vasusharma/Downloads/ntp_observations/original_ntp_server_4mins.csv'
        fp = open(file, 'w+')
    elif client_config.conn_config.host == '127.0.0.1':
        file = '/Users/vasusharma/Downloads/ntp_observations/local_ntp_server_4mins.csv'
        fp = open(file, 'w+')
    else:
        file = '/Users/vasusharma/Downloads/ntp_observations/cloud_ntp_server_4mins.csv'
        fp = open(file, 'w+')

    dw = csv.DictWriter(fp, delimiter=',', fieldnames=["burst_counter", "message_pair", "T1", "T2", "T3", "T4",
                                                       "offset", "delay"])
    dw.writeheader()
    for counter in range(burst_counter):
        # loop :- pack
        org_timestamp = [0]
        rcv_timestamp = [0]
        xmt_timestamp = []
        message_pair = 0
        oi_di_list = []
        min_delay = float('inf')
        offset = None

        end_counter_time = time.time() + 60*4
        while message_pair < burst_size:
            packet = NTPPacket()
            packet.org_timestamp = org_timestamp[message_pair]
            packet.rcv_timestamp = rcv_timestamp[message_pair]
            packet.xmt_timestamp = convert_to_ntp_time(time.time())
            message = packet.convert_to_bytes()
            sock.sendto(message, (client_config.conn_config.host, client_config.conn_config.port))
            duplicate = False
            print(message_pair, duplicate)
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

            save_observations_to_file(dw, counter, message_pair,
                                      datetime.datetime.fromtimestamp(obj.org_timestamp - NTP_DELTA),
                                      datetime.datetime.fromtimestamp(obj.rcv_timestamp - NTP_DELTA),
                                      datetime.datetime.fromtimestamp(obj.xmt_timestamp - NTP_DELTA),
                                      datetime.datetime.fromtimestamp(current_rcv_timestamp - NTP_DELTA),
                                      oi * 1000, di * 1000)

            if di < min_delay:
                min_delay = di * 1000
                offset = oi * 1000

            oi_di_list.append((oi * 1000, di * 1000))

            print("burst-counter :- ", counter, " message-pair :- ", message_pair, " ",
                  datetime.datetime.fromtimestamp(obj.xmt_timestamp))
            # print_time(current_rcv_timestamp)

            # print("delay is :- ", di * 1000)
            # print("offset is :- ", oi * 1000)
            print("-------------------------------------------------")
            org_timestamp.append(obj.xmt_timestamp)
            rcv_timestamp.append(current_rcv_timestamp)
            xmt_timestamp.append(packet.xmt_timestamp)
            message_pair += 1
        dw.writerow({"delay": min_delay, "offset": offset})
        burst_offset_delay_list[counter] = oi_di_list

        while time.time() < end_counter_time:
            continue
    print(burst_offset_delay_list)
    plot_measurements(burst_offset_delay_list)


if __name__ == '__main__':
    main()
