from ulauncher.api.client.Extension import Extension
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent

from .KeywordQueryEventListener import KeywordQueryEventListener
from .ItemEnterEventHandler import ItemEnterEventHandler

import logging

logger = logging.getLogger(__name__)


class MovieExtension(Extension):

    def __init__(self):
        super().__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventHandler())