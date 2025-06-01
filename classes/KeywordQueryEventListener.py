from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

import logging
import requests
import json
import urllib.parse
import subprocess

logger = logging.getLogger(__name__)

class KeywordQueryEventListener(EventListener):

    def build_api_uri(self, movie_name, preferences):
        api_uri = ""
        
        base_uri = "https://yts.mx/api/v2/list_movies.json"

        api_uri = f"{base_uri}?query_term={urllib.parse.quote(str(movie_name))}"
        
        if preferences["order_by"]:
            api_uri += f"&order_by={preferences["order_by"]}"
            
        if preferences["limit"]:
            api_uri += f"&limit={preferences["limit"]}"
            
                
        logger.debug(f"api uri: {api_uri}")

        return api_uri
    
    def get_movies(self, api_uri, preferences):
        # if selected, will connect to vpn before
        logger.debug(preferences)
        if preferences["mullvad"] == 'true':
            subprocess.run(f"mullvad connect --wait", shell=True)
                    
        
        
        try:
            response = json.loads(requests.get(api_uri).text)["data"]
            return response["movies"]
        except:
            logger.info("Movie wasn't found")
            return []


    def on_event(self, event, extension):
        
        api_uri = self.build_api_uri(event.get_argument(), extension.preferences)
        all_movies = self.get_movies(api_uri, extension.preferences)
        
        if len(all_movies) != 0:
            movies = dict()
            for movie in all_movies:
                movies[movie["title"]] = movie["torrents"]
                
            items = []
            keys = list(movies.keys())
            for movie in keys:
                items.append(ExtensionResultItem(
                    icon='images/icon.png',
                    name=str(movie),
                    description=f"{str(movie)} - {all_movies[0]["year"]}",
                    on_enter=ExtensionCustomAction(
                        {"function": "quality",
                        "data": movies[movie],
                        "movieName": str(movie)}, keep_app_open=True))
                )        

            return RenderResultListAction(items)
        
        else:
            return RenderResultListAction([ExtensionResultItem(
                icon='images/icon.png',
                    name="No file was found :(",
                    description="Make sure you are connected to vpn, and the spelling is correct",
                    on_enter=DoNothingAction())
                ])        
            