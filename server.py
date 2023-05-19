# Server implementation
# Networks 1 Assignment
# LVYARI002, NTLKGO002 & MKMVHU001
# 20 February 2023

import socket
import os
import hashlib

# protocol: hashcode<>cmd<>request<>body
# example: hashcode<>cmd<>request<>fileName#fileType#key

# hash function for message validation
def hashcode(data):
    m = hashlib.sha256()
    m.update(data)
    return bytes(m.hexdigest(),'utf8')

def server():
    
    SEPARATOR = b'<SEPARATOR>' # used for splitting with bytes
    SEPARATOR_2 = "<SEPARATOR>" # used for protocol implementation
    HEADER = b'<HEADER>'
    HEADER_2 = "<HEADER>"
    DIVIDER = "<DIVIDER>"
    
    # some constants
    FILENAME_INDEX = 0
    FILETYPE_INDEX = 1
    KEY_INDEX = 2
    hCode = 0 # hash code for sent messgages
    cCode = 0 # hash code for messages recieved from client
    
    # getting server hostname
    host = ''
    
    port = 6000
    # getting socket instance
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host,port))
    
    # 10 connections are allowed
    server_socket.listen(10)
    
    
    print("Server running")
   
    # allowing connections
    while True:
        conn, address = server_socket.accept()
        print(str(address) + " has connected")
        
        #create folder
        oldpath = os.getcwd()
        newpath = os.path.join(oldpath, r'server_files')
        if not os.path.exists(newpath):
            os.makedirs(newpath)
            
        #create text file to store file information 
        infoFileName = newpath + "/files_info.txt"
        if not os.path.exists(infoFileName):
            infoFile = open(infoFileName, "w")
            infoFile.close()
        
        while True:
        
            message = conn.recv(1024)
            #print(message)
            # checking message is valid
            if len(message.split(HEADER)) != 4:
                print("Disconnected")
                conn.close()                
                break     
            
            # checking that hash code matches
            hCode, cmd, request, body = message.split(HEADER)
            
            client_message = message[message.find(HEADER)::]
            cCode = hashcode(client_message)
            if hCode != cCode:
                # codes don't match -> message is invalid
                # closing connection
                print("Error occurred during message transmission")
                print(message, "\n", client_message)
                print(hCode, "\n", cCode)
                print("Disconnected")
                conn.close() 
                break
            
            # don't want to decode body 
            cmd =cmd.decode()
            request = request.decode()
            
            if cmd == "FILENAME":
                
                # Recieving file information from client
                fileName, fileType, key = body.split(SEPARATOR)
                fileName =fileName.decode()
                fileType = fileType.decode()
                key = key.decode()
            
                if request == "DOWNLOAD":
                    
                    # check that user can access file
                    infoFile = open(infoFileName, "r")
                    entered = False
                    
                    for line in infoFile:
                        fileInfo = line.split(DIVIDER)
                        if fileInfo[FILENAME_INDEX].strip() == fileName:
                            entered = True
                            # found corresponding file
                            if fileInfo[FILETYPE_INDEX].strip() == "open":
                                # fine to download
                                # open file for reading
                                file = open(newpath + "/" + fileName, "rb")
                                msg = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}VALID",'utf-8')
                                hCode = hashcode(msg)
                                conn.send(hCode + msg)
                                break
                            else:
                                # it's protected
                                if fileInfo[KEY_INDEX].strip() == key:
                                    # fine to download
                                    # open file for reading
                                    file = open(newpath + "/" + fileName, "rb")
                                    msg = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}VALID",'utf8')
                                    hCode = hashcode(msg)
                                    conn.send(hCode + msg)
                                    break
                                else:
                                    # wrong key provided
                                    msg = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}INVALID",'utf8')
                                    hCode = hashcode(msg)
                                    conn.send(hCode + msg)
                                    break
                                    
                    infoFile.close()
                    if not entered:
                        # didn't find the file in loop
                        msg = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}INVALID",'utf-8')
                        hCode = hashcode(msg)
                        conn.send(hCode + msg)   

                else:
                    # request == UPLOAD
                    # saving file info to a folder
                    
                    #check if file is not already on the server
                    infoFile = open(infoFileName, "r")
                    found = False
                    for line in infoFile:
                        fileInfo = line.split(DIVIDER)
                        if fileInfo[FILENAME_INDEX].strip() == fileName:
                            found = True
                            
                    infoFile.close()
                    
                    if not found:
                        infoFile = open(infoFileName, "a")
                        infoFile.write(f"{fileName}{DIVIDER}{fileType}{DIVIDER}{key}\n")    
                        infoFile.close()
                
                        # opening file for writing
                        file = open(newpath + "/" + fileName, "wb")
                        msg = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}VALID",'utf8')
                        hCode = hashcode(msg)
                        conn.send(hCode + msg)
                    else:
                        print("File is already uploaded")
                        msg = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}INVALID",'utf8')
                        hCode = hashcode(msg)
                        conn.send(hCode + msg)
                
            elif cmd == "DATA":
            
                if request == "DOWNLOAD":
                    # send file data to client
                    print("Sending file")
                    # sending file
                    while True:
                        bytes_read = file.read(512)
                        if not bytes_read:
                            # file is done sending
                            break
                        # send all bytes
        
                        data = bytes(f"{HEADER_2}DATA{HEADER_2}{request}{HEADER_2}",'utf8')
                        hCode = hashcode(data+bytes_read)
                        conn.send(hCode + data + bytes_read)
                       
                        # use for hashCode vaildation
                        msg = conn.recv(1024)
                        hCode, command, rqType, text = msg.split(HEADER) 
                        
                        client_message = msg[msg.find(HEADER)::]
                        cCode = hashcode(client_message)
                        if hCode != cCode:
                            # codes don't match -> message is invalid
                            # closing connection
                            print("Error occurred during message transmission")
                            print("Disconnected")
                            file.close()
                            conn.close() 
                            break                        
                        #print(message.decode())
                    
                    # finished sending data
                    file.close()
                    note = bytes(f"{HEADER_2}FINISH{HEADER_2}{request}{HEADER_2}",'utf8')
                    hCode = hashcode(note)
                    conn.send(hCode + note)  
                    print("File recieved by client")
                    break
                
                elif request == "LIST":
                    infoFile = open(infoFileName, 'r')
                    data = ""
                    for line in infoFile:
                        fileInfo = line.split(DIVIDER)
                        # not sending key info over
                        data += "| {name:<22}| {types:<14}|\n".format(name = fileInfo[FILENAME_INDEX], types = fileInfo[FILETYPE_INDEX])
                    msg = bytes(f'{HEADER_2}MESSAGE{HEADER_2}LIST{HEADER_2}{data}', 'utf-8')
                    hCode = hashcode(msg)
                    conn.send(hCode + msg)
                    print('File list sent')

                    infoFile.close()                                  
                
                else:
                    # request == UPLOAD
                    # Receiving  file data from client
                    #print(body)
                    file.write(body)
                    
                    note = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}Data Recieved",'utf8')
                    hCode = hashcode(note)
                    conn.send(hCode + note)                    
            
            elif cmd == "FINISH":
                # finishing
            
                file.close()
                print("File downloaded to server")
                note = bytes(f"{HEADER_2}MESSAGE{HEADER_2}{request}{HEADER_2}File is uploaded",'utf8')
                hCode = hashcode(note)
                conn.send(hCode + note)                  
                break  
            
            elif cmd == "ERROR":
                # for invalid files and operations
                body = body.decode()
                if body != "":
                    print(body)
                print("Disconnected")
                conn.close()                
                break
        
        
    
    # closing connection once data is sent
    print("Disconnected")
    conn.close()



if __name__ == '__main__':
    server()
