"""
处理器模块
包含搜索、同步、订阅、API、音乐生成等处理逻辑
"""
from .search import SearchHandler
from .sync import SyncHandler
from .subscribe import SubscribeHandler
from .api import ApiHandler
# [新增]
from .music_strm import MusicStrmHandler

__all__ = [
    "SearchHandler",
    "SyncHandler",
    "SubscribeHandler",
    "ApiHandler",
    "MusicStrmHandler" # [新增]
]
