import json
import os
import sys
from time import sleep

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


class GithubApi:
    base = "https://api.github.com/"

    def __init__(self, username, token):
        self.username = username
        self.token = token

    def call(self, endpoint):
        resp = requests.get(
            self.base + endpoint.lstrip("/"), auth=(self.username, self.token)
        )
        return resp.json()

    def get_user_info(self, username, cached=True):
        if cached:
            with open("user.json", "r") as fi:
                return json.load(fi)
        user = self.call(f"users/{username}")
        # with open("user.json", "w") as fo:
        #     json.dump(user, fo, indent=4)
        return user

    def get_user_repos(self, username, cached=True):
        if cached:
            with open("repos.json", "r") as fi:
                return json.load(fi)
        repos = self.call(f"users/{username}/repos")
        # with open("repos.json", "w") as fo:
        #     json.dump(repos, fo, indent=4)
        return repos

    def get_user_overview(self, username):
        user = self.get_user_info(username)
        keys = [
            "name",
            "company",
            "public_repos",
            "followers",
            "created_at",
            "bio",
            "location",
            "email",
            "html_url",
            "public_gists",
        ]
        return {key: user[key] for key in keys}

    def get_repos_overview(self, username):
        keys = ["name", "html_url", "updated_at", "watchers"]
        repos = self.get_user_repos(username)
        items = []
        for repo in repos:
            items.append({key: repo[key] for key in keys})
        return sorted(items, key=lambda x: x["updated_at"], reverse=True)


def list_to_table(items):
    first = next(iter(items), None)
    if not first:
        return Table()
    table = Table(*first.keys(), expand=True)
    for row in items:
        table.add_row(*[str(v) for v in row.values()])
    return table


def dict_to_table(dct):
    table = Table("key", "value", expand=True)
    for k, v in dct.items():
        table.add_row(k, str(v))
    return table


class StateUpdater:
    def __init__(self, api, username):
        self.api = api
        self.username = username
        self.side_bottom_content_numbers = self.side_bottom_content_gen()

    def side_bottom_content(self):
        return next(self.side_bottom_content_numbers)

    @staticmethod
    def side_bottom_content_gen():
        number = 0
        while True:
            number += 1
            yield Panel(f"The current [b]number[/b] is {number}")

    def body_content(self):
        return list_to_table(self.api.get_repos_overview(self.username))

    def side_top_content(self):
        return dict_to_table(api.get_user_overview(username))


def main(api, username):
    console = Console()
    dashboard = Layout()
    state_updater = StateUpdater(api, username)

    # Divide the "screen" in to three parts
    dashboard.split(
        Layout(
            name="header", size=3, renderable=Panel(f"Github overview for {username}")
        ),
        Layout(ratio=1, name="main"),
        Layout(size=10, name="footer"),
    )

    # Divide the "main" layout in to "side" and "body"
    dashboard["main"].split_row(
        Layout(name="side"),
        Layout(name="body", ratio=2),
    )
    # Divide the "side" layout in to two
    dashboard["side"].split_column(
        Layout(name="side-top", renderable=Panel("The number is not set")),
        Layout(name="side-bottom"),
    )

    side_bottom = dashboard["side"]["side-bottom"]
    body = dashboard["body"]
    side_top = dashboard["side"]["side-top"]

    console.print(dashboard)
    with Live(dashboard, screen=True, vertical_overflow="visible"):
        while True:
            side_bottom.update(state_updater.side_bottom_content())
            body.update(state_updater.body_content())
            side_top.update(state_updater.side_top_content())

            sleep(3)


if __name__ == "__main__":
    username = sys.argv[1]
    load_dotenv()
    gh_username = os.getenv("GH_USERNAME")
    gh_token = os.getenv("GH_TOKEN")
    api = GithubApi(gh_username, gh_token)
    main(api, username)
