#!/usr/bin/env python
# coding:utf-8

import socket
import struct
import sys
from collections import namedtuple

natTypes = ("Full Cone NAT", "Restrict NAT", "Restrict Port NAT")

def main():
    #Port to open
    port = int(sys.argv[1])

    #Create new socket using address family and socket type and bind it to the port the server is listening
    sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockfd.bind(("", port))
    print "Listening on port " + str(port)


    #Keep track of Peers connection requests
    groupQueue = {}
    peerInfo = namedtuple("PeerInfo", "addr, nat_type_id")
    while True:
        data, addr = sockfd.recvfrom(1024)
        # help build connection between Peers, act as STUN server
        # nat_type_id refers to the index in the array
        print "connection from %s:%d" % addr
        group, nat_type_id = data.strip().split()

        #Inform Peer about connection informations
        sockfd.sendto("SUCCESS " + str(group), addr)
        print("group={0}, nat_type={1}".format(group, natTypes[int(nat_type_id)]))

        # Check if the connection was successful
        data, addr = sockfd.recvfrom(7)
        if data != "SUCCESS":
            continue

        print "request received for group:", group

        #Send address of peer A to B and vice versa
        try:
            a = groupQueue[group].addr
            b =  addr
            nat_type_id_a, nat_type_id_b = groupQueue[group].nat_type_id, nat_type_id
            sockfd.sendto(convertAddressToString(b), a)
            sockfd.sendto(convertAddressToString(a), b)
            
            
            print "Connection complete", group

            #Remove the group from the group queue
            del groupQueue[group]
        except KeyError:
            groupQueue[group] = peerInfo(addr, nat_type_id)



#Convert address to string
def convertAddressToString(addr):
    host, port = addr
    s = str(host) + "+" + str(port)
    return s


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Command should look like this: server.py port")
        exit(0)
    elif not sys.argv[1].isdigit():
        print("port should be a number!")
        exit(0)
    main()
