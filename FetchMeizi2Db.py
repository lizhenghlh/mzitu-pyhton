#coding: utf-8
import argparse
import urllib2
import os
import requests
import sqlite3
from MyThread import MyThread
from urllib2 import  Request
from bs4 import BeautifulSoup


def get_html(url_address):
    """
    通过url_address得到网页内容
    :param url_address: 请求的网页地址
    :return: html
    """
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:23.0) Gecko/20100101 Firefox/23.0'}
    req = urllib2.Request(url=url_address, headers=headers)
    return urllib2.urlopen(req)

#
def get_soup(html):
    """
    把网页内容封装到BeautifulSoup中并返回BeautifulSoup
    :param html: 网页内容
    :return:BeautifulSoup
    """
    if None == html:
        return
    return BeautifulSoup(html.read(), "html.parser")


def get_img_dirs(soup):
    """
    获取所有相册标题及链接
    :param soup: BeautifulSoup实例
    :return: 字典（ key:标题， value:内容）
    """
    if None == soup:
        return
    lis = soup.find(id="pins").findAll(name='li') # findAll(name='a') # attrs={'class':'lazy'}
    if None != lis:
        img_dirs = {};
        for li in lis:
            links = li.find('a')
            k = links.find('img').attrs['alt']
            t = links.attrs['href']
            img_dirs[k] = t;
        print(img_dirs)
        return img_dirs

def insert_gallery(conn,name,url):
    sql = "INSERT INTO GALLERY (NAME,URL) VALUES ( '" + name + "' , '" + url + "' )"
    print(sql)
    conn.execute(sql)
    conn.commit()

def fetch_imgs(info):
    if None == info:
        return

    # 创建数据库连接
    conn = sqlite3.connect('meizitu.db')
    if None == conn:
        return

    t = info[0]
    l = info[1]
    if None == t or None == l:
        return
    print("创建相册：" + t +" " + l)

    # 插入 相册名称和url连接
    insert_gallery(conn,t,l);

    try:
        os.mkdir(t)
    except Exception as e:
        print("文件夹："+t+"，已经存在")

    print("开始获取相册《" + t + "》内，图片的数量...")

    dir_html = get_html(l)
    dir_soup = get_soup(dir_html)
    img_page_url = get_dir_img_page_url(l, dir_soup)

    # 得到当前相册的封面
    main_image = dir_soup.findAll(name='div', attrs={'class':'main-image'})
    if None != main_image:
        for image_parent in main_image:
            imgs = image_parent.findAll(name='img')
            if None != imgs:
                img_url = str(imgs[0].attrs['src'])
                filename = img_url.split('/')[-1]
                print("开始下载:" + img_url + ", 保存为："+filename)

    # 获取相册下的图片
    for photo_web_url in img_page_url:
        fetch2db(conn, t, photo_web_url)



def fetch2db(conn, t, page_url):
    dir_html = get_html(page_url)
    dir_soup = get_soup(dir_html)

    # 得到当前页面的图片
    main_image = dir_soup.findAll(name='div', attrs={'class':'main-image'})
    if None != main_image:
        for image_parent in main_image:
            imgs = image_parent.findAll(name='img')
            if None != imgs:
                img_url = str(imgs[0].attrs['src'])
                filename = img_url.split('/')[-1]
                print("开始保存:" + img_url + ", 保存为："+filename)
                sql = "SELECT id from GALLERY where NAME = '" + t + "'"
                # print(sql)
                cursor = conn.execute(sql)
                for row in cursor:
                    id = row[0]

                print(id)
                sql = "INSERT INTO PHOTO (GALLERY,URL) VALUES (" + str(id) + " , '" + img_url + "' )"
                print(sql)
                conn.execute(sql)
                conn.commit()


def get_dir_img_page_url(l, dir_soup):
    """
    获取相册里面的图片数量
    :param l: 相册链接
    :param dir_soup:
    :return: 相册图片数量
    """
    divs = dir_soup.findAll(name='div', attrs={'class':'pagenavi'})
    navi = divs[0]
    code = navi['class']
    print(code)

    links = navi.findAll(name='a')
    if None == links:
        return
    a = []
    url_list = []
    for link in links:
        h = str(link['href'])
        n = h.replace(l+"/", "")
        try:
            a.append(int(n))
        except Exception as e:
            print(e)
    _max = max(a)
    for i in range(1, _max):
        u = str(l+"/"+str(i))
        url_list.append(u)
    return url_list



if __name__ == '__main__':
    #创建meizitu表
    conn = sqlite3.connect('meizitu.db')

    print "Opened database successfully";

    conn.execute('''CREATE TABLE IF NOT EXISTS GALLERY
       (ID INTEGER PRIMARY KEY AUTOINCREMENT,
       NAME           TEXT    NOT NULL,
       URL            TEXT    NOT NULL);''')
    print "GALLERY Table created successfully";

    conn.execute('''CREATE TABLE IF NOT EXISTS PHOTO 
       (ID INTEGER PRIMARY KEY AUTOINCREMENT,
       GALLERY       INTEGER         NOT NULL,
       URL           TEXT    NOT NULL);''')
    print "PHOTO Table created successfully";

    parser = argparse.ArgumentParser()
    parser.add_argument("echo")
    # parser.add_argument("url")
    # url = int(args.url)
    args = parser.parse_args()
    url = str(args.echo)
    print("开始解析：" + url)

    html = get_html(url)
    soup = get_soup(html)
    img_dirs = get_img_dirs(soup)
    if None == img_dirs:
        print("无法获取该网页下的相册内容...")
    else:
        for d in img_dirs:
            my_thread = MyThread(fetch_imgs, (d, img_dirs.get(d)))
            my_thread.start()
            my_thread.join()



