import sys
import socket
import json
import os
import stomp


class MQListener(stomp.ConnectionListener):
    def on_message(self, headers, msg):
        content = json.loads(msg)
        if content['type'] == 0:
            print('<<<{}->{}: {}>>>'.format(content['from'], content['to'], content['message']))
        else:
            print('<<<{}->GROUP<{}>: {}>>>'.format(content['from'], content['to'], content['message']))
    def on_error(self, headers, message):
        print('received an error "%s"' % message)

class Client(object):
    def __init__(self, ip, port):
        try:
            socket.inet_aton(ip)
            if 0 < int(port) < 65535:
                self.ip = ip
                self.port = int(port)
            else:
                raise Exception('Port value should between 1~65535')
            self.cookie = {}
            self.group = {}
        except Exception as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        try:
            self.mq = stomp.Connection([('140.113.207.51', 61613)])
            self.mq.set_listener('mq', MQListener())
            self.mq.start()
            self.mq.connect(wait=True)
        except Exception as e:
            print(e, file=sys.stderr)

    def run(self):
        while True:
            cmd = sys.stdin.readline()
            if cmd == 'exit' + os.linesep:
                return
            if cmd != os.linesep:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect((self.ip, self.port))
                        req = self.__attach_token(cmd)
                        s.send(req.encode())
                        resp = s.recv(4096).decode()
                        self.handle_result(json.loads(resp), cmd)
                except Exception as e:
                    print(e, file=sys.stderr)

    def handle_result(self, resp, cmd=None):
        if 'message' in resp:
            print(resp['message'])

        if 'invite' in resp:
            if len(resp['invite']) > 0:
                for l in resp['invite']:
                    print(l)
            else:
                print('No invitations')

        if 'friend' in resp:
            if len(resp['friend']) > 0:
                for l in resp['friend']:
                    print(l)
            else:
                print('No friends')

        if 'post' in resp:
            if len(resp['post']) > 0:
                for p in resp['post']:
                    print('{}: {}'.format(p['id'], p['message']))
            else:
                print('No posts')

        if 'group' in resp:
            if len(resp['group']) > 0:
                for g in resp['group']:
                    print(g)
            else:
                print('No groups')

        if cmd:
            command = cmd.split()
            if resp['status'] == 0:
                if command[0] == 'login':
                    self.cookie[command[1]] = resp['token']
                    self.group[command[1]] = []
                    for g in resp['channel']:
                        if g['type'] == 0:
                            self.mq.subscribe('/queue/' + g['channel'], command[1])
                        else:
                            self.mq.subscribe('/topic/' + g['channel'], g['name'] + command[1])
                            self.group[command[1]].append(g['name'] + command[1])
                elif command[0] == 'create-group' or command[0] == 'join-group':
                    self.mq.subscribe('/topic/' + resp['channel'], command[2] + command[1])
                    self.group[command[1]].append(command[2] + command[1])
                elif command[0] == 'logout' or command[0] == 'delete':
                    self.mq.unsubscribe(command[1])
                    for g in self.group[command[1]]:
                        self.mq.unsubscribe(g)
                    del self.group[command[1]]

    def __attach_token(self, cmd=None):
        if cmd:
            command = cmd.split()
            if len(command) > 1:
                if command[0] != 'register' and command[0] != 'login':
                    if command[1] in self.cookie:
                        command[1] = self.cookie[command[1]]
                    else:
                        command.pop(1)
            return ' '.join(command)
        else:
            return cmd


def launch_client(ip, port):
    c = Client(ip, port)
    c.run()

if __name__ == '__main__':
    if len(sys.argv) == 3:
        launch_client(sys.argv[1], sys.argv[2])
    else:
        print('Usage: python3 {} IP PORT'.format(sys.argv[0]))
