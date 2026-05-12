import sys
import os
import subprocess
import logging
import re

import src.core.helper as helper

conf = {
    "gh_path" : helper.get_resource_path("bin\\gh.exe"),
    "git_path" : "git",
}
logger = logging.getLogger()

def set_logger(arg_logger):
    global logger
    logger = arg_logger
    helper.logger = logger

def process_submition():
    raise(NotImplementedError)

def github_login_new_term():
    """Open terminal and run gh auth login"""
    try:
        # Determine the terminal command based on OS
        if sys.platform == "win32":
            # Windows: Use cmd or PowerShell
            if os.path.exists(os.environ.get('SystemRoot', '') + '\\System32\\WindowsPowerShell\\v1.0\\powershell.exe'):
                terminal_cmd = ['powershell', '-NoExit', '-Command', f'{conf["gh_path"]} auth login']
            else:
                terminal_cmd = ['cmd', '/k', f'{conf["gh_path"]} auth login']
        elif sys.platform == "darwin":
            # macOS: Use Terminal
            terminal_cmd = ['open', '-a', 'Terminal', '--args', 'bash', '-c', f'{conf["gh_path"]} auth login; exec bash']
        else:
            # Linux: Try common terminals
            terminals = ['gnome-terminal', 'xterm', 'konsole', 'xfce4-terminal']
            terminal_cmd = None
            for term in terminals:
                if os.system(f'which {term} > /dev/null 2>&1') == 0:
                    if term == 'gnome-terminal':
                        terminal_cmd = [term, '--', 'bash', '-c', f'{conf["gh_path"]} auth login; exec bash']
                    else:
                        terminal_cmd = [term, '-e', 'bash -c f"{conf["gh_path"]} auth login; exec bash"']
                    break
            
            if terminal_cmd is None:
                messagebox.showerror(
                    "Error",
                    f"No supported terminal found.\nPlease run '{conf["gh_path"]} auth login' manually."
                )
                return
        
        # Launch terminal
        if terminal_cmd:
            subprocess.Popen(terminal_cmd)

    except Exception as e:
        return 1
    
def get_username():
    result = subprocess.run([conf["git_path"], "config", "user.name"], capture_output=True)

    username = result.stdout.strip().decode().replace(' ', '')

    if result.returncode != 0 or len(username) == 0:
        logger.info("failed to get username, ensure git is installed and github is logged in")
        return None

    return username

def clone(repo, branch):
    logger.debug(f"called via {repo=}, {branch=}")
    cmd = [conf['gh_path'], "repo", "clone", repo, "--", "--branch", branch, "--progress", "--single-branch"]

    err = helper.subprocess_popen_poll(
        cmd,
        logger.info
        )

    if err != 0:
        logger.error(f"error cloning")
    return err

def run_workflow(repo, workflow, inputs):
    cmd = [conf['gh_path'], "workflow", "run", workflow, "-R", repo]
    id_from_output_regex = r'/runs/(\d+)'
    for input in inputs:
        cmd.append("-f")
        cmd.append(input)
    logger.info(f"running workflow for {inputs}")
    result = subprocess.run(
        cmd,
        capture_output=True
    )
    if result.returncode != 0:
        logger.error(f"error running workflow: {workflow} for repo {repo}")
        return None

    id = re.search(id_from_output_regex, result.stdout.decode()).group(1)
    logger.info(f"workflow started with id: {id}")

    return id

def _decode_list_workflow_runs_line(line : str):
    """
    ✓       01-🎬YoutubeDownloader  01-🎬YoutubeDownloader  main    workflow_dispatch  25813566250  1m47s    less than a minute ago
    """

    logger.debug(f"decoding {line}")

    line = line.replace('  ', ' ')
    fields = line.split()

    return {
        "is_completed"  : True if fields[0] == "completed" else False,
        "success"  : True if fields[1] == "success" else False,
        "title"   : fields[2],
        "workflow": fields[3],
        "branch"  : fields[4],
        "event"   : fields[5],
        "id"      : fields[6],
        "elapsed" : fields[7],
    }

def delete_workflow_run_log(repo, id):
    cmd = [conf["gh_path"], "api", "-X", "DELETE", f"repos/{repo}/actions/runs/{id}"]
    err = helper.subprocess_popen_poll(cmd, logger.info)
    if err != 0:
        logger.error(f"failed to delete workflow run: {id}")
    return err

def list_workflow_runs(repo):
    """
    STATUS  TITLE                      WORKFLOW                   BRANCH  EVENT              ID           ELAPSED  AGE                   
    ✓       01- 🎬 Youtube Downloader  01- 🎬 Youtube Downloader  main    workflow_dispatch  25813566250  1m47s    less than a minute ago
    """
    logger.info("listing workflows")
    cmd = [conf["gh_path"], "run", "list", "-R", repo]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        logger.error("failed to list workflow runs")
        return result.returncode

    result_raw = result.stdout\
                .decode()\
                .splitlines()[0:] # skip the header
    
    return [ _decode_list_workflow_runs_line(line) for line in result_raw]

def clear_workflow_runs_log(repo):
    logs = list_workflow_runs(repo)
    logger.info("clearing workflow history")
    for log in logs:
        err = delete_workflow_run_log(repo, log["id"])
        if err != 0:
            logger.error(f"failed to delete workflow run {id}")

def list_branches(repo):
    cmd = [conf["gh_path"], 'api', f'repos/{repo}/branches' ,'--jq', '.[].name']
    logger.info("listing branches")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        logger.info("failed to list branches")
        return None
    return result.stdout.decode().splitlines()

def delete_branch(repo, branch_name):
    cmd = [conf["gh_path"], "api", "-X", "DELETE", f"/repos/{repo}/git/refs/heads/{branch_name}"]
    logger.info(f"deleteing branch {branch_name}")
    return helper.subprocess_popen_poll(cmd, logger.info)

def setup_git():
    cmd = [conf["gh_path"], "auth", "setup-git"]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        logger.error("error setting up git")

    return result.returncode