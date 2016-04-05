#!/usr/bin/env python

import struct
import socket
import sys
from threading import Thread, Event, Timer


# define only three types of nat (does not support symmetric)
natTypes = ("Full Cone NAT", "Restrict NAT", "Restrict Port NAT")

"""Convert a string to ip adress with port."""
def stringToAddress(peerInfoString):
    host, port = peerInfoString.strip().split("+")
    target = (host, int(port))
    return target
    
  
"""Peer class"""
class Peer():

    
    def main(self, test_nat_type):
        nat_type = test_nat_type
        print("bro")

        try:
            self.requestForConnection(natTypes.index(nat_type))
        except ValueError:
            print("NAT type unsupported.")
            sys.exit(0)
        # If full cone nat
        if nat_type == natTypes[0]:
            print("FullCone chat mode")
            self.fullconeChat()
        # else restricted
        elif nat_type in (natTypes[1], natTypes[2]):
            print("Restrict chat mode")
            self.restrictChat()
        else:
            print("NAT type wrong!")
    
    #initialize the peer class
    def __init__(self):
        try:
            # (server IP, listening port)
            self.master = (sys.argv[1], int(sys.argv[2]))
            self.group = sys.argv[3].strip()
            self.sockfd = self.target = None
            self.periodic_running = False
            #self.peer_nat_type = None
            
        except (IndexError, ValueError):
            print (sys.stderr, "usage: %s <host> <port> <group>" % sys.argv[0])
            sys.exit(65)

            
    def requestForConnection(self, nat_type_id):
        #Create new socket using address family and socket type and bind it to the port the server is listening
        self.sockfd = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sockfd.sendto(self.group + ' {0}'.format(nat_type_id), self.master)
        
        #Retrieve group info from data and sender address
        data, addr = self.sockfd.recvfrom(len(self.group) + 8)
        if data != "SUCCESS " + self.group:
            print sys.stderr, "unable to request!"
            sys.exit(1)
        
        #Acknowledge request for connection
        self.sockfd.sendto("SUCCESS", self.master)
        sys.stderr = sys.stdout
        print sys.stderr, "request sent, waiting for partner in group '%s'..." % self.group
        
        #Get peer info from data and sender address
        data, addr = self.sockfd.recvfrom(1024)

        #get target info
        self.target = stringToAddress(data)
        print "connected to: " + str(self.target)

    def receiveMessage(self, sock, is_restrict = False, event = None):
        if is_restrict:
            while True:
                data, addr = sock.recvfrom(1024)
                if self.periodic_running:
                    print "periodic_send is alive"
                    self.periodic_running = False
                    event.set()
                    print "received msg from target, periodic send cancelled, chat start."
                if addr == self.target or addr == self.master:
                    sys.stdout.write(data)
                    if data == "punching...\n":
                        sock.sendto("end punching\n", addr)
        else:
            while True:
                data, addr = sock.recvfrom(1024)
                if addr == self.target or addr == self.master:
                    sys.stdout.write(data )
                    if data == "punching...\n": 
                        sock.sendto("end punching", addr)
    
    def sendMessage(self, sock):
        while True:
            data = "My Peer: " + sys.stdin.readline()
            sock.sendto(data, self.target)
            
    def restrictChat(self):
        #Send udp punch through packages
        stopEvent = Event()
        def send(count):
            self.sockfd.sendto('punching...\n', self.target)
            print("UDP punch-through {0}".format(count))
            
            # Send udp packages periodically
            if self.periodic_running:
                Timer(0.5, send, args=(count + 1,)).start()

        self.periodic_running = True
        send(0)
        arguments = {'is_restrict': True, 'event': stopEvent}
        Thread(target=self.receiveMessage, args=(self.sockfd,), kwargs=arguments).start()
        stopEvent.wait()
        Thread(target=self.sendMessage, args=(self.sockfd,)).start()

        
    def fullconeChat(self):
        # A thread for sending messages and one for receiving so we can achieve parrallel action
        Thread(target=self.sendMessage, args=(self.sockfd,)).start()
        Thread(target=self.receiveMessage, args=(self.sockfd,)).start()

#Initialize client
if __name__ == "__main__": 
    peer = Peer()
    try:
        test_nat_type = natTypes[int(sys.argv[4])]
    except IndexError:
        print "NAT type not specified."
        sys.exit(0)
    peer.main(test_nat_type)
