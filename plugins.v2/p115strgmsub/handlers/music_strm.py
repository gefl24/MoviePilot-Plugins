"""
音乐 STRM 生成模块
负责扫描 115 网盘音乐目录并生成本地 STRM 文件
"""
import os
import urllib.parse
from typing import List, Optional
from app.log import logger

class MusicStrmHandler:
    # 支持的音乐格式
    MUSIC_EXTS = {'.mp3', '.flac', '.wav', '.m4a', '.aac', '.ogg', '.dsf', '.dff', '.ape', '.wma', '.alac'}

    def __init__(self, p115_manager, p115_root_path: str, local_save_path: str, url_prefix: str):
        """
        :param p115_manager: 115 客户端管理器实例
        :param p115_root_path: 115网盘中的音乐根目录 (如 /我的接收/Music)
        :param local_save_path: 本地保存 STRM 的根目录 (如 /mnt/user/music_strm)
        :param url_prefix: 播放链接前缀 (如 http://192.168.1.5:5244/d/115)
        """
        self._p115 = p115_manager
        self._p115_root = p115_root_path
        self._local_root = local_save_path
        self._url_prefix = url_prefix.rstrip('/')

    def run(self):
        """执行生成任务"""
        if not self._p115 or not self._p115.client:
            logger.error("115 客户端未初始化，无法生成 STRM")
            return

        logger.info(f"开始扫描 115 音乐目录: {self._p115_root}")
        
        # 获取根目录 CID
        root_cid = self._p115.get_pid_by_path(self._p115_root, mkdir=False)
        if root_cid == -1:
            logger.error(f"115 路径不存在: {self._p115_root}")
            return

        # 开始递归处理
        self._process_directory(root_cid, self._p115_root)
        logger.info("音乐 STRM 生成任务完成")

    def _process_directory(self, cid: int, current_115_path: str):
        """递归处理目录"""
        try:
            # 使用 p115.py 中封装的 list_files，或者直接调 API 以获取更多信息
            # 这里直接调用 fs_files 获取 file_id 和 name
            # 注意：p115.py 的 list_files 可能只返回第一页，这里建议使用 p115client 原生的遍历功能
            
            # 由于 p115.py 没有封装递归遍历"我的文件"的功能，我们这里手动实现简单的分页获取
            offset = 0
            limit = 1000
            
            while True:
                resp = self._p115.client.fs_files({"cid": cid, "offset": offset, "limit": limit})
                if not resp.get("state"):
                    logger.error(f"获取文件列表失败: {current_115_path}")
                    break
                
                data = resp.get("data", [])
                if not data:
                    break

                for item in data:
                    file_name = item.get("n", "")
                    file_id = item.get("fid") # 文件ID，目录则不需要
                    cid_id = item.get("cid")  # 目录ID
                    
                    # 115 API 中 fid 为 undefined 或 0 时通常是目录（取决于具体API），或者有 cid 字段
                    # 更准确是用 'fid' 字段存在且不为0来判断是文件
                    
                    is_dir = False
                    if "fid" in item and item["fid"]:
                        is_dir = False
                    else:
                        is_dir = True

                    # 相对路径 (用于本地目录结构)
                    # 移除 115 根路径前缀，得到相对路径
                    rel_path = current_115_path.replace(self._p115_root, "").lstrip("/")
                    
                    if is_dir:
                        # 递归处理子目录
                        sub_path = f"{current_115_path}/{file_name}"
                        self._process_directory(cid_id, sub_path)
                    else:
                        # 处理文件
                        ext = os.path.splitext(file_name)[1].lower()
                        if ext in self.MUSIC_EXTS:
                            self._generate_strm(file_name, rel_path, current_115_path)

                offset += limit
                if len(data) < limit:
                    break

        except Exception as e:
            logger.error(f"扫描目录出错 {current_115_path}: {e}")

    def _generate_strm(self, file_name: str, relative_path: str, full_115_path: str):
        """生成单个 STRM 文件"""
        try:
            # 本地保存路径
            local_dir = os.path.join(self._local_root, relative_path)
            if not os.path.exists(local_dir):
                os.makedirs(local_dir, exist_ok=True)
            
            strm_file = os.path.join(local_dir, file_name + ".strm")
            
            # 构造播放链接
            # 方式1: 使用 Alist / WebDAV 挂载路径 (最常用，推荐)
            # 假设 full_115_path 是 /我的接收/Music/Song.mp3
            # url_prefix 是 http://alist:5244/d/115
            # 最终 URL: http://alist:5244/d/115/我的接收/Music/Song.mp3
            
            # 对路径进行 URL 编码
            encoded_path = urllib.parse.quote(full_115_path)
            # 处理路径拼接，确保斜杠正确
            final_url = f"{self._url_prefix}{encoded_path}"
            
            # 写入文件
            with open(strm_file, "w", encoding="utf-8") as f:
                f.write(final_url)
                
            # logger.debug(f"生成 STRM: {strm_file}")
            
        except Exception as e:
            logger.error(f"生成 STRM 失败 {file_name}: {e}")
