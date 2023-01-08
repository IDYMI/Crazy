from multiprocessing.dummy import Pool
from fake_useragent import UserAgent
from lxml import etree
import requests
import time
import os
import random
import pandas as pd
from queue import Queue
import threading
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly as py

# 总路径
firstDirt = 'E:\\Crazy'


class Movie():
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random}
        self.columns = ['排名', '电影名称', '导演', '上映年份', '制作国家', '类型', '评分', '评价人数', '短评']  # 爬取信息
        self.interrupt = 10  # 爬取图片的间隔时间
        self.link = 'https://movie.douban.com/top250'
        self.movie_list = []
        self.dataQueue = Queue()
        if not os.path.exists(firstDirt):
            os.mkdir(firstDirt)
        self.num = 0

    def loading_Page(self, url):
        """向url发送请求,获取响应内容"""
        time.sleep(random.random())
        return requests.get(url, headers=self.headers).content

    def get_url(self, url):
        content = self.loading_Page(url)
        html = etree.HTML(content)
        div_list = html.xpath('//*[@id="content"]/div/div[1]/ol/li')
        for each in div_list:
            """排名、电影名称、导演、上映年份、制作国家、类型、评分、评价人数、短评"""
            # 排名
            ranks = each.xpath('div/div[1]/em/text()')
            # 电影名称
            titles = each.xpath('div/div[2]/div[1]/a/span[1]/text()')
            # 导演
            directors = each.xpath('div/div[2]/div[2]/p[1]/text()')[0].strip().replace("\xa0\xa0\xa0", "\t").replace(
                "导演: ", "").split(
                "\t")
            # 下一级网址
            next_html = each.xpath("div/div[2]/div[1]/a/@href")
            # 演员
            # actor = ""
            # res = requests.get(url=next_html[0], headers=self.headers, timeout=self.interrupt)
            # html = res.text
            # div_lists = etree.HTML(html).xpath('//*[@class="actor"]/*[@class="attrs"]/a/text()')
            # for eachs in div_lists:
            #     actor = actor + eachs + "、 "
            # print(actor)
            # 信息
            infos = each.xpath('div/div[2]/div[2]/p[1]/text()')[1].strip().replace('\xa0', '').split('/')
            # 上映年份 地区 类型
            dates, areas, genres = infos[0], infos[1], infos[2]
            # 评分
            ratings = each.xpath('.//div[@class="star"]/span[2]/text()')[0]
            # 评价人数
            scores = each.xpath('.//div[@class="star"]/span[4]/text()')[0][:-3]
            # 短评
            quotes = each.xpath('.//p[@class="quote"]/span/text()')
            for rank, title, director in zip(ranks, titles, directors):
                if len(quotes) == 0:
                    quotes = None
                else:
                    quotes = quotes[0]
                self.movie_list.append([int(rank), title, director, dates, areas, genres, ratings, scores, quotes])
            """图片保存"""
            img_list = each.xpath('.//a/img/@src')[0]
            self.dataQueue.put(self.movie_list)
            self.download_image(img_list, titles[0])
            # print(img_list)
        # print(self.movie_list)

        if url == self.link:
            return [self.link + link for link in html.xpath("//div[@class='paginator']/a/@href")]

    def write_movies_file(self):
        df = pd.DataFrame(self.movie_list, columns=self.columns)
        df_loc = df.sort_values(axis=0, by='排名', ascending=True)
        # path = pd.ExcelWriter(r'{}\Information\Top250.xlsx'.format(firstDirt))
        # df.to_excel(path, sheet_name='Top250', index=False)
        path = '{}\\Information\\Top250.csv'.format(firstDirt)
        with open(path) as fp:
            df_loc.to_csv(path, index=False)
        fp.close()

    def download_image(self, img_list, titles):
        print(titles + ' 图片正在保存...')
        url = requests.get(img_list, headers=self.headers)
        path = firstDirt + '\\films_pic'
        # print(path)
        with open(r'{}\{}.jpg'.format(path, titles), 'wb') as f:
            f.write(url.content)
        # time.sleep(self.interrupt)  # 网站承受能力

    def main(self):
        link_list = self.get_url(self.link)
        thread_list = []
        for link in link_list:
            thread = threading.Thread(target=self.get_url, args=[link])
            thread.start()
            thread_list.append(thread)

        # 父线程等待所有子线程结束，自己再结束
        for thread in thread_list:
            thread.join()

        # 循环get队列的数据，直到队列为空则退出
        while not self.dataQueue.empty():
            # print(self.num + 1)
            # print(self.dataQueue.get())
            self.movie_list = self.dataQueue.get()
            self.num += 1
        self.write_movies_file()

    def print_dall(self):
        path = '{}\\Information\\Top250.csv'.format(firstDirt)
        date = pd.read_csv(path, encoding='utf-8')

        plt.rcParams['font.sans-serif'] = ['SimHei']
        # 设置中文字体为黑体字
        plt.rcParams['font.family'] = 'sans-serif'
        # 解决负号'-'显示为方块的问题

        title = '电影名评分及评价人数折线图'
        lx = '电影名称'
        fyt = '评分'
        syt = '评价人数'
        y1data = go.Scatter(x=date[lx], y=date[fyt], name=fyt, showlegend=True, line=dict(color='blue'))
        y2data = go.Scatter(x=date[lx], y=date[syt], name=syt, showlegend=True, line=dict(color='red'),
                            yaxis='y2')
        fig = go.Figure(data=[y1data, y2data])
        fig.update_layout(
            title=title,
            yaxis=dict(title=fyt),
            yaxis2=dict(title=syt, overlaying='y', side='right'),
            # 设置背景色
            legend=dict(font=dict(color='black')))
        # fig.show()
        path = firstDirt + '\\Top250.html'
        py.offline.plot(fig, filename=path)
        print('折线图已经绘制完毕!')


if __name__ == '__main__':
    spider = Movie()
    while True:
        try:
            d = int(input("请选择：\n 爬虫（1）/ 画图（2）"))
            if d == 1:
                start_time = time.time()
                spider.main()
                end_time = time.time()
                print('爬取数据总用时{}秒'.format(int(end_time - start_time)))
                break
            elif d == 2:
                spider.print_dall()
                break
            else:
                print("输入错误，请重新输入")
        except:
            print("输入错误，请重新输入")
