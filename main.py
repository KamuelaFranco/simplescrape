#!/usr/bin/env python3
import argparse
import html.parser
import os
import os.path
import urllib.parse
import urllib.request


def html_parser(incoming_tag, html, HTMLParser=html.parser.HTMLParser):
    class MyHTMLParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self._lines = []

        def handle_starttag(self, tag, attrs):
            if tag == incoming_tag:
                if tag == "a":
                    attrs_dict = dict(attrs)
                    if attrs_dict["href"]:
                        self._lines.append(attrs_dict["href"])
                elif tag == "link":
                    attrs_dict = dict(attrs)
                    if attrs_dict["href"] and (
                            attrs_dict.get("rel") == "stylesheet"
                            or attrs_dict.get("rel") == "shortcut icon"
                            or attrs_dict.get("rel") == "icon"
                            or attrs_dict.get("rel") == "apple-touch-icon"
                            or attrs_dict.get("type") == "text/css"
                    ):
                        self._lines.append(attrs_dict["href"])
                elif tag == "script":
                    for attr in attrs:
                        if attr[0] == "src":
                            self._lines.append(attr[1])

        def read(self, data):
            self.feed(data)
            return self._lines

    a_parser = MyHTMLParser()
    return a_parser.read(html)


def get_local_path_from_full_url(url, local_directory, hostname, urlparse=urllib.parse.urlparse):
    parsed_url = urlparse(url)
    if parsed_url.hostname != hostname:
        local_path = f"{local_directory}/cached_external_assets/{parsed_url.path.strip('/')}"
    else:
        local_path = local_directory + parsed_url.path.strip("/")
    return local_path


def get_full_url_from_relative_path(relative_path, hostname, urlparse=urllib.parse.urlparse):
    url = urlparse(relative_path)
    if not url.hostname:
        full_url = f"http://{hostname}{url.path}"
        return full_url
    if not url.scheme:
        full_url = f"http://{relative_path}"
        return full_url
    return relative_path


def does_file_exist(path, isfile=os.path.isfile):
    return isfile(path)


def download_new_file(url, local_path, urlretrieve=urllib.request.urlretrieve):
    if does_file_exist(local_path):
        return
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    urlretrieve(url, local_path)


def get_html(url, urlopen=urllib.request.urlopen):
    return str(urlopen(url).read().decode("utf-8"))


def get_path_links(html):
    return html_parser("a", html)


def get_asset_paths(html):
    stylesheets = html_parser("link", html)
    scripts = html_parser("script", html)
    assets = stylesheets + scripts
    return assets


def main(url, urlparse=urllib.parse.urlparse):
    print(f"Downloading {url}")
    root_hostname = urlparse(url).hostname
    html = get_html(url)
    asset_paths = get_asset_paths(html)
    links_paths = get_path_links(html)
    for asset_path in asset_paths:
        full_url = get_full_url_from_relative_path(asset_path, hostname=root_hostname)
        local_path = get_local_path_from_full_url(full_url, "site/", hostname=root_hostname)
        download_new_file(full_url, local_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="root of the site you want to download (usually the index.html)")
    args = parser.parse_args()
    main(args.url)
