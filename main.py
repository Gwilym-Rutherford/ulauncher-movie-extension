from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

import logging
import requests
import json
import urllib.parse
import subprocess


logger = logging.getLogger(__name__)

class MovieExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventHandler())
        
    
    def qualitySelection(data, movieName):
        items = []
        logger.debug(data)
        MovieExtension.movieName = movieName
        for info in data:
            info = dict(info)
            items.append(ExtensionResultItem(
                icon='images/menu.png',
                name=f"quality: {info["quality"]}",
                description=f"type: {info["type"]} \t size: {info["size"]}",
                on_enter=ExtensionCustomAction(
                    {"function": "streamSelection",
                     "data": info}, keep_app_open=True))
            )
            
        return items
    
    def streamSelection(data, preferences):
        text = ["Stream", "Download", "Close"]
        description = ["Stream movie right now, save to:", "Download movie to:", "Close"]
        items = []
        for i in range(0, len(text)):
            if text[i] == "Close":
                items.append(ExtensionResultItem(
                    icon='images/menu.png',
                    name=text[i],
                    description=description[i],
                    on_enter=HideWindowAction())   
                )
            else:
                if text[i] == "Download":
                    obj = {"function": "download", "data": data}
                else:
                    obj = {"function": "stream", "data": data}
                    
                items.append(ExtensionResultItem(
                    icon='images/menu.png',
                    name=text[i],
                    description=f"{description[i]} {preferences["download_path"]}",
                    on_enter=ExtensionCustomAction(obj, keep_app_open=False))
                )
            
        return items
    
    def build_magnet_uri(data, preferences):
        magnet_uri = "magnet:?xt=urn:btih:"
        magnet_uri += data["hash"]
        magnet_uri += "&dn="
        magnet_uri += urllib.parse.quote(MovieExtension.movieName)
        
        trackers = preferences["trackers"].replace(",", "&tr=")
        magnet_uri += f"&tr={trackers}"
        
        return magnet_uri 
    

    def download(data, preferences):
        magnet_uri = MovieExtension.build_magnet_uri(data, preferences)
        subprocess.run(
            f"webtorrent download '{magnet_uri}' --quiet --out '{preferences["download_path"]}'"
            , shell=True
        )
        
    def stream(data, preferences):
        logger.debug(f"Data info: {data}")
        logger.debug(f"Movie name: {MovieExtension.movieName}")
        
        magnet_uri = MovieExtension.build_magnet_uri(data, preferences)
        subprocess.run(
            f"webtorrent '{magnet_uri}' --quiet --vlc --out '{preferences["download_path"]}'",
            shell=True)


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
        if preferences["mullvad"]:
            subprocess.run(f"mullvad connect --wait", shell=True)
                    
        
        response = json.loads(requests.get(api_uri).text)["data"]
        all_movies = response["movies"]
            
        return all_movies


    def on_event(self, event, extension):
        
        api_uri = self.build_api_uri(event.get_argument(), extension.preferences)
        all_movies = self.get_movies(api_uri, extension.preferences)
        
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


class ItemEnterEventHandler(EventListener):
    
    def on_event(self, event, extension):
        
        data = event.get_data()
        
        logger.debug(data)
        
        if data["function"] == "quality":
            items = MovieExtension.qualitySelection(data["data"], data["movieName"])
        elif data["function"] == "streamSelection":
            items = MovieExtension.streamSelection(data["data"], extension.preferences)
        elif data["function"] == "download":
            MovieExtension.download(data["data"], extension.preferences)
            return ExtensionCustomAction(data={}, keep_app_open=False)
        elif data["function"] == "stream":
            MovieExtension.stream(data["data"], extension.preferences)
            return ExtensionCustomAction(data={}, keep_app_open=False)
        else:
            items = (ExtensionResultItem(
                        icon='images/menu.png',
                        name="Seems to be an error",
                        description="You can try restaring",
                        on_enter=HideWindowAction())
                     )
        
        return RenderResultListAction(items)
    
        
if __name__ == '__main__':
    MovieExtension().run()