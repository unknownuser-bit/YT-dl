import src.core.gh as gh
import logging
import shutil
import re

conf = {
    "downloader_repo_name" : "YT-dl",
}

def yt_dlp_download(entry):
    username = gh.get_username()
    downloader_repo = f'{username}/{conf["downloader_repo_name"]}'
    inputs = [
        f"youtube_url={entry["url"]}",
        f"save_in_new_branch=true",
        f"quality={entry["param"] if entry["param"] else "best"}",
        f"split_threshold_mb=99"
    ]
    gh.run_workflow(downloader_repo, "01_Youtube_Downloader", inputs)

def log_error(entry):
    logger.error("please select a command")

dispatch_table = {
    "yt-dlp (youtube,...)" : yt_dlp_download,
    "Select..." : log_error
}

logger = logging.getLogger()

cleanup_resources = {
    'files' : []
}


def set_logger(arg_logger):
    global logger
    logger = arg_logger
    gh.set_logger(arg_logger)

def cleanup():
    for file in cleanup_resources["files"]:
        shutil.rmtree(file)

def submit_operation(submition):
    logger.debug(submition)

    for entry in submition:
        dispatch_table[entry["dropdown"]](entry)

    logger.info("done")

def github_login():
    while True:
        err = gh.github_login_new_term()
        if err != 0:
            logger.error("failed to login")
            break
        err = gh.setup_git()
        if err != 0:
            logger.error("setup git")
            break
        user = gh.get_username()
        if user is None:
            logger.error("failed to get user")
            err = 1
            break
    logger.info("done")

def clear_download_history():
    username = gh.get_username()
    repo = f'{username}/{conf["downloader_repo_name"]}'
    repo_name_regex = r'(\d{4})\.(\d{2})\.(\d{2})\.(\d{2})\.(\d{2})_([a-f0-9]{40})'

    if username == '':
        logger.info("done")
        return 1

    logger.info("clearing download history")

    for run in gh.list_workflow_runs(repo):
        gh.delete_workflow_run_log(repo, run["id"])
    for branch in gh.list_branches(repo):
        if re.match(repo_name_regex, branch):
            gh.delete_branch(repo, branch)

    logger.info("done")
    return 0