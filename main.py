import os
import json
from urllib import parse
from ghapi.all import *
from fastcore.utils import *
from urllib.parse import urlparse
from os import path
import subprocess
import time


def check_flag():
    if path.exists(str(os.environ.get('RUNNER_HOME')) + "/" + str(os.environ.get('KILL_FILE'))):
        return True
    else:
        return False


def parse_runner_org_and_repo(runner):
    parsed = urlparse(runner['gitHubUrl'])
    org = os.path.split(parsed.path)[0].strip("/")
    repo = os.path.split(parsed.path)[1]
    return org, repo


def check_if_busy(api, runner):
    org, repo = parse_runner_org_and_repo(runner)
    this = api.actions.get_self_hosted_runner_for_repo(
        org, repo, runner['agentId'])
    return this.busy


def demote(user_uid, user_gid):
    def set_ids():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return set_ids


def run_as_user(cmd, cwd, uid, gid):
    return subprocess.check_output(cmd, preexec_fn=demote(uid, gid), cwd=cwd)


def get_remove_token(api, runner):
    org, repo = parse_runner_org_and_repo(runner)
    token = api.actions.create_remove_token_for_repo(org, repo)
    return token


def gracefully_terminate(api, runner, home_dir):
    if not check_if_busy(api, runner):
        subprocess.Popen(['./svc.sh', 'stop'], shell=False, cwd=home_dir)
        subprocess.Popen(['./svc.sh', 'uninstall'], shell=False, cwd=home_dir)
        time.sleep(5)
        token = get_remove_token(api, runner)
        run_as_user(['./config.sh', 'remove', '--unattended', '--name', runner['agentName'],
                    '--url', runner['gitHubUrl'], '--token', str(token.token)], home_dir, 1001, 1001)
        print("Runner " + str(runner['agentId']) +
              " on " + str(runner['gitHubUrl'] + " removed."))
        return True
    else:
        print("Runner " + str(runner['agentId']) +
              " on " + str(runner['gitHubUrl'] + " is busy."))
        return False


def main():
    while True:
        if check_flag():
            print("Found kill file, starting recycle.")
            api = GhApi()
            runners = str(os.environ.get('RUNNERS_HOMES')).split(",")
            for home_dir in runners:
                if os.path.exists(home_dir + "/.runner"):
                    with open(home_dir + "/.runner", encoding='utf-8-sig') as f:
                        runner = json.load(f)
                        if check_if_busy(api, runner):
                            print(
                                "Runner " + str(runner['agentId']) + " on " + str(runner['gitHubUrl'] + " is busy."))
                        else:
                            if gracefully_terminate(api, runner, home_dir):
                                print(
                                    "Runner " + str(runner['agentId']) + " on " + str(runner['gitHubUrl'] + " terminated."))
                                runners.remove(home_dir)
                            else:
                                print(
                                    "Runner " + str(runner['agentId']) + " on " + str(runner['gitHubUrl'] + " not terminated."))
                else:
                    print("No .runner file, runner was likely previously removed.")
                    runners.remove(home_dir)
            time.sleep(60)
        else:
            print("Kill file not found, sleeping.")
            time.sleep(60)


if __name__ == '__main__':
    main()
