#!/usr/bin/env python3
import argparse
import html.parser
import os
import os.path
import urllib.error
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
                    if attrs_dict.get("href"):
                        self._lines.append(attrs_dict["href"])
                elif tag == "link":
                    attrs_dict = dict(attrs)
                    if attrs_dict.get("href") and (
                            attrs_dict.get("rel") == "stylesheet"
                            or attrs_dict.get("rel") == "shortcut icon"
                            or attrs_dict.get("rel") == "icon"
                            or attrs_dict.get("rel") == "apple-touch-icon"
                            or attrs_dict.get("type") == "text/css"
                    ):
                        self._lines.append(attrs_dict["href"])
                elif tag == "script":
                    attrs_dict = dict(attrs)
                    if attrs_dict.get("src"):
                        self._lines.append(attrs_dict["src"])
                elif tag == "img":
                    attrs_dict = dict(attrs)
                    if attrs_dict.get("src"):
                        self._lines.append(attrs_dict["src"])

        def read(self, data):
            self.feed(data)
            return self._lines

    a_parser = MyHTMLParser()
    return a_parser.read(html)


def get_local_path_from_full_url(url, local_directory, hostname, urlparse=urllib.parse.urlparse):
    parsed_url = urlparse(url)
    if not local_directory.endswith("/"):
        local_directory += "/"
    if parsed_url.hostname != hostname:
        local_path = f"{local_directory}cached_external_assets/{parsed_url.path.strip('/')}"
    else:
        local_path = local_directory + parsed_url.path.strip("/")
    return local_path


def get_full_url_from_relative_path(relative_path, hostname, urlparse=urllib.parse.urlparse):
    url = urlparse(relative_path)
    if not url.hostname:
        full_url = f"http://{hostname}/{url.path.strip('/')}"
        return full_url
    if not url.scheme:
        full_url = f"http:{relative_path}"
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


def get_path_links(html, hostname, urlparse=urllib.parse.urlparse):
    all_raw_links = html_parser("a", html)
    all_links = list(set(map(lambda link: get_full_url_from_relative_path(link, hostname), all_raw_links)))
    local_links = []
    for link in all_links:
        if urlparse(link).hostname == hostname:
            local_links.append(link)
    return local_links


def get_asset_paths(html):
    stylesheets = html_parser("link", html)
    scripts = html_parser("script", html)
    images = html_parser("img", html)
    assets = stylesheets + scripts + images
    return assets


def main(url, subdirectory="site/", root_hostname="", links=[], downloaded_links=[], urlparse=urllib.parse.urlparse):
    print(f"Crawling {url}")
    parsed_url = urlparse(url)
    if not root_hostname:
        root_hostname = parsed_url.hostname
    html = get_html(url)
    if not subdirectory.endswith("/"):
        subdirectory += "/"
    if not parsed_url.path.endswith(".html"):
        os.makedirs(os.path.dirname(subdirectory), exist_ok=True)
        with open(f"{subdirectory}index.html", "w") as f:
            f.write(html)
            f.close()
        downloaded_links.append(url)
    asset_paths = list(set(map(
        lambda path: get_full_url_from_relative_path(path, root_hostname),
        get_asset_paths(html))))
    for asset_path in asset_paths:
        local_path = get_local_path_from_full_url(asset_path, subdirectory, hostname=root_hostname)
        try:
            download_new_file(asset_path, local_path)
        except urllib.error.URLError:
            print("Connection attempt failed while trying to download:")
            print(f"\t{asset_path} TO {local_path}")
        except:
            print("An unknown failure occurred while trying to download:")
            print(f"\t{asset_path} TO {local_path}")
    local_link_paths = get_path_links(html, root_hostname)
    links += local_link_paths
    remaining_links = [a_link for a_link in links if a_link not in downloaded_links]
    for link in remaining_links:
        next_subdirectory = get_local_path_from_full_url(link, subdirectory, hostname=root_hostname)
        main(link, subdirectory=next_subdirectory, root_hostname=root_hostname, links=remaining_links,
             downloaded_links=downloaded_links)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="root of the site you want to download")
    args = parser.parse_args()
    main(args.url)
