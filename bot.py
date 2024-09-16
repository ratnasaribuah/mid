from colorama import *
from datetime import datetime, timedelta
from fake_useragent import FakeUserAgent
from faker import Faker
from requests import (
    JSONDecodeError,
    RequestException,
    Session
)
from time import sleep
import json
import os
import re
import sys

class Midas:
    def __init__(self) -> None:
        self.session = Session()
        self.faker = Faker()
        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Host': 'api-tg-app.midas.app',
            'Origin': 'https://prod-tg-app.midas.app',
            'Pragma': 'no-cache',
            'Referer': 'https://prod-tg-app.midas.app/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': FakeUserAgent().random
        }

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_timestamp(self, message):
        print(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{message}",
            flush=True
        )

    def load_queries(self, file_path):
        with open(file_path, 'r') as file:
            return [line.strip() for line in file if line.strip()]

    def process_queries(self, lines_per_file: int):
        if not os.path.exists('queries.txt'):
            raise FileNotFoundError(f"File 'queries.txt' not found. Please ensure it exists.")

        with open('queries.txt', 'r') as f:
            queries = [line.strip() for line in f if line.strip()]
        if not queries:
            raise ValueError("File 'queries.txt' is empty.")

        existing_queries = set()
        for file in os.listdir():
            if file.startswith('queries-') and file.endswith('.txt'):
                with open(file, 'r') as qf:
                    existing_queries.update(line.strip() for line in qf if line.strip())

        new_queries = [query for query in queries if query not in existing_queries]
        if not new_queries:
            self.print_timestamp(f"{Fore.YELLOW + Style.BRIGHT}[ No New Queries To Add ]{Style.RESET_ALL}")
            return

        files = [f for f in os.listdir() if f.startswith('queries-') and f.endswith('.txt')]
        files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)

        last_file_number = int(re.findall(r'\d+', files[-1])[0]) if files else 0

        for i in range(0, len(new_queries), lines_per_file):
            chunk = new_queries[i:i + lines_per_file]
            if files and len(open(files[-1], 'r').readlines()) < lines_per_file:
                with open(files[-1], 'a') as outfile:
                    outfile.write('\n'.join(chunk) + '\n')
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Updated '{files[-1]}' ]{Style.RESET_ALL}")
            else:
                last_file_number += 1
                queries_file = f"queries-{last_file_number}.txt"
                with open(queries_file, 'w') as outfile:
                    outfile.write('\n'.join(chunk) + '\n')
                self.print_timestamp(f"{Fore.GREEN + Style.BRIGHT}[ Generated '{queries_file}' ]{Style.RESET_ALL}")

    def register(self, queries: str):
        url = 'https://api-tg-app.midas.app/api/auth/register'
        tokens = []
        for query in queries:
            data = json.dumps({'initData':query,'source':'ref_84e9c8fc-be5d-4f6e-aef7-9671e31415cf'})
            headers = {
                **self.headers,
                'Content-Length': str(len(data)),
                'Content-Type': 'application/json'
            }
            try:
                response = self.session.post(url=url, headers=headers, data=data)
                response.raise_for_status()
                token = response.text
                tokens.append(token)
            except (Exception, JSONDecodeError, RequestException) as e:
                self.print_timestamp(
                    f"{Fore.YELLOW + Style.BRIGHT}[ Failed To Process {query} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}"
                )
                continue
        return tokens

    def user_visited(self, token: str):
        url = 'https://api-tg-app.midas.app/api/user/visited'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': 'application/json'
        }
        try:
            response = self.session.patch(url=url, headers=headers)
            response.raise_for_status()
            return True
        except (Exception, JSONDecodeError, RequestException):
            return False

    def user(self, token: str):
        url = 'https://api-tg-app.midas.app/api/user'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}'
        }
        try:
            response = self.session.get(url=url, headers=headers)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching User: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching User: {str(e)} ]{Style.RESET_ALL}")

    def get_streak(self, token: str, first_name: str):
        url = 'https://api-tg-app.midas.app/api/streak'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}'
        }
        try:
            response = self.session.get(url=url, headers=headers)
            response.raise_for_status()
            streak = response.json()
            if streak['claimable']:
                return self.post_streak(token=token, first_name=first_name, points=streak['nextRewards']['points'], tickets=streak['nextRewards']['tickets'])
            return self.print_timestamp(
                f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.MAGENTA + Style.BRIGHT}[ Daily Streak Already Claimed ]{Style.RESET_ALL}"
            )
        except RequestException as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Streak: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Streak: {str(e)} ]{Style.RESET_ALL}")

    def post_streak(self, token: str, first_name: str, points: int, tickets: int):
        url = 'https://api-tg-app.midas.app/api/streak'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = self.session.post(url=url, headers=headers)
            response.raise_for_status()
            streak = response.json()
            return self.print_timestamp(
                f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.GREEN + Style.BRIGHT}[ Claimed Daily Streak ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}[ Day {streak['streakDaysCount']} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT}[ Points {points} Tickets {tickets} ]{Style.RESET_ALL}"
            )
        except RequestException as e:
            if e.response.status_code == 400:
                error_post_streak = response.json()
                if error_post_streak['message'] == 'Can\'t claim streak now':
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Cannot Claim Streak Now ]{Style.RESET_ALL}"
                    )
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Streak: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Streak: {str(e)} ]{Style.RESET_ALL}")

    def play(self, token: str, first_name: str):
        url = 'https://api-tg-app.midas.app/api/game/play'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        while True:
            try:
                response = self.session.post(url=url, headers=headers)
                response.raise_for_status()
                play_game = response.json()
                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Claimed {play_game['points']} From Tapping Rock ]{Style.RESET_ALL}"
                )
            except RequestException as e:
                if e.response.status_code == 400:
                    error_play = response.json()
                    if error_play['message'] == 'Not enough tickets':
                        self.print_timestamp(
                            f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                            f"{Fore.YELLOW + Style.BRIGHT}[ Not Enough Tickets ]{Style.RESET_ALL}"
                        )
                        break
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Play Game: {str(e.response.reason)} ]{Style.RESET_ALL}")
                break
            except (Exception, JSONDecodeError) as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Play Game: {str(e)} ]{Style.RESET_ALL}")
                break

    def claim_referral(self, token: str, first_name: str):
        url = ' https://api-tg-app.midas.app/api/referral/claim'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = self.session.post(url=url, headers=headers)
            response.raise_for_status()
            claim_referral = response.json()
            if claim_referral['message'] == 'Rewards claimed successfully':
                return self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Rewards Frens Claimed Successfully ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}[ Points {claim_referral['totalPoints']} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}[ Tickets {claim_referral['totalTickets']} ]{Style.RESET_ALL}"
                )
        except RequestException as e:
            if e.response.status_code == 400:
                error_claim_referral = response.json()
                if error_claim_referral['message'] == 'No rewards available to claim':
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.YELLOW + Style.BRIGHT}[ Not Enough Tickets ]{Style.RESET_ALL}"
                    )
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Referral: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Referral: {str(e)} ]{Style.RESET_ALL}")

    def available_tasks(self, token: str, first_name: str):
        url = 'https://api-tg-app.midas.app/api/tasks/available'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}'
        }
        try:
            response = self.session.get(url=url, headers=headers)
            response.raise_for_status()
            tasks = response.json()
            for task in tasks:
                if task['completed'] == False:
                    if task['mechanic'] == 'START_WAIT_CLAIM':
                        if task['state'] == 'WAITING':
                            self.start_task(token=token, first_name=first_name, task_id=task['id'], task_name=task['name'], task_points=task['points'])
                        elif task['state'] == 'CLAIMABLE':
                            self.claim_task(token=token, first_name=first_name, task_id=task['id'], task_name=task['name'], task_points=task['points'])
                    elif task['mechanic'] == 'CHECK_STATUS_CLAIM':
                        if task['state'] == 'CLAIMABLE':
                            self.claim_task(token=token, first_name=first_name, task_id=task['id'], task_name=task['name'], task_points=task['points'])
        except RequestException as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Fetching Tasks: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Fetching Tasks: {str(e)} ]{Style.RESET_ALL}")

    def start_task(self, token: str, first_name: str, task_id: str, task_name: str, task_points: int):
        url = f'https://api-tg-app.midas.app/api/tasks/start/{task_id}'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = self.session.post(url=url, headers=headers)
            response.raise_for_status()
            start_task = response.json()
            if start_task['state'] == 'CLAIMABLE':
                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.YELLOW + Style.BRIGHT}[ {task_name} Started ]{Style.RESET_ALL}"
                )
                sleep_duration = (datetime.fromisoformat(start_task['canBeClaimedAt'].replace('Z', '+00:00')).astimezone() - datetime.now().astimezone()).total_seconds() + 3
                if sleep_duration > 0:
                    sleep(sleep_duration)
                return self.claim_task(token=token, first_name=first_name, task_id=task_id, task_name=task_name, task_points=task_points)
        except RequestException as e:
            if e.response.status_code == 400:
                error_start_task = response.json()
                if error_start_task['message'] == f'User task with ID {task_id} cannot be started because it is not in a waiting state':
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.RED + Style.BRIGHT}[ {task_name} Cannot Be Started Because It Is Not In A Waiting State ]{Style.RESET_ALL}"
                    )
                elif error_start_task['message'] == f'Task type with ID {task_id} cannot be started with START_WAIT_CLAIM mechanic':
                    return self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.RED + Style.BRIGHT}[ {task_name} Cannot Be Started With START_WAIT_CLAIM Mechanic ]{Style.RESET_ALL}"
                    )
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Start Tasks: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Start Tasks: {str(e)} ]{Style.RESET_ALL}")

    def claim_task(self, token: str, first_name: str, task_id: str, task_name: str, task_points: int):
        url = f'https://api-tg-app.midas.app/api/tasks/claim/{task_id}'
        headers = {
            **self.headers,
            'Authorization': f'Bearer {token}',
            'Content-Length': '0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        try:
            response = self.session.post(url=url, headers=headers)
            response.raise_for_status()
            claim_task = response.json()
            if claim_task['completed']:
                return self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Claimed {task_points} From {task_name} ]{Style.RESET_ALL}"
                )
        except RequestException as e:
            if e.response.status_code == 400:
                error_claim_task = response.json()
                if error_claim_task['message'] == f'Task with ID {task_id} cannot be claimed because it is not in a claimable state':
                    return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {task_name} Cannot Be Claimed Because It Is Not In A Claimable State ]{Style.RESET_ALL}")
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An HTTP Error Occurred While Claim Tasks: {str(e.response.reason)} ]{Style.RESET_ALL}")
        except (Exception, JSONDecodeError) as e:
            return self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ An Unexpected Error Occurred While Claim Tasks: {str(e)} ]{Style.RESET_ALL}")

    def main(self, queries: str):
        while True:
            try:
                tokens = self.register(queries=queries)
                total_points = 0

                for token in tokens:
                    self.user_visited(token=token)
                    user = self.user(token=token)
                    if user is None: continue
                    first_name = user['firstName'] if user else self.faker.first_name()

                    self.print_timestamp(
                        f"{Fore.CYAN + Style.BRIGHT}[ {first_name} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.GREEN + Style.BRIGHT}[ Points {user['points']} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE + Style.BRIGHT}[ Tickets {user['tickets']} ]{Style.RESET_ALL}"
                    )

                    self.get_streak(token=token, first_name=first_name)
                    self.claim_referral(token=token, first_name=first_name)

                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Play Tickets ]{Style.RESET_ALL}")
                for token in tokens:
                    user = self.user(token=token)
                    if user is None: continue
                    first_name = user['firstName'] if user else self.faker.first_name()
                    self.play(token=token, first_name=first_name)

                self.print_timestamp(f"{Fore.WHITE + Style.BRIGHT}[ Tasks ]{Style.RESET_ALL}")
                for token in tokens:
                    user = self.user(token=token)
                    if user is None: continue
                    total_points += user['points'] if user else 0
                    first_name = user['firstName'] if user else self.faker.first_name()
                    self.available_tasks(token=token, first_name=first_name)

                self.print_timestamp(
                    f"{Fore.CYAN + Style.BRIGHT}[ Total Account {len(tokens)} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.GREEN + Style.BRIGHT}[ Total Points {total_points} ]{Style.RESET_ALL}"
                )

                sleep_timestamp = datetime.now().astimezone() + timedelta(seconds=900)
                timestamp_sleep_time = sleep_timestamp.strftime('%X %Z')
                self.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Restarting At {timestamp_sleep_time} ]{Style.RESET_ALL}")

                sleep(900)
                self.clear_terminal()
            except Exception as e:
                self.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
                continue

if __name__ == '__main__':
    try:
        init(autoreset=True)
        midas = Midas()

        queries_files = [f for f in os.listdir() if f.startswith('queries-') and f.endswith('.txt')]
        queries_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)

        midas.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 1 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Split Queries ]{Style.RESET_ALL}"
        )
        midas.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 2 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Use Existing 'queries-*.txt' ]{Style.RESET_ALL}"
        )
        midas.print_timestamp(
            f"{Fore.MAGENTA + Style.BRIGHT}[ 3 ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.CYAN + Style.BRIGHT}[ Use 'queries.txt' Without Splitting ]{Style.RESET_ALL}"
        )

        initial_choice = int(input(
            f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.YELLOW + Style.BRIGHT}[ Select An Option ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
        ))
        if initial_choice == 1:
            accounts = int(input(
                f"{Fore.YELLOW + Style.BRIGHT}[ How Much Account That You Want To Process Each Terminal ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            ))
            midas.print_timestamp(f"{Fore.CYAN + Style.BRIGHT}[ Processing Queries To Generate Files ]{Style.RESET_ALL}")
            midas.process_queries(lines_per_file=accounts)

            queries_files = [f for f in os.listdir() if f.startswith('queries-') and f.endswith('.txt')]
            queries_files.sort(key=lambda x: int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0)

            if not queries_files:
                raise FileNotFoundError("No 'queries-*.txt' Files Found")
        elif initial_choice == 2:
            if not queries_files:
                raise FileNotFoundError("No 'queries-*.txt' Files Found")
        elif initial_choice == 3:
            queries = [line.strip() for line in open('queries.txt') if line.strip()]
        else:
            raise ValueError("Invalid Choice. Please Run The Script Again And Choose A Valid Option")

        if initial_choice in [1, 2]:
            midas.print_timestamp(f"{Fore.MAGENTA + Style.BRIGHT}[ Select The Queries File To Use ]{Style.RESET_ALL}")
            for i, queries_file in enumerate(queries_files, start=1):
                midas.print_timestamp(
                    f"{Fore.MAGENTA + Style.BRIGHT}[ {i} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT}[ {queries_file} ]{Style.RESET_ALL}"
                )

            choice = int(input(
                f"{Fore.BLUE + Style.BRIGHT}[ {datetime.now().astimezone().strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT}[ Select 'queries-*.txt' File ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            )) - 1
            if choice < 0 or choice >= len(queries_files):
                raise ValueError("Invalid Choice. Please Run The Script Again And Choose A Valid Option")

            selected_file = queries_files[choice]
            queries = midas.load_queries(selected_file)

        midas.main(queries=queries)
    except (ValueError, IndexError, FileNotFoundError) as e:
        midas.print_timestamp(f"{Fore.RED + Style.BRIGHT}[ {str(e)} ]{Style.RESET_ALL}")
    except KeyboardInterrupt:
        sys.exit(0)
