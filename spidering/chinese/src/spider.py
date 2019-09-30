#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import pickle
import os
import subprocess
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re


class Spider:
    UNKNOWN = None
    BILIBILI = 'bilibili'
    TENCENT = 'tencent'
    IQIYI = 'iqiyi'
    YOUKU = 'youku'
    MARK = '@@@ '

    @staticmethod
    def get_source_and_vid(url):
        if 'bilibili.com' in url:
            return Spider.BILIBILI, re.search(r'(av[0-9]*)', url).group(1)
        elif 'qq.com' in url:
            return Spider.TENCENT, re.search(r'/([^/]*?)\.html', url).group(1)
        elif 'iqiyi.com' in url:
            return Spider.IQIYI, re.search(r'/([^/]*?)\.html', url).group(1)
        elif 'youku.com' in url:
            return Spider.YOUKU, re.search(r'/([^/]*?)\.html', url).group(1)
        else:
            return Spider.UNKNOWN, None

    def __init__(self):
        self.header = {'User-Agent': 'Chrome/76.0.3809.132'}
        # self.data['metadata']: vid -> video metadata
        self.data = {'query': None, 'urls': set(), 'metadata': {}}

    def set_query(self, query):
        self.data['query'] = query

    def save_data(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self.data, f)

    def load_data(self, filename):
        with open(filename, 'rb') as f:
            self.data = pickle.load(f)

    def save_urls(self, filename):
        with open(filename, 'w') as f:
            f.writelines(url + '\n' for url in self.data['urls'])

    def load_urls(self, filename):
        with open(filename) as f:
            self.data['urls'].update(f.read().splitlines())

    def export_query(self, filename):
        with open(filename, 'w') as f:
            f.write(self.data['query'] + '\n')

    def export_descriptions(self, filename):
        with open(filename, 'w') as f:
            f.writelines(Spider.MARK + k + '\n' + v['description'] + '\n' for k, v in self.data['metadata'].items() if
                         v['description'])

    def export_titles(self, filename):
        with open(filename, 'w') as f:
            f.writelines(Spider.MARK + k + '\n' + v['title'] + '\n' for k, v in self.data['metadata'].items() if v['title'])

    def download(self, output_dir, filters=None):
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        urls = self.data['urls'] if not filters else [url for url in self.data['urls'] if
                                                      any(s in url for s in filters)]
        for i, url in enumerate(urls):
            vid = self.get_source_and_vid(url)[1]
            print(f'Downloading video {i + 1} / {len(urls)}')
            subprocess.call(['you-get', '-o', output_dir, '-O', vid, url])

    def get_urls(self, source, num, duration=1, order=0, tids_1=0, tids_2=0, scr=1):
        bilibili_orders = ['totalrank', 'click', 'pubdate', 'dm', 'stow']
        iqiyi_sources = ['', 'iqiyi', 'qq', 'sohu', 'youku', 'tudou', 'acfun', 'bilibili', 'ifeng', 'cntv', 'm1905']
        if source == Spider.BILIBILI:
            fs = 'https://search.bilibili.com/all?keyword=' + self.data['query'] + '&order=' + bilibili_orders[
                order] + '&duration=' + str(duration) + '&tids_1=' + str(tids_1) + '&tids_2=' + str(tids_2) + '&page=%d'
        elif source == Spider.TENCENT:
            fs = 'https://v.qq.com/x/search/?q=' + self.data['query'] + '&cxt=%%3Dduration%%3D' + str(
                duration) + '&cur=%d'
        elif source == Spider.IQIYI:
            fs = 'https://so.iqiyi.com/so/q_' + self.data['query'] + '_ctg__t_' + str(
                duration + 1 if duration != 0 else 0) + '_page_%d' + '_p_1_qc_0_rd__site_' + iqiyi_sources[
                     scr] + '_m_1_bitrate_'
        elif source == Spider.YOUKU:
            fs = 'https://so.youku.com/search_video/q_' + self.data['query'] + '?aaid=0&lengthtype=' + str(
                duration) + '&pg=%d'
        else:
            print('Unknown source')
            return
        page = 1
        count = 0
        while count < num:
            prev_count = count
            print(f'--- Source {source}, Page {page} ---')
            s = fs % page
            response = requests.get(s, headers=self.header)
            if response.status_code != 200:
                print('Search failed: ' + s)
                return
            if source == Spider.BILIBILI:
                soup = BeautifulSoup(response.text, 'html.parser')
                video_items = soup.find_all('li', {'class': 'video-item matrix'})
            elif source == Spider.TENCENT:
                soup = BeautifulSoup(response.text, 'html.parser')
                video_items = soup.find_all('div', {'class': 'result_item result_item_h _quickopen'})
            elif source == Spider.IQIYI:
                soup = BeautifulSoup(response.text, 'html.parser')
                video_items = soup.find_all('li', {'class': 'list_item'})
            elif source == Spider.YOUKU:
                video_items = list(set(re.findall(r'(id_.*?)\.html', response.text)))
            else:
                print('Unknown source')
                return
            for v in video_items:
                if source == Spider.BILIBILI:
                    url = 'https://www.bilibili.com/video/' + v.find('span', {'class': 'type avid'}).text
                elif source == Spider.TENCENT:
                    url = v.a['href']
                elif source == Spider.IQIYI:
                    url = v.find({'a', 'href'})['href']
                elif source == Spider.YOUKU:
                    url = 'https://v.youku.com/v_show/' + v + '.html'
                else:
                    print('Unknown source')
                    return
                resp = requests.head(url, headers=self.header)
                if resp.status_code // 100 >= 4 or url in self.data['urls']:
                    continue
                self.data['urls'].add(url)
                count += 1
                print(f'Got video URL {count} / {num}')
                if count == num:
                    break
            if count == prev_count:
                break
            page += 1

    def get_data_from_url(self, url):
        # parses metadata from a single url, updates self.data
        source, vid = self.get_source_and_vid(url)
        if vid in self.data['metadata']:
            return
        response = requests.get(url, headers=self.header)
        if response.status_code != 200:
            print('Video page failed: ' + url)
            return
        if source == Spider.BILIBILI:
            s = re.search(r'window.__INITIAL_STATE__=({.*?});', response.text).group(1)
            d = json.loads(s)['videoData']
            self.data['metadata'][vid] = {'vid': vid, 'url': url, 'title': d['title'], 'description': d['desc'],
                                          'duration': d['duration'],
                                          'publish_time': datetime.fromtimestamp(d['pubdate']),
                                          'last_time': datetime.fromtimestamp(d['ctime']), 'poster': d['owner']['name']}
        elif source == Spider.TENCENT:
            s = re.search(r'var\s*VIDEO_INFO\s*=\s*({.*?})[;\n]', response.text, re.DOTALL).group(1)
            d = json.loads(s)
            pt = d['publish_date']
            if pt and pt[0] != '0':
                if len(pt) > 10:
                    publish_time = datetime.strptime(pt, '%Y-%m-%d %H:%M:%S')
                else:
                    publish_time = datetime.strptime(pt, '%Y-%m-%d')
            else:
                publish_time = None
            lt = d['modify_time']
            if lt and lt[0] != '0':
                if len(lt) > 10:
                    last_time = datetime.strptime(lt, '%Y-%m-%d %H:%M:%S')
                else:
                    last_time = datetime.strptime(lt, '%Y-%m-%d')
            else:
                last_time = None
            self.data['metadata'][vid] = {'vid': vid, 'url': url, 'title': d['title'], 'description': d['desc'],
                                          'duration': int(d['duration']), 'publish_time': publish_time,
                                          'last_time': last_time,
                                          'poster': d['upload_qq']}
        elif source == Spider.IQIYI:
            s = re.search(r'video-info=\'({.*?})\'', response.text).group(1)
            d = json.loads(s)
            poster = d['user']['name'] if 'user' in d else None
            self.data['metadata'][vid] = {'vid': vid, 'url': url, 'title': d['name'], 'description': d['description'],
                                          'duration': d['duration'],
                                          'publish_time': datetime.fromtimestamp(d['firstPublishTime'] * 1e-3),
                                          'last_time': datetime.fromtimestamp(d['lastPublishTime'] * 1e-3),
                                          'poster': poster,
                                          'subtitle': d['subtitle']}
        elif source == Spider.YOUKU:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('meta', {'name': 'title'})['content']
            description = soup.find('meta', {'name': 'description'})['content']
            duration = round(float(re.search(r'seconds:\s*\'(.*?)\'', response.text).group(1)))
            pt = soup.find('meta', {'itemprop': 'datePublished'})['content']
            publish_time = datetime.strptime(pt, '%Y-%m-%d %H:%M:%S') if pt != '' else None
            lt = soup.find('meta', {'itemprop': 'uploadDate'})['content']
            last_time = datetime.strptime(lt, '%Y-%m-%d %H:%M:%S') if lt != '' else None
            poster = re.search(r'videoOwner:\s*\'(.*?)\'', response.text).group(1)
            self.data['metadata'][vid] = {'vid': vid, 'url': url, 'title': title, 'description': description,
                                          'duration': duration, 'publish_time': publish_time, 'last_time': last_time,
                                          'poster': poster}
        else:
            print('Unknown source')

    def get_data(self):
        # processes all urls in self.data['urls'], updates self.data
        to_remove = set()
        for i, url in enumerate(self.data['urls']):
            print(f'Retrieving metadata {i + 1} / {len(self.data["urls"])}')
            try:
                self.get_data_from_url(url)
            except Exception as e:
                print('Error: ' + url)
                print(e)
                to_remove.add(url)
        self.data['urls'].difference_update(to_remove)
