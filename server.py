import socket
import os
import mimetypes

# parse HTTP request but does not convert bytes to string
def parse(request):
    lines = request.split(b'\r\n')

    start_line = lines[0] # Start line is the first line of the request message

    words = start_line.split(b' ') # split start line into seperate words
    # [ b'method', b'URI', b'HTTP/1.1 ]
    lines[0] = words

    method = words[0].decode() # call decode to convert bytes to string

    return lines, method

def handle_request(conn, request):
    request, method = parse(request)
    print("Server recv: ", request[0])
    if method == 'GET':
        return handle_GET(conn, request)
        
    if method == 'POST':
        return handle_POST(request)
        # If cannot process the request
    return b'HTTP/1.1 400 Bad Request\r\n'

def handle_GET(conn, request):
    path = request[0][1].decode().strip('/') # remove slash from URI
    
    if not path:
        # If path is empty, that means user is at the homepage so just serve index.html
        path = 'index.html'

    if os.path.exists(path) and not os.path.isdir(path): # don't serve directories
        status_line = b'HTTP/1.1 200 OK\r\n'
        headers = b'Server : localhost\r\nConnection: keep-alive\r\n'
        
        # find out a file's MIME type
        # if nothing is found, just send `text/html`
        content_type = mimetypes.guess_type(path)[0] or 'text/html'
        if content_type.split('/')[0] == 'text':
            content_type +=  '; charset=UTF-8'
            # html, css, text
            # Open file as binary so we dont need to convert to bytes
            with open(path, 'r') as file:
                body = file.read().encode()
            headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
            headers += b'Content-Type: ' + content_type.encode() + b'\r\n'
        # If file's type is PDF (download files) 
        elif content_type == 'application/pdf':
            #headers += b'Content-Type: ' + content_type.encode() + b'\r\n'
            headers += b'Content-Type: application/octet-stream\r\n'
            headers += b'Transfer-Encoding: chunked\r\n'

            body = handle_chunked_response(path)           
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
    
    print(status_line.decode() + headers.decode())
    
    blank_line = b'\r\n'
    response = status_line + headers + blank_line + body
    
    return response

# create chunked response/ chunked data
def handle_chunked_response(path):
    # Open file as binary
    file = open(path, 'rb')
    
    chunk_body = b''
    chunk_size = 1024 * 128
    chunk = file.read(chunk_size)
    
    while chunk:
        chunk_size = len(chunk)
        chunk_size_hex = hex(chunk_size)[2:].encode()
        chunk_body += chunk_size_hex + b'\r\n' + chunk + b'\r\n'
        chunk = file.read(chunk_size)
    # End of chunk
    chunk_body += b'0\r\n\r\n'
    file.close()
    return chunk_body

def handle_POST(request):
    if b'Content-Type: application/x-www-form-urlencoded' in request:
        if b'inputAccount=admin&inputPassword=admin' in request: 
            print('Logged in')
            # using status code 303 See Other to redirect a POST request is recommended
            # The server sent this response to direct the client to get the requested resource at another URI with a GET request.
            # This response code is usually sent back as a result of PUT or POST. The method used to display this redirected page is always GET.
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Redirections
            # https://tools.ietf.org/html/rfc7231#section-6.4.4
            status_line = b'HTTP/1.1 303 See Other\r\n'
            headers = b'Location: /info.html\r\n'
            blank_line = b'\r\n'
            response = status_line + headers + blank_line
        else:
            print('fail auth')
            response = handle_404()
    else:
        print('fail content type')
        response = handle_404()
    return response

def handle_404():
    # Open file as text
    with open('404.html', 'r') as file:
        body = file.read().encode()
        
    status_line = b'HTTP/1.1 404 Not Found\r\n'
    
    headers = b'Server : localhost\r\n'
    headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
    headers += b'Content-Type: text/html\r\n'
    
    blank_line = b'\r\n'
    
    response = status_line + headers + blank_line + body
    
    return response

if __name__ == '__main__':
    # The server's hostname or IP address. Standard loopback interface address (localhost)
    HOST = "127.0.0.1" 
    
    # The port used by the server, to listen on (non-privileged ports are > 1023)
    PORT = 8888 
    
    '''
    Note that a server must perform the sequence socket(), bind(), listen(), accept() (possibly repeating the accept()),
    Also note that the server does not sendall()/recv() on the socket it is listening on but on the new socket returned by accept().
    '''
    
    # Create a TCP/IP socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set socket keep alive
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind the socket to an address and a port
    server.bind((HOST, PORT))

    # Enable server to accept connections. 
    server.listen()
    # Now waiting for clients to connect
    try:
        while True:
            # accept a connection
            conn, address = server.accept()
            print("\nConnected by ", address)
            request = conn.recv(1024)
            
            response = handle_request(conn, request)
            # sending data (HTTP response) to client (web browser)
            conn.sendall(response)

            # closing connection
            conn.close()
    except KeyboardInterrupt:
        print("Keyboard Interrupted")
    finally:
        print("Closing server")
        server.close()