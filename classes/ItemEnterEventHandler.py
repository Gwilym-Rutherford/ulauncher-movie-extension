from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.HideWindowAction import HideWindowAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

import logging
import urllib.parse
import subprocess

logger = logging.getLogger(__name__)


class ItemEnterEventHandler(EventListener):
    
    def qualitySelection(self, data, movieName):
        items = []
        logger.debug(data)
        self.movieName = movieName
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
    
    def streamSelection(self, data, preferences):
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
    
    def build_magnet_uri(self, data, preferences):
        magnet_uri = "magnet:?xt=urn:btih:"
        magnet_uri += data["hash"]
        magnet_uri += "&dn="
        magnet_uri += urllib.parse.quote(self.movieName)
        
        trackers = preferences["trackers"].replace(",", "&tr=")
        magnet_uri += f"&tr={trackers}"
        
        return magnet_uri 
    

    def download(self, data, preferences):
        magnet_uri = self.build_magnet_uri(data, preferences)
        subprocess.run(
            f"webtorrent download '{magnet_uri}' --quiet --out '{preferences["download_path"]}'"
            , shell=True
        )
        
    def stream(self, data, preferences):
        logger.debug(f"Data info: {data}")
        logger.debug(f"Movie name: {self.movieName}")
        
        magnet_uri = self.build_magnet_uri(data, preferences)
        subprocess.run(
            f"webtorrent '{magnet_uri}' --quiet --vlc --out '{preferences["download_path"]}'",
            shell=True)
    
    def on_event(self, event, extension):
        
        data = event.get_data()
        
        logger.debug(data)
        
        if data["function"] == "quality":
            items = self.qualitySelection(data["data"], data["movieName"])
        elif data["function"] == "streamSelection":
            items = self.streamSelection(data["data"], extension.preferences)
        elif data["function"] == "download":
            self.download(data["data"], extension.preferences)
            return ExtensionCustomAction(data={}, keep_app_open=False)
        elif data["function"] == "stream":
            self.stream(data["data"], extension.preferences)
            return ExtensionCustomAction(data={}, keep_app_open=False)
        else:
            items = (ExtensionResultItem(
                        icon='images/menu.png',
                        name="Seems to be an error",
                        description="You can try restaring",
                        on_enter=HideWindowAction())
                     )
        
        return RenderResultListAction(items)
    