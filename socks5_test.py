#encoding: utf-8
#SOCKS Protocol Version 5: http://www.openssh.com/txt/rfc1928.txt

#this file is used as single-time client or server.

import socket

#---- socks5 client ----#
def client():
    HOST = '127.0.0.1'
    PORT = 7070
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    #ver=5, n_method=1, methods=[0]
    s.sendall("\x05\x01\x00")
    print repr(s.recv(1024))

    #ver=5, cmd=1(connect), reserved=0 + atype=1(ip), host=127.0.0.1 + port=80 ;;p.s. ATYPE(03=host,04=ipv6)
    s.sendall("\x05\x01\x00" + "\x01\x7f\x00\x00\x01" + "\x00\x50")
    print repr(s.recv(1024))

    #http request
    s.sendall("GET / HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
    print s.recv(4096)

#---- socks5 server ----#
def server():
    HOST = '0.0.0.0'
    PORT = 7070
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1024)
    t, a = s.accept()
    print repr(t.recv(1024))

    #ver=5, method=0(no authentication)
    t.send("\x05\x00")
    print repr(t.recv(1024))

    #ver=5, Reply=0(succeeded), reserved=0, atype=1(ip), host=127.0.0.1 + port=80
    t.send("\x05\x00\x00" + "\x01\x7f\x00\x00\x01" + "\x00\x50")

    #http-request from client
    x = t.recv(4096)
    print x 

    #http-response
    t.send("HTTP/1.1 200 OK\r\nContent-Length: 6\r\n\r\nhello!")

client()
#server()
