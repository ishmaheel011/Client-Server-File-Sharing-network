from socket import *
from hashlib import *
import os

# protocol: hashcode<>cmd<>request<>body

def main():
    
    def hashcode(data):
        m=sha256()
        m.update(data)
        return bytes(m.hexdigest(),'utf8')   

    SEPARATOR = b'<SEPARATOR>' # used for splitting with bytes
    SEPARATOR2 = "<SEPARATOR>" # used for protocol implementation
    HEADER = b'<HEADER>' #for receiving
    HEADER2 = "<HEADER>" #for sending
    DIVIDER = "<DIVIDER>"
    GUI_LINE = "+-----------------------+---------------+"
    GUI_TITLE = "| File Name\t\t| File Type\t|"
    
    #create folder
    oldpath = os.getcwd()
    newpath = os.path.join(oldpath, r'downloads')
    if not os.path.exists(newpath):
        os.makedirs(newpath)
    
    #create socket
    client = socket(AF_INET, SOCK_STREAM)
    
    #get IP and Port Number
    remote = input("Is the server local[1] or remote[2]?")
    IP = gethostbyname(gethostname())
    PORT = 6000
    if remote == "2":
        IP = input("what is the IP address of the server?\n")
        PORT = int(input("what is the port number on the server\n"))

    ADDR = (IP, PORT)
    
    #Connect to server
    client.connect(ADDR)
    
    command = input("Hi, do you want to upload[1], or download[2], or quit[q]?\n")
    
    #if user wants to upload
    if command == '1':
        #print the list of files on the server
        msg = bytes(f'{HEADER2}DATA{HEADER2}LIST{HEADER2}', 'utf-8')
        code = hashcode(msg)
        client.send(code + msg)

        message = client.recv(1024)
        hashCode, cmd, request, body = message.split(HEADER)
        
        #validate correctness of data
        myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
        if not hashCode == myCode:
            client.close()
            print("operation unexpectedly failed")
            
        
        body = body.decode().strip()
        if body:
            print("file on server")
            print(GUI_LINE)
            print(GUI_TITLE)
            print(GUI_LINE)
            print(body)
            print(GUI_LINE)
        #get details of file
        fileName = input("input filename (file extension included e.g cat.png)\n")
        k = 0
        while not os.path.isfile(fileName):
            fileName = input("file path was not found, input correct filename (file extension included e.g cat.png)\n")
            k += 1
            if k == 3:
                quit()
            
        fileType = "open"
        key = ""
        protect = input("Input file key/password, if you don't want to protect it, just press enter\n")
        if not protect == "":
            fileType = "protected"
            key = protect
        
        #send message with filename to user   
        info = bytes(f'{fileName}{SEPARATOR2}{fileType}{SEPARATOR2}{key}','utf-8')
        msg = bytes(f'{HEADER2}FILENAME{HEADER2}UPLOAD{HEADER2}', 'utf-8')
        code = hashcode(msg+info)
        client.send(code+msg+info)

        #wait for response
        message = client.recv(1024)
        hashCode, cmd, request, body = message.split(HEADER)
        myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
        if not hashCode == myCode:
            client.close()
            print("operation unexpectedly failed")
        #open the file
        
        if(body.decode() == "VALID"):
            print("uploading...")
            f = open(fileName, 'rb')
            while True:
                data = f.read(512) #read 512 bytes
                if not data: #oo more bytes to read
                    break

                #send bytes to append to open file
                msg = bytes(f'{HEADER2}DATA{HEADER2}UPLOAD{HEADER2}', 'utf-8')
                code = hashcode(msg+data)
                client.send(code+msg+data)

                #wait for response
                message = client.recv(1024)
                hashCode, cmd, request, body = message.split(HEADER)
                myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
                if not hashCode == myCode:
                    client.close()
                    print("operation unexpectedly failed")
                
        
            #close the file
            f.close()
        
            #send finish message to close the file on server
            message = bytes(f'{HEADER2}FINISH{HEADER2}UPLOAD{HEADER2}', 'utf-8')
            code = hashcode(message)
            client.send(code+message)

            #wait for response
            message = client.recv(1024)
            myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
            if not hashCode == myCode:
                client.close()
                print("operation unexpectedly failed")
        
            #Close socket
            client.close()
            print("upload successful")
            main()
        else:
            print("filename already exists on server")
            main()
        
    #if user wants to download file
    elif command == '2':
        #print the list of files on the server
        msg = bytes(f'{HEADER2}DATA{HEADER2}LIST{HEADER2}', 'utf-8')
        code = hashcode(msg)
        client.send(code + msg)

        message = client.recv(1024)
        hashCode, cmd, request, body = message.split(HEADER)
        myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
        if not hashCode == myCode:
            client.close()
            print("operation unexpectedly failed")
        body = body.decode()
        print("files on server")
        print(GUI_LINE)
        print(GUI_TITLE)
        print(GUI_LINE)
        print(body)
        print(GUI_LINE)
        
        #get details of file to download
        fileName = input("input filename (file extension included e.g cat.png)\n")
        fileType = "open"
        key = ""
        protect = input("Input file key/password, if file is not protected, just press enter\n")
        if not protect == "":
            fileType = "protected"
            key = protect
        
        #send the filename to check the file on the server
        info = bytes(f'{fileName}{SEPARATOR2}{fileType}{SEPARATOR2}{key}','utf-8')
        msg = bytes(f'{HEADER2}FILENAME{HEADER2}DOWNLOAD{HEADER2}', 'utf-8')
        code = hashcode(msg+info)
        client.send(code+msg+info)
        
        message = client.recv(1024)
        hashCode, cmd, request, body = message.split(HEADER)
        myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
        if not hashCode == myCode:
            client.close()
            print("operation unexpectedly failed")
        #if download is approved by server
        if(body.decode() == "VALID"):
            #notify server to send data
            msg = bytes(f'{HEADER2}DATA{HEADER2}DOWNLOAD{HEADER2}', 'utf-8')
            code = hashcode(msg)
            client.send(code+msg)
            
            #open file to write to
            f = open(newpath+"/"+fileName, 'wb')
            
            print("downloading...")
            while True:
                message = client.recv(1024)
                hashCode, cmd, request, body = message.split(HEADER)
                myCode = hashcode(HEADER + cmd + HEADER + request + HEADER + body)
                if not hashCode == myCode:
                    client.close()
                if cmd.decode() == "FINISH":
                    break
                f.write(body)
                #notify server that data is downloaded
                msg = bytes(f'{HEADER2}DATA{HEADER2}DOWNLOADED{HEADER2}', 'utf-8')
                code = hashcode(msg)
                client.send(code+msg)
            #close the file
            f.close()
                
            client.close()
            print("file downloaded")
            main()
        else:
            client.close()
            print("file not found or key is invalid ")
            main()
    elif command == "q":
        client.close()
        quit()
        
    else:
        client.close()
        print("Request not recognised, please press 1 to upload or press 2 to download or q to quit")
        main()


if __name__ == "__main__":
    main()
