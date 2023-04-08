import json
import random
from helpers import *
import os


per_page = 120
sleep_period_between_each_request_by_seconds = 1
max_retry = 5
# 15 minutes = (60 seconds = 1 minute) * (15 minutes) = 900 seconds
sleep_period_between_each_retry = 1
max_of_requests = 110  # each request equal to 1000 users
max_of_users = 10000  # each request equal to 1000 users
max_of_create_followers_file = 300

shuffle_system = True

parent = 'adidas-300114634'
directory = f'users/{parent}/followers' if parent else f'users/followers'
work_in_sub_directory = True

dir_list = sorted(os.listdir(directory))

if shuffle_system:
    random.shuffle(dir_list)

all_request = 0
all_users = 0

for dir in dir_list:
    start_fetch = open(createRealPath(directory, dir))
    users_to_fetch_followers = json.load(start_fetch)

    users_to_fetch_followers = users_to_fetch_followers.get('users', list())
    if shuffle_system:
        random.shuffle(users_to_fetch_followers)

    for user_to_fetch_followers in users_to_fetch_followers:

        request_count = 0
        count_retry = 0
        users_count = 0
        twitter_info = open('twitter_info.json')
        data = json.load(twitter_info)

        variables = random.choice(data['variables'])
        features = random.choice(data['features'])

        user_id = user_to_fetch_followers.get('content', dict()).get('itemContent', dict()).get(
            'user_results', dict()).get('result', dict()).get('rest_id', '123456789')  # '300114634'
        screen_name = user_to_fetch_followers.get('content', dict()).get('itemContent', dict()).get(
            'user_results', dict()).get('result', dict()).get('legacy', dict()).get('screen_name', '123456789')  # 'nike'
        # cursor = None  # "cursor": "1761682985370050002|1640969515229511638",

        print(
            f" ==================  Start at work in {datetime.now().strftime('%H:%M:%S')} for user id: {user_id} by screen name: {screen_name} ==================")

        path_followers = f'users/{parent}/{screen_name}-{user_id}/followers' if parent else f'users/{screen_name}-{user_id}/followers'
        path_info = f'users/{parent}/{screen_name}-{user_id}/info.json' if parent else f'users/{screen_name}-{user_id}/info.json'

        is_exist = checkIfUserDir(path_followers)

        createInfoFile(path_info, user_to_fetch_followers)

        users = True
        request_count, cursor = checkCursorAndFileNumber(
            path_followers, screen_name)

        if is_exist:
            if checkCountFetchFollowers(path_followers, max_of_create_followers_file):
                break

        while users:
            headers = random.choice(data['headers'])
            previous_cursor = cursor
            users, cursor, retry, request_count, count_retry = fetchUsers(headers, variables, features, user_id, per_page, cursor, request_count, screen_name,
                                                                          path_followers, sleep_period_between_each_request_by_seconds, count_retry)
            all_request += 1
            users_count += (users if isinstance(users, int) else 0)
            all_users += (users if isinstance(users, int) else 0)
            if retry:
                print(
                    f"Stop For {int(sleep_period_between_each_retry/60)} Minutes To retry again")
                print(f"count of user until this moment {all_users}")
                sleep(sleep_period_between_each_retry)
                users = True
                cursor = previous_cursor
            if count_retry > max_retry:
                print(
                    f"try for user_id {user_id} retry {count_retry} times break in {datetime.now().strftime('%H:%M:%S')}")
                print(f"count of user until this moment {all_users}")
                print("break while loop and start fetch new user because max retry")
                break
            if request_count > max_of_requests:
                print(
                    f"try for user_id {user_id} request {request_count} times break in {datetime.now().strftime('%H:%M:%S')}")
                print(f"count of user until this moment {all_users}")
                print("break while loop and start fetch new user because max request")
                break
            if users_count > max_of_users:
                print(
                    f"try for user_id {user_id} user count {users_count} times break in {datetime.now().strftime('%H:%M:%S')}")
                print(f"count of user until this moment {all_users}")
                print("break while loop and start fetch new user because max users")
                break

print(f"All request equal to {all_request}")
print(f"And count of user fetch equal to {all_users}")
