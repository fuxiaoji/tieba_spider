"""
贴吧帖子爬虫核心模块
使用贴吧客户端API（无需登录）爬取帖子内容
"""

import hashlib
import urllib.request
import urllib.parse
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path


CLIENT_VERSION = "9.7.8.0"
CLIENT_ID = "wappc_1534235498291_633"
CLIENT_TYPE = "2"
PHONE_IMEI = "000000000000000"
USER_AGENT = f"bdtb for Android {CLIENT_VERSION}"
API_BASE = "http://c.tieba.baidu.com"


def sign(params: dict) -> str:
    """生成贴吧API请求签名"""
    keys = sorted(params.keys())
    s = "".join(k + "=" + str(params[k]) for k in keys) + "tiebaclient!!!"
    return hashlib.md5(s.encode("utf-8")).hexdigest().upper()


def api_request(endpoint: str, params: dict, timeout: int = 15) -> dict:
    """发起贴吧API请求"""
    base_params = {
        "_client_id": CLIENT_ID,
        "_client_type": CLIENT_TYPE,
        "_client_version": CLIENT_VERSION,
        "_phone_imei": PHONE_IMEI,
    }
    base_params.update(params)
    base_params["sign"] = sign(base_params)
    post_data = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in base_params.items())
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=post_data.encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def extract_tid(url: str) -> str:
    """从贴吧URL中提取帖子ID"""
    # 支持格式: https://tieba.baidu.com/p/7487460366?...
    match = re.search(r"/p/(\d+)", url)
    if match:
        return match.group(1)
    # 纯数字
    if url.strip().isdigit():
        return url.strip()
    raise ValueError(f"无法从URL中提取帖子ID: {url}")


def get_page(tid: str, page_num: int, rn: int = 30) -> dict:
    """获取帖子某一页的数据"""
    params = {
        "kz": tid,
        "pn": str(page_num),
        "rn": str(rn),
        "r": "0",
        "lz": "0",
        "st": "0",
        "z": "0",
    }
    return api_request("/c/f/pb/page", params)


def get_subposts(tid: str, pid: str, page_num: int = 1, rn: int = 20) -> list:
    """获取某楼的子回复（楼中楼）"""
    params = {
        "kz": tid,
        "pid": pid,
        "pn": str(page_num),
        "rn": str(rn),
    }
    data = api_request("/c/f/pb/floor", params)
    if data.get("error_code") == 0:
        return data.get("subpost_list", [])
    return []


def format_timestamp(ts: int) -> str:
    """将Unix时间戳格式化为可读时间"""
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def parse_content(content_list: list) -> tuple:
    """
    解析帖子内容，返回 (markdown文本, 图片URL列表)
    content type:
      0 = 文字
      1 = 链接
      2 = 表情
      3 = 图片
      4 = @用户
      9 = 视频
      10 = 话题
    """
    text_parts = []
    images = []

    for item in content_list:
        t = item.get("type", 0)
        if t == 0:
            # 普通文字
            text = item.get("text", "")
            text_parts.append(text)
        elif t == 1:
            # 链接
            link_text = item.get("text", "")
            link_url = item.get("link", "")
            if link_url:
                text_parts.append(f"[{link_text}]({link_url})")
            else:
                text_parts.append(link_text)
        elif t == 2:
            # 表情
            c = item.get("c", "")
            text_parts.append(f"[表情:{c}]")
        elif t == 3:
            # 图片
            # 优先使用 origin_src，其次 big_cdn_src，再次 cdn_src
            img_url = (
                item.get("origin_src")
                or item.get("big_cdn_src")
                or item.get("cdn_src")
                or ""
            )
            if img_url:
                images.append(img_url)
                # Markdown图片占位符，后续替换为本地路径
                text_parts.append(f"__IMG_{len(images) - 1}__")
        elif t == 4:
            # @用户
            text = item.get("text", "")
            text_parts.append(f"@{text}")
        elif t == 9:
            # 视频
            text_parts.append("[视频内容]")
        elif t == 10:
            # 话题
            text = item.get("text", "")
            text_parts.append(f"#{text}#")
        else:
            text = item.get("text", "")
            if text:
                text_parts.append(text)

    return "".join(text_parts), images


def download_image(url: str, save_dir: str, filename: str, callback=None) -> str:
    """下载图片到本地，返回本地路径（相对路径）"""
    os.makedirs(save_dir, exist_ok=True)
    # 获取文件扩展名
    ext = ".jpg"
    url_path = url.split("?")[0]
    if "." in url_path.split("/")[-1]:
        ext = "." + url_path.split("/")[-1].split(".")[-1]
        if len(ext) > 5:
            ext = ".jpg"

    local_filename = filename + ext
    local_path = os.path.join(save_dir, local_filename)

    if os.path.exists(local_path):
        return local_filename

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://tieba.baidu.com/",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            with open(local_path, "wb") as f:
                f.write(resp.read())
        if callback:
            callback(f"已下载图片: {local_filename}")
        return local_filename
    except Exception as e:
        if callback:
            callback(f"图片下载失败: {url[:60]}... 错误: {e}")
        return ""


class TiebaCrawler:
    """贴吧帖子爬虫"""

    def __init__(self, output_dir: str = ".", download_images: bool = True,
                 include_subposts: bool = True, progress_callback=None):
        self.output_dir = output_dir
        self.download_images = download_images
        self.include_subposts = include_subposts
        self.progress_callback = progress_callback
        self._stop = False

    def log(self, msg: str):
        if self.progress_callback:
            self.progress_callback(msg)

    def stop(self):
        self._stop = True

    def crawl(self, url: str) -> str:
        """
        爬取帖子，返回保存的Markdown文件路径
        """
        self._stop = False
        tid = extract_tid(url)
        self.log(f"开始爬取帖子 ID: {tid}")

        # 获取第一页以获取基本信息
        self.log("正在获取帖子基本信息...")
        first_page = get_page(tid, 1)
        if first_page.get("error_code") != 0:
            raise RuntimeError(f"API错误: {first_page.get('error_msg', '未知错误')}")

        thread_info = first_page.get("thread", {})
        page_info = first_page.get("page", {})
        total_pages = int(page_info.get("total_page", 1))
        total_posts = int(page_info.get("total_num", 0))

        title = thread_info.get("title", "无标题")
        author_info = thread_info.get("author", {})
        author_name = author_info.get("name_show") or author_info.get("name", "未知用户")
        create_time = thread_info.get("create_time", 0)
        # 从 twzhibo_info 或 display_forum 获取吧名
        forum_name = (
            thread_info.get("fname")
            or thread_info.get("twzhibo_info", {}).get("forum_name")
            or first_page.get("display_forum", {}).get("name")
            or ""
        )
        reply_num = thread_info.get("reply_num", 0)
        agree_num = thread_info.get("agree_num", 0)
        collect_num = thread_info.get("collect_num", 0)

        self.log(f"帖子标题: {title}")
        self.log(f"所在吧: {forum_name}吧")
        self.log(f"发帖人: {author_name}")
        self.log(f"共 {total_pages} 页，{total_posts} 楼")

        # 创建输出目录
        safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:50]
        post_dir = os.path.join(self.output_dir, f"{tid}_{safe_title}")
        img_dir = os.path.join(post_dir, "images")
        os.makedirs(post_dir, exist_ok=True)

        # 构建用户ID->名称映射
        user_map = {}

        # 收集所有楼层数据
        all_posts = []
        for page_num in range(1, total_pages + 1):
            if self._stop:
                self.log("爬取已停止")
                break
            self.log(f"正在获取第 {page_num}/{total_pages} 页...")
            if page_num == 1:
                page_data = first_page
            else:
                time.sleep(0.5)  # 适当延迟，避免请求过快
                page_data = get_page(tid, page_num)
                if page_data.get("error_code") != 0:
                    self.log(f"第 {page_num} 页获取失败，跳过")
                    continue

            # 更新用户映射
            for user in page_data.get("user_list", []):
                uid = str(user.get("id", ""))
                name = user.get("name_show") or user.get("name", "")
                if uid and name:
                    user_map[uid] = name

            posts = page_data.get("post_list", [])
            all_posts.extend(posts)

        self.log(f"共获取 {len(all_posts)} 个楼层")

        # 构建Markdown内容
        md_lines = []

        # 标题和元信息
        md_lines.append(f"# {title}\n")
        md_lines.append(f"> **所在吧**: {forum_name}吧  ")
        md_lines.append(f"> **发帖人**: {author_name}  ")
        md_lines.append(f"> **发帖时间**: {format_timestamp(create_time)}  ")
        md_lines.append(f"> **总回复数**: {reply_num}  ")
        md_lines.append(f"> **点赞数**: {agree_num}  ")
        md_lines.append(f"> **收藏数**: {collect_num}  ")
        md_lines.append(f"> **帖子链接**: https://tieba.baidu.com/p/{tid}\n")
        md_lines.append("---\n")

        # 全局图片计数器
        global_img_counter = [0]

        def process_post_content(post):
            """处理单个楼层的内容，返回markdown文本"""
            content_list = post.get("content", [])
            text, images = parse_content(content_list)

            # 下载图片并替换占位符
            if images and self.download_images:
                for i, img_url in enumerate(images):
                    global_img_counter[0] += 1
                    img_filename = f"img_{global_img_counter[0]:04d}"
                    local_name = download_image(img_url, img_dir, img_filename, self.log)
                    if local_name:
                        rel_path = f"images/{local_name}"
                        text = text.replace(f"__IMG_{i}__", f"\n\n![图片]({rel_path})\n")
                    else:
                        text = text.replace(f"__IMG_{i}__", f"\n\n![图片]({img_url})\n")
            else:
                # 不下载图片时，使用原始URL
                for i, img_url in enumerate(images):
                    text = text.replace(f"__IMG_{i}__", f"\n\n![图片]({img_url})\n")

            return text

        # 处理每个楼层
        for post in all_posts:
            if self._stop:
                break

            floor = post.get("floor", 0)
            pid = str(post.get("id", ""))
            post_time = post.get("time", 0)
            author_id = str(post.get("author_id", ""))
            post_author = user_map.get(author_id, f"用户{author_id}")
            sub_post_num = post.get("sub_post_number", 0)
            agree = post.get("agree", {}).get("agree_num", 0)

            self.log(f"处理第 {floor} 楼...")

            # 楼层标题
            if floor == 1:
                md_lines.append(f"## 第 1 楼（楼主）\n")
            else:
                md_lines.append(f"## 第 {floor} 楼\n")

            # 楼层元信息
            md_lines.append(f"**发帖人**: {post_author} | **时间**: {format_timestamp(post_time)} | **点赞**: {agree}\n")

            # 楼层内容
            content_text = process_post_content(post)
            if content_text.strip():
                md_lines.append(content_text)
            else:
                md_lines.append("*（内容为空）*")
            md_lines.append("")

            # 获取子回复（楼中楼）
            if self.include_subposts and sub_post_num > 0 and pid:
                self.log(f"  获取第 {floor} 楼的 {sub_post_num} 条子回复...")
                subposts = get_subposts(tid, pid)
                if subposts:
                    md_lines.append(f"<details>\n<summary>展开 {len(subposts)} 条楼中楼回复</summary>\n")
                    for sp in subposts:
                        sp_author_id = str(sp.get("author", {}).get("id", ""))
                        sp_author = (
                            sp.get("author", {}).get("name_show")
                            or sp.get("author", {}).get("name")
                            or user_map.get(sp_author_id, f"用户{sp_author_id}")
                        )
                        sp_time = sp.get("time", 0)
                        sp_content_list = sp.get("content", [])
                        sp_text, sp_images = parse_content(sp_content_list)

                        # 子回复图片处理
                        if sp_images and self.download_images:
                            for i, img_url in enumerate(sp_images):
                                global_img_counter[0] += 1
                                img_filename = f"img_{global_img_counter[0]:04d}"
                                local_name = download_image(img_url, img_dir, img_filename, self.log)
                                if local_name:
                                    sp_text = sp_text.replace(f"__IMG_{i}__", f"![图片](images/{local_name})")
                                else:
                                    sp_text = sp_text.replace(f"__IMG_{i}__", f"![图片]({img_url})")
                        else:
                            for i, img_url in enumerate(sp_images):
                                sp_text = sp_text.replace(f"__IMG_{i}__", f"![图片]({img_url})")

                        md_lines.append(f"> **{sp_author}** ({format_timestamp(sp_time)}): {sp_text}\n")
                    md_lines.append("</details>\n")

            md_lines.append("\n---\n")

        # 写入Markdown文件
        md_content = "\n".join(md_lines)
        md_filename = os.path.join(post_dir, f"{safe_title}.md")
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(md_content)

        self.log(f"[收工] 爬取完成！文件已保存至: {md_filename}")
        return md_filename


if __name__ == "__main__":
    # 命令行测试
    def print_progress(msg):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

    crawler = TiebaCrawler(
        output_dir="./output",
        download_images=True,
        include_subposts=True,
        progress_callback=print_progress,
    )
    result = crawler.crawl("https://tieba.baidu.com/p/7487460366")
    print(f"\n结果文件: {result}")
