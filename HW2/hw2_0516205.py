import socket
import json

user_token = {}

def has_key(key):
	if(key in user_token):
		return 1
	return 0

def replace_token(idx):
	s = ''
	uid = tokens[idx]
	for i in range(len(tokens)):
		if(i == idx):
			if(has_key(uid)):
				# replace token
				s = s + ' ' + user_token[uid]
			else:
				# did not login, replace space
				s = s + ' ' + ' '
		else:
			s = s + ' ' + tokens[i]
	return s

def delete_token(uid):
	if(has_key(uid)):
		del user_token[uid]

# 140.113.207.51
# 8007
SERVER_IP = "140.113.207.51"
PORT = 8007

while(1):
	cmd = input('')
	tokens = cmd.split()
	
	# Exit
	if(cmd == 'exit'):
		user_token.clear()
		break

	# if receive empty string or only spaces
	if(len(tokens) == 0):
		continue

	# if only command no arguements
	if(len(tokens) < 2):
		client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client.connect((SERVER_IP, PORT))
		client.send(cmd.encode("utf-8"))
		result = client.recv(4096).decode('utf-8')
		# print(result)
		try:
			result = json.loads(result)
			print(result['message'])
		except:
			print("Can not parse received json format, message: " + result)
		continue

	# Set ip and port
	if(tokens[0] == 'set'):
		SERVER_IP = tokens[1]
		PORT = int(tokens[2])
		print("Success! IP: " + SERVER_IP + " PORT: " + str(PORT))
		continue

	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.connect((SERVER_IP, PORT))

	# Register
	if(tokens[0] == 'register'):
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		print(result['message'])
	# Login
	elif(tokens[0] == 'login'):
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		if(result['status'] == 1):
			print(result['message'])
		else:
			uid = tokens[1]
			user_token[uid] = result['token']
			print(result['message'])
	# Delete
	elif(tokens[0] == 'delete'):
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		uid = tokens[1]
		if(result['status'] == 1):
			print(result['message'])
		else:
			delete_token(uid)
			print(result['message'])
	# Logout
	elif(tokens[0] == 'logout'): 
		uid = tokens[1]
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		if(result['status'] == 1):
			print(result['message'])
		else:
			delete_token(uid)
			print(result['message'])
	# Invite
	elif(tokens[0] == 'invite'):
		uid = tokens[1] 
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		print(result['message'])
	# List-Invite
	elif(tokens[0] == 'list-invite'):
		uid = tokens[1] 
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		if(result['status'] == 0):
			if((len(result['invite'])) == 0):
				print('No invitations')
			else:
				for i in result['invite']:
					print(i)
		else:
			print(result['message'])
	# Accept-Invite
	elif(tokens[0] == 'accept-invite'):
		uid = tokens[1] 
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		print(result['message'])
	# List-Friend
	elif(tokens[0] == 'list-friend'):
		uid = tokens[1] 
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		if(result['status'] == 0):
			if((len(result['friend'])) == 0):
				print('No friends')
			else:
				for i in result['friend']:
					print(i)
		else:
			print(result['message'])
	# Post
	elif(tokens[0] == 'post'):
		uid = tokens[1] 
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		print(result['message'])
	# Receive-Post
	elif(tokens[0] == 'receive-post'):
		uid = tokens[1] 
		cmd = replace_token(1)
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		if(result['status'] == 0):
			if((len(result['post'])) == 0):
				print('No posts')
			else:
				for post in result['post']:
					print(post['id'] + ':', end=' ')
					print(post['message'])
		else:
			print(result['message'])
	else:
		client.send(cmd.encode("utf-8"))
		result = eval(client.recv(4096).decode('utf-8'))
		print(result['message'])
	client.close()
