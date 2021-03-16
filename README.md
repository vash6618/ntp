# Programming Assignment 3 :- NTP
## People involved in the assignment :- 
### Vasu Sharma and Manan Khasgiwale


#### How to run the system
1) The system contains a server and a client file. The client file 
incorporates the logic for calculating offset and delays, burst messages 
   and positive acknowledgement.
2) There is a client config present in the source code
    1) To evaluate values with the local ntp server, uncomment the host and port for the local ntp server
    2) To evaluate values with the cloud ntp server, uncomment the host and port for the cloud ntp server 
    3) To evaluate values with the public ntp server, uncomment the host and port for the public ntp server
3) After uncommenting the client config, if you want to first run with the local ntp server run the ntp_server.py
file and then run the ntp_client.py file. For other scenarios just run the ntp_client.py file
4) To run the respective server or client files just use this command :- python3 filename



#### Measurements file
1) All measurements are stored in xlsx format in separate files for local, cloud and public 
ntp servers.
2) Each measurement contains burst counter, burst message pair, T1, T2, T3, T4, offset (ms), delay (ms).
3) After each burst there is a line which contains the minimum delay and the offset related to that minimum
delay.
   

#### Graphs 
1) All graphs are stored in png format in separate files for local, cloud and public ntp servers.
2) Each graph has circled the point with minimum delay and its corresponding offset for each burst.
3) Since the circled point is very small and has large decimal values, it's value is not shown in the graph. 
Instead its value is present in the measurements file.

