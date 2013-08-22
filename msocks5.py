#!/usr/bin/python

# @2013.08.22 by felix021
# This file is modified fron github/felix021/mixo
# to act as a pure socks5 proxy.
#
# usage:
#    python msocks5.py          #listens on 7070
#    python msocks5.py 1080     #listens on 1080

import sys 
import struct
import signal

try:
    import gevent
    from gevent import socket
    from gevent.server import StreamServer
    from gevent.socket import create_connection, gethostbyname
except:
    print >>sys.stderr, "please install gevent first!"
    sys.exit(1)

class XSocket(gevent.socket.socket):
    def __init__(self, socket = None, addr = None):
        if socket is not None:
            gevent.socket.socket.__init__(self, _sock = socket)
        elif addr is not None:
            gevent.socket.socket.__init__(self)
            self.connect(addr)
        else:
            raise Exception("XSocket.init: bad arguments")

    def unpack(self, fmt, length):
        data = self.recv(length)
        if len(data) < length:
            raise Exception("XSocket.unpack: bad formatted stream")
        return struct.unpack(fmt, data)

    def pack(self, fmt, *args):
        data = struct.pack(fmt, *args)
        return self.sendall(data)

    def recv(self, length, *args):
        return super(XSocket, self).recv(length, *args)

    def sendall(self, data, flags = 0):
        return super(XSocket, self).sendall(data, flags)

    def forward(self, dest):
        try:
            while True:
                data = self.recv(1024)
                if not data:
                    break
                dest.sendall(data)
        #except IOError, e: pass
        finally:
            print 'connection closed'
            self.close()
            dest.close()


class SocksServer(StreamServer):
    def __init__(self, listener, **kwargs):
        StreamServer.__init__(self, listener, **kwargs)

    def handle(self, sock, addr):
        print 'connection from %s:%s' % addr

        src = XSocket(socket = sock)

        #socks5 negotiation step1: choose an authentication method
        ver, n_method = src.unpack('BB', 2) 

        if ver != 0x05:
            src.pack('BB', 0x05, 0xff)
            return

        if n_method > 0:
            src.recv(n_method)
        
        src.pack('!BB', 0x05, 0x00) #0x00 means no authentication needed

        #socks5 negotiation step2: specify command and destination
        ver, cmd, rsv, atype = src.unpack('BBBB', 4)

        if cmd != 0x01:
            src.pack('BBBBIH', 0x05, 0x07, 0x00, 0x01, 0, 0)
            return

        if atype == 0x01: #ipv4
            host, port = src.unpack('!IH', 6)
            hostip = socket.inet_ntoa(struct.pack('!I', host))
        elif atype == 0x03: #domain name
            length = src.unpack('B', 1)[0]
            hostname, port = src.unpack("!%dsH" % length, length + 2)
            hostip = gethostbyname(hostname)
            host = struct.unpack("!I", socket.inet_aton(hostip))[0]
        elif atype == 0x04: #ipv6: TODO
            src.pack('!BBBBIH', 0x05, 0x07, 0x00, 0x01, 0, 0)
            return
        else:
            src.pack('!BBBBIH', 0x05, 0x07, 0x00, 0x01, 0, 0)
            return

        print 'after step2'

        try:
            dest = XSocket(addr = (hostip, port))
        except IOError, ex:
            print "%s:%d" % addr, "failed to connect to %s:%d" % (hostip, port)
            src.pack('!BBBBIH', 0x05, 0x03, 0x00, 0x01, host, port)
            return

        src.pack('!BBBBIH', 0x05, 0x00, 0x00, 0x01, host, port)

        gevent.spawn(src.forward, dest)
        gevent.spawn(dest.forward, src)

    def close(self):
        sys.exit(0)

    @staticmethod
    def start_server():
        global port
        server = SocksServer(('0.0.0.0', port))
        gevent.signal(signal.SIGTERM, server.close)
        gevent.signal(signal.SIGINT, server.close)
        print "Server is listening on 0.0.0.0:%d" % port
        server.serve_forever()

if __name__ == '__main__':
    import sys
    global port
    port = 7070
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    SocksServer.start_server()
