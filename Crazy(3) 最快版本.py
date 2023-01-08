from fake_useragent import UserAgent
from lxml import etree
import requests
import time
import os
from multiprocessing.dummy import Pool
import pandas as pd
import random
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import plotly as py

# 网站根地址
link = 'https://movie.douban.com/top250'
# 总路径
firstDirt = 'E:\\Crazy'

if not os.path.exists(firstDirt):
    os.mkdir(firstDirt)


class Movie():
    def __init__(self):
        self.headers = {
            'User-Agent': UserAgent().random,
            'Referer': link}
        self.columns = ['排名', '电影名称', '导演', '上映年份', '制作国家', '类型', '评分', '评价人数', '短评']  # 爬取信息
        self.interrupt = 10  # 爬取图片的间隔时间
        self.movie_list = []
        self.urls = {}
        if not os.path.exists(firstDirt):
            os.mkdir(firstDirt)

    def get_html(self):
        for i in range(0, 10):
            # 等待再次爬取，模拟人的操作
            time.sleep(random.random())
            print(f'正在爬取第{i + 1}页,请稍等...')
            try:
                url = "https://movie.douban.com/top250?start={}&filter=".format(str(i * 25))
                # print(url)
                res = requests.get(url, headers=self.headers, timeout=self.interrupt)
                html = res.text
                self.get_movies(html)
            except:
                print("出现错误！")
                break

    def get_movies(self, html):
        div_list = etree.HTML(html).xpath('//*[@id="content"]/div/div[1]/ol/li')
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
            # next_html = each.xpath("div/div[2]/div[1]/a/@href")
            # 完整演员(这里可以再加一个线程池，懒了，不写了，下回出博客补上）
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
                self.movie_list.append(
                    [int(rank), title, director, dates, areas, genres, ratings, scores, quotes])
            """图片保存"""
            img_list = each.xpath('.//a/img/@src')[0]
            self.urls[img_list] = titles[0]
            # print(self.urls[img_list])
            # print(img_list)

    def write_movies_file(self):
        df = pd.DataFrame(self.movie_list, columns=self.columns)
        df_loc = df.sort_values(axis=0, by='排名', ascending=True)
        # path = pd.ExcelWriter(r'{}\Information\Top250.xlsx'.format(firstDirt))
        # df.to_excel(path, sheet_name='Top250', index=False)
        path = '{}\\Information\\Top250.csv'.format(firstDirt)
        with open(path) as t:
            df_loc.to_csv(path, index=False)
        t.close()

    def download_image(self, url):
        print(self.urls[url], '正在下载.....')
        data = requests.get(url=url, headers=self.headers).content
        path = firstDirt + '\\films_pic\\' + self.urls[url] + '.jpg'
        # print(path)
        with open(path, 'wb') as fp:
            fp.write(data)
            print(self.urls[url], '下载成功')
        fp.close()
        # time.sleep(self.interrupt)  # 网站承受能力

    def main(self):
        start_time = time.time()
        self.get_html()
        image_list = list(self.urls.keys())
        # print(image_list)
        # 线程池（10线程）
        pool = Pool(10)
        pool.map(self.download_image, image_list)
        pool.close()
        pool.join()
        self.write_movies_file()
        end_time = time.time()
        print('爬取数据总用时{}秒'.format(int(end_time - start_time)))

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
                spider.main()
                break
            elif d == 2:
                spider.print_dall()
                break
            else:
                print("输入错误，请重新输入")
        except:
            print("错误")
