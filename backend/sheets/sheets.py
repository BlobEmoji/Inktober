import datetime
import logging
import os.path
import pickle

import discord
import googleapiclient.discovery
import googleapiclient.http
from discord.ext import commands, tasks
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import backend.config
import backend.day_themes
from bot import Bot as Client

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
BLOB_EMOJI_SPREADSHEET_ID = '1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs'
log = logging.getLogger(__name__)


class Sheets(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot
        self.channel_description.start()

    def cog_unload(self):
        self.channel_description.cancel()

    @tasks.loop(hours=1)
    async def channel_description(self):
        now_day = int(datetime.datetime.now().strftime("%d"))
        channel: discord.TextChannel = self.bot.get_channel(backend.config.inktober_submit_channel)
        await channel.edit(reason="Time passed", topic=f"Currently accepting "
        f"{now_day - 1}: {backend.day_themes.day_themes[now_day - 1]},"
        f"{now_day}: {backend.day_themes.day_themes[now_day]},"
        f"{now_day + 1}: {backend.day_themes.day_themes[now_day + 1]}")


def setup(bot):
    bot.add_cog(Sheets(bot))


def credential_getter():
    credentials = None
    if os.path.exists('backend/sheets/token.pickle'):
        with open('backend/sheets/token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'backend/sheets/credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('backend/sheets/token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
    return credentials


def fetch_users():
    credentials = credential_getter()
    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().get(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range="👀!A5:A200")
    response = request.execute()

    if "values" not in response:
        return []

    users = []
    for row in response["values"]:
        users.append(row[0])
    return users


def fetch_user_days(user_id, data_list: list):
    log.info("Fetching User Days")
    cell = 4 + data_list.index(user_id) + 1

    credentials = credential_getter()
    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().get(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range=f"👀!D{cell}")
    response = request.execute()

    log.info(response)

    if "values" not in response:
        return []

    users = []
    for row in response["values"]:
        users.append(row[0])
    return users


def insert_user_days(user_id, data_list: list, day: int, user_tag: str):
    log.info("Inserting User Days")
    log.info(data_list)
    cell = 4 + len(data_list) + 1

    credentials = credential_getter()
    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().update(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range=f"👀!D{cell}",
        valueInputOption="RAW",
        body={
            "values": [
                [
                    day
                ]
            ]
        }
    )
    response = request.execute()

    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().update(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range=f"👀!C{cell}",
        valueInputOption="RAW",
        body={
            "values": [
                [
                    user_tag
                ]
            ]
        }
    )
    response = request.execute()

    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().update(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range=f"👀!A{cell}",
        valueInputOption="RAW",
        body={
            "values": [
                [
                    str(user_id)
                ]
            ]
        }
    )
    response = request.execute()


def say_that_roles_added(user_id, data_list: list):
    log.info(f"Adding 'Added' for {user_id}")
    cell = 4 + data_list.index(user_id) + 1

    credentials = credential_getter()
    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().update(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range=f"👀!E{cell}",
        valueInputOption="RAW",
        body={
            "values": [
                [
                    "Added"
                ]
            ]
        }
    )
    response = request.execute()


async def update_days(user_id, data_list: list, new_day, old_days: list, bot):
    log.info("Updating days, {}, {}, {}".format(user_id, new_day, old_days))
    cell = 4 + data_list.index(user_id) + 1

    if str(new_day) in old_days[0].split(" "):
        log.warning(f"{user_id} tried to submit another post for {new_day}")
        channel = bot.get_channel(backend.config.bot_spam_channel)
        await channel.send("{} tried to submit another post for {}".format(user_id, new_day))
        return

    old_days.append(new_day)
    new_list = old_days[0].split(" ")
    new_list.append(new_day)
    new_list.sort()

    credentials = credential_getter()
    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().update(
        spreadsheetId=BLOB_EMOJI_SPREADSHEET_ID,
        range=f"👀!D{cell}",
        valueInputOption="RAW",
        body={
            "values": [
                [
                    " ".join(new_list)
                ]
            ]
        }
    )
    response = request.execute()

    if "values" not in response:
        return []

    users = []
    for row in response["values"]:
        users.append(row[0])
    return users
