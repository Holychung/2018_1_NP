import boto3


ec2 = boto3.resource('ec2', 'ap-northeast-1')
client = boto3.client('ec2')
waiter = client.get_waiter('instance_status_ok')

ListAppServer=[]

user_data="""\n
#cloud-config\n
repo_update: true\n
repo_upgrade: all\n
\n
runcmd:\n
#!/bin/bash\n
- curl -o client.py 52.199.164.17:8000/client.py\n
- curl -o requirements.txt 52.199.164.17:8000/requirements.txt\n
- curl -o hw4_0516205.py 52.199.164.17:8000/hw4_0516205.py\n
- curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py\n
- python3 get-pip.py\n
- pip3 install peewee\n
- pip3 install stomp.py\n
- pip3 install boto3\n
- pip3 install PyMySQL\n
- pip3 install awscli\n
- python3 hw4_0516205.py 0.0.0.0 4321\n
"""

class AppServer(object):
	def __init__(self, instance_id, ip, count, client_token):
		self.instance_id = instance_id
		self.ip = ip
		self.count = count
		self.client_token = [client_token]

	def AddClient(self, token):
		self.count += 1
		self.client_token.append(token)

	def RemoveClient(self, token):
		self.count -= 1
		self.client_token.remove(token)

def CreateInstance(client_token):
	instances = ec2.create_instances(
		ImageId='ami-06c43a7df16e8213c',
		MinCount=1,
		MaxCount=1,
		KeyName='MyKeyPair',
		InstanceType="t2.micro",
		Placement={'AvailabilityZone': 'ap-northeast-1a'},
		UserData=user_data,
		SecurityGroupIds = ['sg-025e1768593cf771e'],
	)
	# Wait Instance
	waiter.wait(
		InstanceIds=[
		instances[0].id,
		],
	)
	# Describe Instance
	response = client.describe_instances(
		InstanceIds=[
			instances[0].id,
		],
	)
	# Add to ListAppServer
	publicIpAddress = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
	tmp_AppServer=AppServer(instances[0].id, publicIpAddress, 0, client_token)
	tmp_AppServer.AddClient(client_token)
	ListAppServer.append(tmp_AppServer)
	return publicIpAddress

print(response['Reservations'])
print(response['Reservations'][0]['Instances'])
print(response['Reservations'][0]['Instances'][0]['PublicIpAddress'])

def LogoutORDelete(user_token):
	# waiter = client.get_waiter('instance_terminated')
	for appServer in ListAppServer:
		for token in appServer.client_token:
			if(user_token == token):
				appServer.RemoveClient(user_token)
				if(appServer.count == 0):
					# No user, Terminate instance and Remove from List
					response = client.terminate_instances(InstanceIds = [appServer.instance_id],)
					ListAppServer.remove(appServer)
					# waiter.wait(
					# 	InstanceIds=[appServer.instance_id],
					# )

print("ok")


def AssignAppServer(client_token):
	publicIpAddress = ''
	needNewServer = 1
	if(len(ListAppServer) == 0):
		needNewServer = 1
	else:
		for appServer in ListAppServer:
			if(appServer.count == 10):
				# Server is now full
				continue
			else:
				# Server is now available
				# Store client token in list, return server ip
				appServer.AddClient(client_token)
				publicIpAddress = appServer.ip
				needNewServer = 0
				break
	if(needNewServer == 1):
		# Create Instance
		CreateInstance(client_token)

	return publicIpAddress



a=AppServer('sid', '140.113', 8, 'a_token')
a.AddClient('bbb')
a.AddClient('ccc')

b=AppServer('sid', '140.777', 10, 'b_token')
ListAppServer.append(a)
ListAppServer.append(b)



print(a.client_token)