#!/usr/bin/env python3
import socket
import os
import mimetypes


def parse(request):
    # parse HTTP request but does not convert bytes to string
    lines = request.split(b'\r\n')

    # Start line is the first line of the request message
    start_line = lines[0]

    lines[0] = start_line.split(b' ')  # split start line into seperate words
    # lines[0] == [ b'method', b'URI', b'HTTP/1.1' ]

    method = lines[0][0].decode()  # call decode to convert bytes to string

    return lines, method


def handle_request(request):
    request, method = parse(request)
    # The request is parsed
    print('Server recv (parsed): ', repr(request[0]))
    if method == 'GET':
        return handle_GET(request)

    if method == 'POST':
        return handle_POST(request)

    # If cannot process the request
    response = b'HTTP/1.1 400 Bad Request\r\nServer: localhost\r\nContent-Length: 0\r\n\r\n'
    print(response.decode())
    return response


def handle_GET(request):
    URI = request[0][1].decode()
    path = URI.strip('/')  # remove the first slash from URI

    if not path:
        # If path is empty, that means user is at the homepage so just serve index.html
        path = 'index.html'

    if os.path.isfile(path):  # check if file exists
        status_line = b'HTTP/1.1 200 OK\r\n'
        headers = b'Server: localhost\r\n'

        # find out a file's MIME type
        # if nothing is found, just send 'text/html'
        content_type = mimetypes.guess_type(path)[0] or 'text/html'
        if content_type.split('/')[0] == 'text':
            content_type += '; charset=UTF-8'
            # html, css, text
            # Open file as binary so we dont have to convert string to bytes
            with open(path, 'rb') as file:
                body = file.read()
            headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
            headers += b'Content-Type: ' + content_type.encode() + b'\r\n'
        # If file's type is PDF (download files)
        elif content_type == 'application/pdf':
            headers += b'Content-Type: application/octet-stream\r\n'
            headers += b'Transfer-Encoding: chunked\r\n'

            body = handle_chunked_body(path)
        else:
            # image, others
            # Open file as binary
            with open(path, 'rb') as file:
                body = file.read()
            headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
            headers += b'Content-Type: ' + content_type.encode() + b'\r\n'
    else:
        # no file on the server
        return handle_404()

    blank_line = b'\r\n'
    response = status_line + headers + blank_line + body

    print(status_line.decode() + headers.decode())
    return response


def handle_chunked_body(path):
    # create chunked response/chunked data

    file = open(path, 'rb')  # Open file as binary

    chunk_body = b''
    chunk_size = 1024 * 64
    chunk = file.read(chunk_size)

    while chunk:
        chunk_size = len(chunk)
        # The chunk size is transferred as a hexadecimal number
        chunk_size_hex = hex(chunk_size)[2:].encode()
        # followed by \r\n as a line separator, followed by a chunk of data of the given size
        chunk_body += chunk_size_hex + b'\r\n' + chunk + b'\r\n'
        chunk = file.read(chunk_size)
    file.close()

    # End of chunk
    chunk_body += b'0\r\n\r\n'
    return chunk_body


def handle_POST(request):
    if b'inputAccount=admin&inputPassword=admin' in request:
        print('Logged in')
        # using status code 303 See Other to redirect a POST request is recommended
        # The server sent this response to direct the client to get the requested resource at another URI with a GET request.
        # This response code is usually sent back as a result of PUT or POST. The method used to display this redirected page is always GET.
        # https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections
        # https://tools.ietf.org/html/rfc7231#section-6.4.4
        status_line = b'HTTP/1.1 303 See Other\r\n'

        headers = b'Location: /info.html\r\n'
        headers += b'Content-Length: 0\r\n'

        blank_line = b'\r\n'
        print(status_line.decode() + headers.decode())
        response = status_line + headers + blank_line
    else:
        print('fail auth')
        response = handle_404()
    return response


def handle_404():
    # Open file as binary so we dont have to convert string to bytes
    with open('404.html', 'rb') as file:
        body = file.read()

    status_line = b'HTTP/1.1 404 Not Found\r\n'

    headers = b'Server: localhost\r\n'
    headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
    headers += b'Content-Type: text/html\r\n'

    blank_line = b'\r\n'
    response = status_line + headers + blank_line + body

    print(status_line.decode() + headers.decode())
    return response


if __name__ == '__main__':
    # The server's hostname or IP address. Standard loopback interface address (localhost)
    HOST = '127.0.0.1'

    # The port used by the server, to listen on (non-privileged ports are > 1023)
    PORT = 8888

    # Note that a server must perform the sequence socket(), bind(), listen(), accept() (possibly repeating the accept()),

    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind the socket to an address and a port
    server.bind((HOST, PORT))

    # Enable server to accept connections.
    server.listen(5)
    print('Listening at', server.getsockname(), '\n')
    # Now waiting for clients to connect
    try:
        while True:
            # accept connection from client (web browser)
            conn, address = server.accept()
            print('Connected by ', address)
            # receive HTTP request from client (web browser)
            request = conn.recv(1024)

            # Also note that the server does not sendall()/recv() on the socket it is listening on but on the new socket returned by accept().

            # process the request then reply with appropriate response
            response = handle_request(request)
            # sending data (HTTP response) to client (web browser)
            conn.sendall(response)
            # closing connection
            conn.close()
    except KeyboardInterrupt:
        # press Ctrl + C then reload the web to trigger exception
        print('Keyboard Interrupted')
        conn.close()
    finally:
        print('Closing server')
        server.close()
