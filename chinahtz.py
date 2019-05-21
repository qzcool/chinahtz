#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""中国高新区科技金融信息服务平台的爬虫。"""

__author__ = 'Qiao Zhang'

import time
import json
import codecs
import pandas as pd
import pyautogui
from selenium import webdriver
from bs4 import BeautifulSoup
from collections import OrderedDict
from tqdm import tqdm


class Chinaahtz:

    def __init__(self, username=None, password=None):
        self.username, self.password = username, password
        self.driver = self.login()

    def login(self):
        """
        登录程序，输入用户密码，手工完成认证。
        :return:
        """
        #TODO：登录程序debug，登录按钮无法点击
        driver = webdriver.Chrome()

        driver.get('https://auth.cninfo.com.cn/login')
        driver.find_element_by_xpath("//*[@id='username']").send_keys(self.username)
        driver.find_element_by_xpath("//*[@id='password']").send_keys(self.password)
        print ("请在8s内手工完成认证。")
        time.sleep(8)
        driver.find_element_by_xpath("//*[@id='fm1']/div[5]/button").click()
        return driver

    def chinaahtz_scraper_biz(self,
                          url,
                          sector=None,
                          sector_sub=None,
                          area=None,
                          amount=None,
                          stage=None,
                          label=None,
                          keyword=None,
                          export='csv'):
        def get_list_urls(driver, sector, sector_sub, area, amount, stage, label):
            """
            获取当前筛选条件下的所有项目链接。
            :param driver:
            :return:
            """
            def set_filter(sector, sector_sub, area, amount, stage, label):
                """
                设置表头的筛选项目。
                :return:
                """
                if sector == '高端制造及工业制造':
                    driver.find_element_by_xpath("//*[@id='twe_6']").click()

                if sector_sub == '半导体/芯片':
                    driver.find_element_by_xpath("//*[@id='trade183']").click()

                if area is None:
                    pass

                if amount is None:
                    pass

                if stage is None:
                    pass

                if label is None:
                    pass

                return driver

            def read_pages_number():
                """
                返回当前筛选条件下的多项目列表页码数，用于翻页。
                :param driver:
                :return: pages_number
                """
                driver.find_element_by_xpath("//*[@id='RoadshowPull']/ul/li[13]/a").click()
                pages_number = int(driver.find_elements_by_xpath("//*[@id='RoadshowPull']/ul/li")[-1].text)
                driver.find_element_by_xpath("//*[@id='RoadshowPull']/ul/li[1]/a").click()
                # TODO:DEBUG
                print (pages_number, 'Pages Number.')
                return pages_number

            def change_page():
                """
                实现多列表页的翻页功能。
                :param driver:
                :return:
                """
                try:
                    driver.find_element_by_xpath("//*[@id='RoadshowPull']/ul/li[12]/a").click()
                except:
                    #TODO:DEBUG
                    # page_number_current = int(driver.find_element_by_xpath("//div[@class='content__pg']").get_attribute('data-curpage'))
                    # driver.find_element_by_xpath("//div[@class='content__pg']/a[@data-page='{}']".format(page_number_current+1)).click()
                    pass

            def get_list_urls_single():
                """
                获取单页所有的项目链接。获取项目ID号码并拼接URL
                :param driver:
                :return: list_urls_single
                """
                list_urls_single = []
                for i in driver.find_elements_by_xpath("//a[@class='content__list--item--aside']"):
                    list_urls_single.append(i.get_attribute('href'))
                return list_urls_single

            driver = set_filter(sector=sector, sector_sub=sector_sub, area=area, amount=amount, stage=stage,label=label)
            pages_number = read_pages_number()
            list_urls = []
            list_urls_single = get_list_urls_single()
            list_urls += list_urls_single
            print('开始获取当前筛选条件下的所有项目页链接。Windows平台下，请勿最小化浏览器。')
            for _ in tqdm(range(pages_number - 1)): # 默认-1/97
                change_page()
                list_urls_single = get_list_urls_single()
                list_urls += list_urls_single

            # 去除重复链接
            list_urls = list(set(list_urls))
            return list_urls

        def get_list_info(driver, url):
            """
            获取单项目信息。针对公寓和整租/合租的两种情况分别爬取,并分别存入数据库。
            :param driver:
            :param url:
            :return: df
            """
            driver.get(url)
            ##TODO：支持对公寓项目的爬取。
            if 'apartment' in url:
                pass
            else:
                # 类型/标题：可能为空，导致标题的爬取报错
                # try:
                #     rent_type = driver.find_element_by_xpath("//p[@class='content__title']").text.split(' · ')[0]
                #     title = driver.find_element_by_xpath("//p[@class='content__title']").text.split(' · ')[1]
                # except:
                #     rent_type = '未知'
                #     title = driver.find_element_by_xpath("//p[@class='content__title']").text
                rent_type = driver.find_elements_by_xpath("//p[@class='content__article__table']/span")[0].text
                title = driver.find_element_by_xpath("//p[@class='content__title']").text
                if '未知' in rent_type:
                    rent_type = '未知'

                # 上架时间
                time_listed = driver.find_element_by_xpath("//div[@class='content__subtitle']").text[7:17]

                # 编号
                house_code = driver.find_element_by_xpath("//div[@class='content__subtitle']/i[@class='house_code']").text[5:]

                # 信息卡照片：可能为空
                ##TODO:是否有多个？有bug无法打开
                try:
                    duty_img = driver.find_element_by_xpath("//div[@class='content__subtitle']/ul/li/div/img").get_attribute('src').split('!')[0]
                except:
                    duty_img = ''

                # 信息卡号：可能为空
                try:
                    duty_id = driver.find_element_by_xpath("//div[@class='content__subtitle']/ul/li/div/p").text.split('证件号码：')[1].stripe()
                except:
                    duty_id = ''

                # 营业执照
                ##TODO

                # 经纪备案：可能为空
                ##TODO
                try:
                    pass
                except:
                    pass

                # 项目照片列表
                json_house_imgs = []
                for i in driver.find_elements_by_xpath("//div[@class='content__article__slide__item']/img"):
                    json_house_imgs.append(i.get_attribute('src'))
                json_house_imgs = json.dumps(json_house_imgs, ensure_ascii=False)

                # 价格
                house_price = int(driver.find_element_by_xpath("//p[@class='content__aside--title']/span").text)

                # 特色标签列表
                json_house_tags = []
                for i in driver.find_elements_by_xpath("//p[@class='content__aside--tags']/i"):
                    json_house_tags.append(i.text)
                json_house_tags = json.dumps(json_house_tags, ensure_ascii=False)

                # 户型、面积、朝向
                house_type = driver.find_elements_by_xpath("//p[@class='content__article__table']/span")[1].text
                house_area = int(driver.find_elements_by_xpath("//p[@class='content__article__table']/span")[2].text.split('㎡')[0])
                house_orient = driver.find_elements_by_xpath("//p[@class='content__article__table']/span")[3].text.split('朝')[1]

                # 经纪人姓名：可能为空
                ##TODO

                # 经纪人联系方式
                try:
                    broker_contact = driver.find_element_by_xpath("//p[@class='content__aside__list--bottom oneline']").text
                except:
                    broker_contact = ''

                # 最短租期/最长租期:统一显示为天数，一年360天(防止12个月和365天天数不相等的情况)，一个月30天
                rent_peroid = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[5]").text[3:]
                if '~' in rent_peroid:
                    if '月' in rent_peroid:
                        rent_peroid_lower = int(rent_peroid.split('~')[0])*30
                        rent_peroid_upper = int(rent_peroid.split('~')[1].split('个月')[0])*30
                    elif '年' in rent_peroid:
                        rent_peroid_lower = int(rent_peroid.split('~')[0])*360
                        rent_peroid_upper = int(rent_peroid.split('~')[1].split('年')[0])*360
                    else:
                        print ("请手工检查租期：", rent_peroid, url)
                        rent_peroid_lower = rent_peroid
                        rent_peroid_upper = rent_peroid
                else:
                    rent_peroid_lower = rent_peroid
                    rent_peroid_upper = rent_peroid

                # 所在楼层
                house_floor = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[8]").text[3:].split('/')[0]

                # 总楼层
                house_total_floor = int(driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[8]").text[3:].split('/')[1].replace('层',''))

                # 车位
                parking = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[11]").text[3:]

                # 用电
                electricity_type = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[14]").text[3:]

                # 入住
                check_in = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[3]").text[3:]

                # 看房
                reservation = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[6]").text[3:]

                # 电梯
                lift = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[9]").text[3:]

                # 用水
                water = driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[12]").text[3:]

                # 燃气
                ##TODO:和下面的天然气有什么区别？
                gas= driver.find_element_by_xpath("//div[@class='content__article__info']/ul/li[15]").text[3:]

                # 电视
                television = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[2]").get_attribute('class')
                if '_no' in television:
                    television = 0
                else:
                    television = 1

                # 冰箱
                refrigerator = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[3]").get_attribute('class')
                if '_no' in refrigerator:
                    refrigerator = 0
                else:
                    refrigerator = 1

                # 洗衣机
                washing_machine = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[4]").get_attribute('class')
                if '_no' in washing_machine:
                    washing_machine = 0
                else:
                    washing_machine = 1

                # 空调
                air_conditioner = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[5]").get_attribute('class')
                if '_no' in air_conditioner:
                    air_conditioner = 0
                else:
                    air_conditioner = 1

                # 热水器
                water_heater = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[6]").get_attribute('class')
                if '_no' in water_heater:
                    water_heater = 0
                else:
                    water_heater = 1

                # 床
                bed = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[7]").get_attribute('class')
                if '_no' in bed:
                    bed = 0
                else:
                    bed = 1

                # 暖气
                heating = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[8]").get_attribute('class')
                if '_no' in heating:
                    heating = 0
                else:
                    heating = 1

                # 宽带
                wifi = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[9]").get_attribute('class')
                if '_no' in wifi:
                    wifi = 0
                else:
                    wifi = 1

                # 衣柜
                wardrobe = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[10]").get_attribute('class')
                if '_no' in wardrobe:
                    wardrobe = 0
                else:
                    wardrobe = 1

                # 天然气
                natural_gas = driver.find_element_by_xpath("//ul[@class='content__article__info2']/li[11]").get_attribute('class')
                if '_no' in natural_gas:
                    natural_gas = 0
                else:
                    natural_gas = 1

                # 地址和交通，地铁便利性
                ##TODO:地铁便利性的筛选标准，距任一地铁站的距离有小于1000m的
                accessibility_subway = 0
                try:
                    list_subways = []
                    for i in driver.find_elements_by_xpath("//div[@class='content__article__info4']/ul/li"):
                        subway_line = i.text[3:].split(' - ')[0]
                        subway_station = i.text.split(' - ')[1].split(' ')[0]
                        subway_station_distance = int(i.text.split(' - ')[1].split(' ')[1].split('m')[0])
                        list_subways.append([subway_line,subway_station,subway_station_distance])

                        if subway_station_distance < 1000:
                            accessibility_subway = 1
                    json_subways = json.dumps(list_subways, ensure_ascii=False)
                except:
                    print("地址和交通有未知错误：", url)
                    json_subways = ''

                # 小区最新成交
                try:
                    complex_deals = driver.find_element_by_xpath("//div[@class='table']").get_attribute('innerHTML')
                    table = BeautifulSoup(complex_deals, 'lxml')
                    record = []
                    # 表格内容
                    for tr in table.find_all("div", class_='tr')[1:]:
                        cols = tr.find_all("div", class_='td')
                        cols = [ele.text.strip() for ele in cols]
                        record.append([ele for ele in cols if ele])  # Get rid of empty values
                    complex_deals = pd.DataFrame(data=record, columns=['成交日期','居室','面积','租赁方式','出租价格']).to_json(orient='records', force_ascii=False)
                except:
                    print ("无小区最新成交信息：", url)
                    complex_deals = ''

                # 项目描述
                if len(driver.find_elements_by_xpath("//div[@class='content__article__info3 ']/ul/li/p")) > 2:
                    house_description = ''
                    print ("请调整子函数get_list_info的项目描述部分，有超过一条评论的情况需要全部考虑。（做成列表而不再是文本）", url)
                else:
                    try:
                        house_description = driver.find_element_by_xpath("//div[@class='content__article__info3 ']/ul/li/p[1]").text
                    except:
                        house_description = ''

                # 项目链接
                house_url = url

                # 城市
                city = driver.find_element_by_xpath("//div[@class='bread__nav w1150 bread__nav--empty']/p/a[1]").text[:-3]

                # 城区
                district = driver.find_element_by_xpath("//div[@class='bread__nav w1150 bread__nav--empty']/p/a[2]").text[:-2]

                # 商圈
                bizcircle = driver.find_element_by_xpath("//div[@class='bread__nav w1150 bread__nav--empty']/p/a[3]").text[:-2]

                # 小区名称
                complex = driver.find_element_by_xpath("//div[@class='bread__nav w1150 bread__nav--empty']/h1/a").text[:-2]

                # 小区链接
                complex_url = driver.find_element_by_xpath("//div[@class='bread__nav w1150 bread__nav--empty']/h1/a").get_attribute('href')

                # 每平米房价
                try:
                    house_price_unit = round(house_price/house_area, 2)
                except:
                    print('无法计算每平米房价：', url)
                    house_price_unit = ''

                # 经纪人品牌
                broker_brand = driver.find_element_by_xpath("//div[@class='content__aside fr']/ul[@class='content__aside__list']/li/p").text
                if ' 经纪人' in broker_brand:
                    broker_brand = broker_brand[:-4]
                if '管家' in broker_brand:
                    broker_brand = broker_brand[:-3]

                # 上下楼便利性：无障碍性，楼层与电梯的合成项
                accessibility_floor = 0
                if lift == '有':
                    accessibility_floor = 1
                elif lift == '无' and house_floor <= '3':
                    accessibility_floor = 1
                elif lift == 0 and house_floor == '低楼层':
                    accessibility_floor = 1
                else:
                    pass

                # 导出所有信息
                dict_single = {'类型':rent_type,'标题':title,'上架时间':time_listed,'编号':house_code,'信息卡照片':duty_img,'信息卡号':duty_id,
                              '营业执照':'','经纪备案':'','项目图片列表':json_house_imgs,'价格':house_price,'特色标签列表':json_house_tags,
                              '户型':house_type,'面积':house_area,'朝向':house_orient,'经纪人姓名':'','经纪人联系方式':broker_contact,
                              '最短租期':rent_peroid_lower,'最长租期':rent_peroid_upper,'所在楼层':house_floor,'总楼层':house_total_floor,
                              '车位':parking,'用电':electricity_type,'入住':check_in,'看房':reservation,'电梯':lift,'用水':water,'燃气':gas,
                              '电视':television, '冰箱':refrigerator,'洗衣机':washing_machine,'空调':air_conditioner,'热水器':water_heater,
                              '床':bed,'暖气':heating,'宽带':wifi,'衣柜':wardrobe,'天然气':natural_gas,'地址和交通':json_subways,
                              '小区最新成交':complex_deals,'项目描述':house_description,'项目链接':house_url,
                              '城市':city,'城区':district,'商圈':bizcircle,'小区名称':complex,'小区链接':complex_url,
                              '每平米房价':house_price_unit, '经纪人品牌':broker_brand, '上下楼便利性':accessibility_floor,
                              '地铁便利性':accessibility_subway}
                return dict_single

        def gen_json(table_dict, keyword):
            """
            保存字典为JSON文件，用于数据存储。
            :param table_dict: dict_all
            :param keyword: 筛选条件
            :return:
            """
            list_dic = []
            for i in list(table_dict.keys()):
                list_dic.append((i, table_dict[i]))
            dic = OrderedDict(list_dic)
            list_json = WriterJson().odict_to_json(dic)
            WriterJson().write_json(json_list=list_json, file_name=keyword+'.json')

        def main(driver, keyword):
            """
            主运行函数。
            :param driver:
            :param keyword: 筛选条件，用于命名JSON文件。
            :return: df
            """
            # 获取符合当前筛选条件的所有项目链接
            list_urls = get_list_urls(driver=driver)

            # 循环获取单项目信息并保存为df
            print("开始获取项目具体信息。")
            dict_all = {}
            list_sequence = 0
            df = pd.DataFrame()
            for url in tqdm(list_urls):
                if 'apartment' not in url:
                    try:
                        dict_single = get_list_info(driver=driver, url=url)
                        dict_all[list_sequence] = dict_single
                        df = df.append(pd.DataFrame(list(dict_all[list_sequence].items())).transpose(), ignore_index=True)
                        list_sequence += 1
                    except:
                        print("有未知报错，请检查:", url)
                        pass

            # 去除多余的表头
            ##TODO:加快表头的处理速度。
            df.drop_duplicates(inplace=True)
            df = df.reset_index()
            header = df.iloc[0]
            df = df[1:]
            df.columns = header

            # 保存列表为JSON或csv（默认）
            if export == 'csv':
                df.to_csv(keyword+'.csv', encoding='gb18030')
            elif export == 'json':
                gen_json(table_dict=dict_all, keyword=keyword)
            elif export is None:
                pass
            else:
                print("请选择正确的输出格式，支持'xlsx'和'json'。")
                pass

            driver.quit()
            return df

        self.driver.get(url)
        df = main(self.driver, keyword)
        return df


if __name__ == "__main__":
    df_bizcircles = Chinaahtz(username='13661277904', password='Youcai123').chinaahtz_scraper(url='https://www.chinahtz.com/FincProj/EntpFincProj.do', keyword='高端制造及工业制造-半导体芯片', export='csv')
