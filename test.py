import socket
import os
import mimetypes

HOST = "127.0.0.1"
PORT = 8888

# initializing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s = setsockopt() python keep-alive digi.com

# binding host and port
s.bind((HOST, PORT))

# waiting for client to connect
s.listen(5)

#file = open("Example.html", "r")
file = open("index.html", "r")
response = "HTTP/1.1 200 OK\r\nConnection: keep-alive\r\nServer: socket\r\nContent-Type: text/html\r\n\r\n" + file.read()
msga="""
POST /index.html HTTP/1.1 \r\n
Host: localhost\r\n
Connection: close\r\n
Content-Type: application/x-www-form-urlencoded\r\n
Content-Length: 
"""
#msg=msg+"Content-Length: " + str( len( file.read() ) ) + "\r\n"

#inputAccount=value1&inputPassword=value2
file.close()

print("Waiting for Client")


#handle request
def handle_request(request):
    request, method = parse(request)
    
    if method == 'GET':
        return handle_GET(request)
        
    if method == 'POST':
        return handle_POST(request)
    # 400 Bad request
    return response

def parse(request):
        lines = request.split(b'\r\n')

        start_line = lines[0] # start line is the first line of the request message

        words = start_line.split(b' ') # split start line into seperate words
        
        lines[0] = words

        method = words[0].decode() # call decode to convert bytes to string

        URI = words[1]

        version = words[2]

        if len(words) > 1:
            # we put this in if block because sometimes browsers
            # don't send URI with the request for homepage
            uri = words[1].decode() # call decode to convert bytes to string

        if len(words) > 2:
            # we put this in if block because sometimes browsers
            # don't send HTTP version
            version = words[2]
        
        return lines, method

def handle_GET(request):
    path = request[0][1].decode().strip('/')
    
    if not path:
        # If path is empty, that means user is at the homepage
        # so just serve index.html
        path = 'index.html'

    if os.path.exists(path) and not os.path.isdir(path): # don't serve directories
        with open(path, 'rb') as file:
            body = file.read()
        
        #response_line = self.response_line(200)
        
        
        status_code = b'200'
        status_message = b'OK'
        status_line = b'HTTP/1.1 200 OK\r\n'
        headers = b'Server : localhost\r\nConnection: keep-alive\r\n'
        
        # find out a file's MIME type
        # if nothing is found, just send `text/html`
        content_type = mimetypes.guess_type(path)[0] or 'text/html'
        if content_type.split('/')[0] == 'text':
            content_type +=  '; charset=UTF-8'
        if content_type == 'application/pdf':
            #headers += b'Content-Type: ' + content_type.encode() + b'\r\n'
            #headers += b'Content-Type: application/octet-stream\r\n'
            #headers += b'Content-Type: text/plain\r\n'
            headers += b'Transfer-Encoding: chunked\r\n'
            #headers += b'Trailer: Max-Forwards\r\n'
            #headers += b'Content-Encoding: gzip\r\n'
            
            file_size = len(body)
            data = body
            body = b''
            i = 0
            print('file_size: %d' %file_size)
            MB = 1024 * 1024
            # this while loop taking so long
            while i < file_size:
                chunk = data[i:i+MB]
                i += MB
                chunk_size = len(chunk)
                chunk_size_hex = hex(chunk_size)[2:chunk_size].encode()
                body = body + chunk_size_hex + b'\r\n' + chunk + b'\r\n'
            
            # End of chunk
            body += b'0\r\n\r\n'
            
            # tosend = '%X\r\n%s\r\n'%(len(chunk), chunk)
            
            print('debug')
            #body = data
        else:
            headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
            headers += b'Content-Type: ' + content_type.encode() + b'\r\n'
    else:
        return handle_404()
    
    print(status_line+headers)
    blank_line = b'\r\n'
    
    response = status_line + headers + blank_line + body
    
    return response

def handle_download(request):
    # create chunked response, data chunk
    
    return response
    
def handle_POST(request):
    if b'Content-Type: application/x-www-form-urlencoded' in request:
        if b'inputAccount=admin&inputPassword=admin' in request: 
            print('Logged in')
            # using status code 303 See Other to redirect a POST request is recommended
            # The server sent this response to direct the client to get the requested resource at another URI with a GET request.
            # https://tools.ietf.org/html/rfc7231#section-6.4.4
            status_code = b'303'
            status_message = b' See Other\r\n'
            status_line = b'HTTP/1.1 ' + status_code + status_message
            headers = b'Location: /info.html\r\n'
            response = status_line + headers
        else:
            print('fail auth')
            response = handle_404()
    else:
        print('fail content type')
        response = handle_404()
    return response
    
def handle_404():
    with open('404.html', 'rb') as file:
        body = file.read()
        
    status_line = b'HTTP/1.1 404 Not Found\r\n'
    
    headers = b'Server : localhost\r\n'
    headers += b'Content-Length: ' + str(len(body)).encode() + b'\r\n'
    headers += b'Content-Type: text/html\r\n'
    
    blank_line = b'\r\n'
    
    response = status_line + headers + blank_line + body
    
    return response

if __name__ == '__main__':
    try:
        while True:
            conn, address = s.accept()
            print("Connected by ", address)
            request = conn.recv(1024)
            if len(request) == 0:
                print('No request sent')
                break
            print("Server recv:\n" + request.decode())
            response = handle_request(request)
            # sending data
            conn.sendall(response)

            # closing
            conn.close()
    except KeyboardInterrupt:
        print("Closing server\n")
        conn.close()
        s.close()

