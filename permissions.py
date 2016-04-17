
from collections import OrderedDict
import json

def set_permission(message, type, to_set, permission, setting):
	try:
		with open("data/" + message.server.id + "_permissions.json", "x+") as permissions_file:
			json.dump({"name" : message.server.name}, permissions_file)
	except FileExistsError:
		pass
	with open("data/" + message.server.id + "_permissions.json", "r") as permissions_file:
		permissions_data = json.load(permissions_file)
	if type == "everyone":
		if not "everyone" in permissions_data:
			permissions_data["everyone"] = {permission : setting}
		else:
			permissions_data["everyone"][permission] = setting
	elif type == "role":
		if not "roles" in permissions_data:
			role = find_role(message, to_set)
			permissions_data["roles"] = {to_set : {"name" : role.name, permission : setting}}
		elif not to_set in permissions_data["roles"]:
			role = find_role(message, to_set)
			permissions_data["roles"][to_set] = {"name" : role.name, permission : setting}
		else:
			permissions_data["roles"][to_set][permission] = setting
	elif type == "user":
		if not "users" in permissions_data:
			user = find_user(message, to_set)
			permissions_data["users"] = {to_set : {"name" : user.name, permission : setting}}
		elif not to_set in permissions_data["users"]:
			user = find_user(message, to_set)
			permissions_data["users"][to_set] = {"name" : user.name, permission : setting}
		else:
			permissions_data["users"][to_set][permission] = setting
	with open("data/" + message.server.id + "_permissions.json", "w") as permissions_file:
		json.dump(permissions_data, permissions_file)

def get_permission(message, type, to_find, permission):
	try:
		with open("data/" + message.server.id + "_permissions.json", "x+") as permissions_file:
			json.dump({"name" : message.server.name}, permissions_file)
	except FileExistsError:
		pass
	with open("data/" + message.server.id + "_permissions.json", "r") as permissions_file:
		permissions_data = json.load(permissions_file)
	if type == "everyone":
		return check_everyone(permissions_data, permission)
	elif type == "role":
		if check_role(permissions_data, to_find, permission) == -1:
			return check_everyone(permissions_data, permission)
		else:
			return check_role(permissions_data, to_find, permission)
	elif type == "user":
		if check_user(permissions_data, to_find, permission) == -1:
			user = find_user(message, to_find)
			role_positions = {}
			for role in user.roles:
				role_positions[role.position] = role
			sorted_role_positions = OrderedDict(sorted(role_positions.items(), reverse = True))
			for role_position, role in sorted_role_positions.items():
				if check_role(permissions_data, role.id, permission) != -1:
					return check_role(permissions_data, role.id, permission)
			return check_everyone(permissions_data, permission)
		else:
			return check_user(permissions_data, to_find, permission)

def check_everyone(permissions_data, permission):
	if not "everyone" in permissions_data or not permission in permissions_data["everyone"]:
			return -1
	else:
		return permissions_data["everyone"][permission]

def check_role(permissions_data, to_find, permission):
	if not "roles" in permissions_data or not to_find in permissions_data["roles"] or not permission in permissions_data["roles"][to_find]:
		return -1
	else:
		return permissions_data["roles"][to_find][permission]

def check_user(permissions_data, to_find, permission):
	if not "users" in permissions_data or not to_find in permissions_data["users"] or not permission in permissions_data["users"][to_find]:
		return -1
	else:
		return permissions_data["users"][to_find][permission]

def find_role(message, role_id):
	for role in message.server.roles:
		if role.id == role_id:
			return role
	
def find_user(message, user_id):
	for member in message.server.members:
		if member.id == user_id:
			return member
