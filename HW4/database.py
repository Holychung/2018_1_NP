import peewee
from peewee import *
import uuid
import json

mysql_db = peewee.MySQLDatabase(host='localhost', user='root', database='np', password='mickey94378', charset='utf8mb4')
mysql_db.connect()

class BaseModel(Model):
	class Meta:
		database = mysql_db

class User(BaseModel):
	uid = CharField(primary_key=True, max_length=100)
	password = TextField()
	token = TextField(null=True, default=None)

class Invite(BaseModel):
	uid_sender = CharField(max_length=100)
	uid_receiver = CharField(max_length=100)
	class Meta:
		primary_key = CompositeKey('uid_sender', 'uid_receiver')

class Friend(BaseModel):
	uid = CharField(max_length=100)
	uid_friend = CharField(max_length=100)
	class Meta:
		primary_key = CompositeKey('uid', 'uid_friend')

class Post(BaseModel):
	uid = CharField(max_length=100)
	message = TextField()

class Groups(BaseModel):
	groupname = CharField(max_length=100)
	uid = CharField(max_length=100)

# truncate table user; truncate table invite; truncate table friend; truncate table post; truncate table groups;

# create table
User.create_table()
Invite.create_table()
Friend.create_table()
Post.create_table()
Groups.create_table()

def validate_token(token):
	user = User.select().where(User.token == token).dicts()
	if(len(user) > 0):
		return True
	else:
		return False

def get_uid(token):
	user = User.select().where(User.token == token).dicts()
	return user[0]['uid']

def check_uid_exist(uid):
	user = User.select().where(User.uid == uid).dicts()
	if(len(user) > 0):
		return True
	else:
		return False

def validate_account(uid, password):
	user = User.select().where(User.uid == uid, User.password == password).dicts()
	if(len(user) > 0):
		return True
	else:
		return False

def check_friendship(uid, uid_friend):
	check_friendship = Friend.select().where(Friend.uid == uid, Friend.uid_friend == uid_friend).dicts()
	if(len(check_friendship) > 0):
		return True
	else:
		return False

def check_already_invite(uid_sender, uid_receiver):
	invited = Invite.select().where(Invite.uid_sender == uid_sender, Invite.uid_receiver == uid_receiver).dicts()
	if(len(invited) > 0):
		return True
	else:
		return False

def has_be_invited(uid_sender, uid_receiver):
	invited = Invite.select().where(Invite.uid_sender == uid_receiver, Invite.uid_receiver == uid_sender).dicts()
	if(len(invited) > 0):
		return True
	else:
		return False

def create_token():
	return str(uuid.uuid1())

def check_token_exist(uid):
	user = User.select().where(User.uid == uid).dicts()
	if(user[0]['token'] == None):
		return False
	return True

def get_token(uid):
	user = User.select().where(User.uid == uid).dicts()
	return user[0]['token']

def list_invite(uid):
	array = []
	invite = Invite.select().where(Invite.uid_sender==uid).dicts()
	for row in invite:
		array.append(row['uid_receiver'])
	return array

def list_friend(uid):
	array = []
	friend = Friend.select().where(Friend.uid==uid).dicts()
	for row in friend:
		array.append(row['uid_friend'])
	return array

def create_friendship(uid, uid_friend):
	Friend.create(uid=uid, uid_friend=uid_friend)
	Friend.create(uid=uid_friend, uid_friend=uid)
	return None

def parse_message(tokens):
	sequence = []
	for i in range(len(tokens)):
		if(i == 0 or i == 1):
			continue
		sequence.append(tokens[i])
	message = ' '.join(sequence)
	return message

def post_message(sender, message):
	for friend in list_friend(sender):
		print(friend)
		Post.create(uid=friend, message=message)
	return None

def list_post(uid):
	array = []
	friend = Friend.select().where(Friend.uid==uid).dicts()
	for i in range(len(friend)):
		friend_uid = friend[i]['uid_friend']
		post = Post.select().where(Post.uid==friend_uid).dicts()
		for j in range(len(post)):
			obj = {}
			obj['id'] = post[j]['uid']
			obj['message'] = post[j]['message']
			array.append(obj)
	return array

def delete_account(uid):
	User.delete().where(User.uid==uid).execute()
	Invite.delete().where(Invite.uid_sender==uid).execute()
	Invite.delete().where(Invite.uid_receiver==uid).execute()
	Post.delete().where(Post.uid==uid).execute()
	Friend.delete().where(Friend.uid==uid).execute()
	Friend.delete().where(Friend.uid_friend==uid).execute()
	return None

# hw4
def parse_message_2(tokens):
	sequence = []
	for i in range(len(tokens)):
		if(i == 0 or i == 1 or i == 2):
			continue
		sequence.append(tokens[i])
	message = ' '.join(sequence)
	return message

def check_group_exist(groupname):
	group = Groups.select().where(Groups.groupname == groupname).dicts()
	if(len(group) > 0):
		return True
	else:
		return False

def create_group(uid, groupname):
	Groups.create(uid=uid, groupname=groupname)
	return None

def list_group():
	array = []
	grouplist = Groups.select().distinct().dicts()
	for row in grouplist:
		array.append(row['groupname'])
	return array

def list_joined(uid):
	array = []
	joinedlist = Groups.select().where(Groups.uid == uid).dicts()
	for row in joinedlist:
		array.append(row['groupname'])
	return array

def check_joined_group(uid, groupname):
	group = Groups.select().where(Groups.uid == uid, Groups.groupname == groupname).dicts()
	if(len(group) > 0):
		return True
	else:
		return False

def join_group(uid, groupname):
	Groups.create(uid=uid, groupname=groupname)
	return None

# Test section
User.create(uid = '111', password='111', token='aaa')
User.create(uid = '222', password='222', token='bbb')
User.create(uid = '333', password='333', token='bbb')
# Post.create(uid = '111', message='aaa')
# Post.create(uid = '111', message='bbb')
# Post.create(uid = '333', message='bbb')
# create_friendship('222', '111')
# create_friendship('333', '222')
# print(list_post(uid='222'))
create_group('111', 'A')
create_group('222', 'B')
create_group('333', 'C')
for row in list_group():
	print(row)
print(check_group_exist('A'))
join_group('111', 'C')
join_group('222', 'A')
join_group('333', 'B')
for row in list_joined('111'):
	print(row)
print(check_joined_group('111', 'C'))
print("finish!")




# if(validate_token('aaa')):
# 	Invite.create(uid_sender='111', uid_receiver='222')
# print(check_uid_exist('111'))
# print(validate_account('111', '111'))
# print(check_friendship('111', '222'))
# print(check_already_invite('111', '222'))
# print(has_be_invited('111', '222'))

# User.create(uid = '333', password='333', token=None)
# create record
# book1 = Book.create(bid = 123, author = '我是來側長度的你確定要這麼長嗎', title = 'WTF')
# User.create(bid = 123, uname = 'holy', uid = 555)
# User.update(token=create_token()).where(User.uid=='111').execute()

# create_friendship('111', '222')
# print(list_friend('111'))

# DELETE INSTANCE
# book1 = Book.get(author = '我是來側長度的')
# book1.delete_instance()
# Invite.delete().where(Invite.uid_sender=='111').execute()

# SELECT
# all_book = Book.select().dicts() # dicts tuples
# for row in all_book:
# 	print(type(row))

# JOIN  WHERE
# all_book = Book.select().join(User, on=(Book.bid == User.bid)).where(Book.timestamp < datetime.datetime(2018, 10, 28, 17, 26)).dicts() # dicts tuples
# for row in all_book:
	# print(row)

# BULK INSERT
# data_source = [
#     {'field1': 'val1-1', 'field2': 'val1-2'},
#     {'field1': 'val2-1', 'field2': 'val2-2'},
# ]
# for data_dict in data_source:
#     MyModel.create(**data_dict)