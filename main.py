import requests
import time
import json
from pprint import pprint
from alive_progress import alive_bar
from urllib.parse import urlencode


def api_request(add_params):
    params = {'access_token': access_token, 'v': '5.52'}
    params.update(add_params)
    URL = 'https://api.vk.com/method/execute'
    try:
        repeat = True
        while repeat:
            response = requests.get(URL, params=params).json()
            if 'error' in response and 'error_code' in response['error'] and response['error']['error_code'] == 6:
                time.sleep(1)
            else:
                repeat = False
        return response["response"]
    except requests.exceptions.ReadTimeout:
        n = 1
        while n < 3:
            print('\n Reconnecting to server. \n')
            try:
                return requests.get(URL, params=params).json()["response"]
            except requests.exceptions.ReadTimeout:
                print('\n Reconnecting to server. \n')
            n+=1     
        else:
            print('Failed, please check your Internet connection.')


def get_user_id():
    user_id = input("Input user ID or screen name: ")
    add_params = {}
    add_params["code"] = "return API.users.get({'user_ids': '" + str(user_id) + "'});"
    try:
        return api_request(add_params)[0]['id']
    except KeyError:
        print("Incorrect input, try again.")
        user_id = get_user_id()
        return user_id


def get_groups_list(user_id):
    add_params = {}
    add_params["code"] = "return API.groups.get({'user_id': '" + str(user_id) + "'});"
    return api_request(add_params)['items']


def get_friends_list(user_id, offset):
    add_params = {}
    add_params["code"] = "return API.friends.get({'user_id': '" + str(user_id) + "', 'count': '200', 'offset': '" + str(offset) + "'});"
    return api_request(add_params)['items']


def is_member(output_groups, group_id, friends_list, friends_limit=0):
    friends_list = ", ".join(list(map(lambda x: str(x), friends_list)))
    add_params = {}
    add_params["code"] = "return API.groups.isMember({'group_id': '" + str(group_id) + "', 'user_ids': '" + friends_list + "'});"
    try:
        response = list(map(lambda x: x['member'], api_request(add_params)))
        if response.count(1) <= friends_limit:
            output_groups.append(group_id)
            return output_groups
        else:
            return output_groups
    except KeyError:
        print(f"Group ID: {group_id} - error, this group is not available!")


def get_group_info(group_id):
    add_params = {}
    add_params["code"] = "return API.groups.getById({'group_id': '" + str(group_id) + "', 'fields': 'members_count'});"
    response = api_request(add_params)
    group_dict = {'name': response[0]['name'], 'id': response[0]['id'], 'members_count': response[0]['members_count']}
    return group_dict


def input_limit():
    friends_limit = input("Count groups with X or less friends in it: ")
    try:
        return int(friends_limit)
    except:
        print("You should input a number!")
        friends_limit = input_limit()
        return int(friends_limit)


def write_json(output_groups):
    output_groups = set(output_groups)
    output_list = []
    with alive_bar(len(output_groups)) as bar:
        print("\nGetting groups info...")
        for group in output_groups:
            bar()
            output_list.append(get_group_info(group))    
    with open('groups.json', 'w') as groups_file:
        json.dump(output_list, groups_file, ensure_ascii=False, indent=4)


def match_groups_friends(groups_list, friends_limit, user_id):
    output_groups = []
    offset = 0
    friends_list = get_friends_list(user_id, offset)
    while len(friends_list) != 0:
        with alive_bar(len(groups_list)) as bar:
            print("\nMatching friends and groups...")
            for group in groups_list:
                bar()
                output_groups = is_member(output_groups, group, friends_list, friends_limit)
        offset += 200
        friends_list = get_friends_list(user_id, offset)
    return output_groups


if __name__ == "__main__":
    access_token = input("Please input access token: ")
    user_id = get_user_id()
    groups_list = get_groups_list(user_id)
    friends_limit = input_limit()

    output_groups = match_groups_friends(groups_list, friends_limit, user_id)
    write_json(output_groups)

    print('\nDone! All information was saved to "groups.json" file.')