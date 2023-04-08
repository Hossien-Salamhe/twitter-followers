import json
import os
import urllib
import requests
import time
from datetime import datetime

debug_status = True


def fetchUsers(headers, variables, features, user_id, per_page, cursor, request_count, screen_name, directory,sleep_period_between_each_request_by_seconds, count_retry):
    parameters = prepareQuery(variables, features, user_id, per_page, cursor)
    users, cursor, retry, count_retry = fetchUsersAndCursorResponse(
        headers, parameters, count_retry=count_retry)
    request_count = addCountRequest(request_count, len(users) if users else 0)
    if retry:
        return users, cursor, retry, request_count, count_retry
    cursor = prepareCursor(cursor, directory)
    appendUsersToFile(users, screen_name, directory,
                      appendEveryTenRequestInOneFile(request_count))
    sleep(sleep_period_between_each_request_by_seconds)
    return len(users), cursor, retry, request_count, count_retry


def prepareVariableQuery(variables, userId, count, cursor=None):
    variables['userId'] = userId
    variables['count'] = count
    if cursor:
        res = dict()
        for key in variables:
            res[key] = variables[key]
            if key == 'count':
                res.update({'cursor': cursor})
    else:
        res = variables

    # debug_print(res, 'res = variables')
    return res


def prepareQuery(variables, features, userId, per_page, cursor):
    variables = prepareVariableQuery(variables, userId, per_page, cursor)
    query = {
        'variables': json.dumps(variables),
        'features': json.dumps(features),
    }

    parameters = urllib.parse.urlencode(query)
    # debug_print(parameters, 'parameters')
    return parameters


def fetchUsersAndCursorResponse(headers, parameters,
                                url="https://twitter.com/i/api/graphql/xjJ7_nvN1nSB_z0VsPTG0Q/Followers", count_retry=0):
    try:
        req = requests.get(url=url, headers=headers, params=parameters)
    except requests.exceptions.ConnectionError:
        print("Connection refused")
        count_retry += 1
        # err_file = open('errors/requests/error.txt', 'a')
        # err_file.write(req.text)
        return None, [], True, count_retry
    try:
        debug_print(req.url, "req_url")
        return sliceUsersAndCursorFromResponse(req.json(), count_retry)
    except requests.exceptions.JSONDecodeError:
        print("Expecting value convert to json")
        count_retry += 1
        # err_file = open('errors/requests/error.txt', 'a')
        # err_file.write(req.text)
        return None, [], True, count_retry


def sliceUsersAndCursorFromResponse(response, count_retry):
    entries = dict()
    instructions = (
        response.get('data', dict())
        .get('user', dict())
        .get('result', dict())
        .get('timeline', dict())
        .get('timeline', dict())
        .get('instructions', dict())
    )

    if instructions:
        # index = 2 if len(instructions) == 3 else 0
        entries = instructions[-1].get('entries', list())

    return saveUsersInFileAndGenerateCursor(entries, count_retry)


def saveUsersInFileAndGenerateCursor(entries, count_retry):
    # TODO:: get users and slice 2 last record and generate next cursor to next page
    retry = False
    if entries:
        separator = len(entries) - 2
        users = entries[:separator]
        cursor = entries[separator:]
        return users, cursor, retry, 0
    else:
        retry = True
        return None, None, retry, count_retry + 1


def prepareCursor(cursor, directory):
    try:
        cursor_bottom = cursor[0]
        content_value = cursor_bottom.get('content', dict()).get('value', '')
        saveCursorInFile(content_value, directory)
        return content_value
    except IndexError:
        return ''


def saveCursorInFile(cursor, directory):
    checkIfUserDir(directory)
    cursor_file_path = f"{directory}/cursors.txt"
    cursor_file = open(cursor_file_path, 'a')
    cursor_file.write(cursor + '\n')


def appendUsersToFile(users, screen_name, directory, number_file, zero_left_pad_string=6):
    checkIfUserDir(directory)
    path = f'{directory}/{screen_name}-{str(number_file).zfill(zero_left_pad_string)}.json'

    file_existed = os.path.isfile(path)

    if file_existed:
        fetched_users_file = open(path, 'r+')
        fetched_users = json.load(fetched_users_file)
        fetched_users.get('users').extend(users)
        fetched_users_file.seek(0)
        fetched_users_file.truncate()
    else:
        fetched_users_file = open(path, 'w+')
        fetched_users = dict({'users': users})

    json.dump(fetched_users, fetched_users_file)


def checkIfUserDir(path="users"):
    isExist = os.path.exists(path)
    if not isExist:
        os.makedirs(path)
        return False  # new
    return True  # already exists


def addCountRequest(request_count, len_users):
    if len_users:
        request_count += 1
    print(
        f" ***** request {request_count} with => {len_users} users => {datetime.now().strftime('%H:%M:%S')}")
    return request_count


def debug_print(variable, name, sleep=1):
    if debug_status:
        print(f" =========== start of {name} ===========")
        print(type(variable))
        print("======================")
        print(variable)
        print(f" =========== end of {name} ===========")
        time.sleep(sleep)


def appendEveryTenRequestInOneFile(request_count):
    return int(request_count / 10)


def sleep(second):
    time.sleep(second)


def checkCursorAndFileNumber(dir_path, screen_name):
    cursor_file_name = "cursors.txt"
    isExist = os.path.exists(dir_path)
    if not isExist:
        return 0, None
    dir_list = os.listdir(dir_path)
    dir_list.sort()
    dir_list = [file for file in dir_list if screen_name in file]
    file_number = int(dir_list[-1].split('-')
                      [-1].split('.')[0]) if dir_list else 0

    cursor_file = open(createRealPath(dir_path, cursor_file_name), 'w+')

    cursor_file_readlines = cursor_file.readlines()

    cursor = (cursor_file_readlines[len(
        cursor_file_readlines) - 1])[:-1] if cursor_file_readlines else None

    return file_number * 10, cursor


def createRealPath(path, file):
    return path + '/' + file


def createInfoFile(path, user_to_fetch_followers):
    fetched_users_file = open(path, 'w')
    json.dump(user_to_fetch_followers, fetched_users_file)


def checkCountFetchFollowers(path_followers, max_of_create_followers_file=300):
    dir_list = sorted(os.listdir(path_followers))
    return len(dir_list) > max_of_create_followers_file
