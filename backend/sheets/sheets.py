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

import backend.day_themes
from bot import Bot as Client

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = '1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs'
SAMPLE_RANGE_NAME = 'Class Data!A2:E'

log = logging.getLogger(__name__)


class Sheets(commands.Cog):
    def __init__(self, bot):
        self.bot: Client = bot
        self.channel_description.start()

    @tasks.loop(hours=1)
    async def channel_description(self):
        now_day = int(datetime.datetime.now().strftime("%d"))
        channel: discord.TextChannel = self.bot.get_channel(628013530888667157)
        await channel.edit(reason="Time passed", topic={f"Currently accepting "
                                                        f"{now_day - 1}: {backend.day_themes.day_themes[now_day - 1]},"
                                                        f"{now_day}: {backend.day_themes.day_themes[now_day]},"
                                                        f"{now_day + 1}: {backend.day_themes.day_themes[now_day + 1]}"})
        channel: discord.TextChannel = self.bot.get_channel(628013545946218536)
        await channel.edit(reason="Time passed", topic={f"Currently accepting "
                                                        f"{now_day - 1}: {backend.day_themes.day_themes[now_day - 1]},"
                                                        f"{now_day}: {backend.day_themes.day_themes[now_day]},"
                                                        f"{now_day + 1}: {backend.day_themes.day_themes[now_day + 1]}"})


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
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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
        channel = bot.get_channel(411929226066001930)
        await channel.send("{} tried to submit another post for {}".format(user_id, new_day))
        return

    old_days.append(new_day)
    new_list = old_days[0].split(" ")
    new_list.append(new_day)
    new_list.sort()

    credentials = credential_getter()
    service = build('sheets', 'v4', credentials=credentials)
    request: googleapiclient.http.HttpRequest = service.spreadsheets().values().update(
        spreadsheetId="1IIpC8dAYlpiOGMLlbwTKk03eZT8oTkou0GUCw-cTjhs",
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


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID,
                                range=SAMPLE_RANGE_NAME).execute()
    values = result.get('values', [])

    if not values:
        print('No data found.')
    else:
        print('Name, Major:')
        for row in values:
            # Print columns A and E, which correspond to indices 0 and 4.
            print('%s, %s' % (row[0], row[4]))
