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
        driver = webdriver.Chrome()

        driver.get('https://auth.cninfo.com.cn/login')
        driver.find_element_by_xpath("//*[@id='username']").send_keys(self.username)
        driver.find_element_by_xpath("//*[@id='password']").send_keys(self.password)
        print ("请在8s内手工完成认证，认证后请勿点击登录按钮。")
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
                return pages_number

            def change_page():
                """
                实现多列表页的翻页功能。
                :param driver:
                :return:
                """
                driver.find_element_by_xpath("//*[@id='RoadshowPull']/ul/li[12]/a").click()

            def get_list_urls_single():
                """
                获取单页所有的项目链接。获取项目ID号码并拼接URL
                :param driver:
                :return: list_urls_single
                """
                list_urls_single = []
                for i in driver.find_elements_by_xpath("//div[@class='proj-left']/a"):
                    url_prefix = 'https://www.chinahtz.com/FincProj/FincProjefpdetail.do?id='
                    url_project = url_prefix + i.get_attribute('onclick').split('(')[1].split(',')[0]
                    list_urls_single.append(url_project)
                return list_urls_single

            driver = set_filter(sector=sector, sector_sub=sector_sub, area=area, amount=amount, stage=stage,label=label)
            pages_number = read_pages_number()
            list_urls = []
            list_urls_single = get_list_urls_single()
            list_urls += list_urls_single
            print('开始获取当前筛选条件下的所有项目页链接。Windows平台下，请勿最小化浏览器。')
            # TODO： DEBUG为什么只有前四页可以爬取
            for i in tqdm(range(pages_number - 1)): # 默认-1/14
                print (i)
                change_page()
                list_urls_single = get_list_urls_single()
                list_urls += list_urls_single

            # 去除重复链接
            print ("开始去除重复链接:长度", len(list_urls))
            print (list_urls)
            list_urls = list(set(list_urls))
            print ("结束去除重复链接:长度", len(list_urls))
            return list_urls

        def get_list_info(driver, url):
            """
            获取单项目信息。
            :param driver:
            :param url:
            :return: df
            """
            driver.get(url)

            # 项目名称
            name = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div/div/div[1]").text.strip()

            # 行业
            industry = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div/div/div[2]").text.strip()

            # 轮次
            round = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div/div/div[3]/ul/li[1]").text.strip()

            # 融资额
            amount = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div/div/div[3]/ul/li[2]").text.strip()

            # 城市
            city = driver.find_element_by_xpath("/html/body/div[2]/div[1]/div[2]/div/div/div[3]/ul/li[3]").text.strip()

            # 项目介绍
            project_info = driver.find_elements_by_xpath("//*[@id='descri_content']")[0].text.strip()
            print (project_info)

            # 核心成员：姓名，职位，介绍
            # TODO: 将核心成员变为列表JSON
            # core_name = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/div[3]/div[2]").text.strip()
            # try:
            #     core_title = driver.find_elements_by_xpath("/html/body/div[3]/div/div[1]/div[3]/div[2]/span")[0].text.strip()
            # except:
            #     core_title = driver.find_elements_by_xpath("/html/body/div[3]/div/div[1]/div[3]/div[2]/span").text.strip()
            # core_info = driver.find_element_by_xpath("/html/body/div[3]/div/div[1]/div[3]/div[2]/span/div").text.strip()
            core_name, core_title, core_info = '', '', ''
            print (core_name, core_title, core_info)

            # 股权结构
            # TODO:DEBUG股权结构不显示
            try:
                list_shares = []
                for i in driver.find_elements_by_xpath("/html/body/div[3]/div/div[1]/div[4]/div[2]/ul/li"):
                    shares_holder = i.split(' 丨 ')[0]
                    shares_percentage = i.text.split('：')[1]
                    list_shares.append([shares_holder, shares_percentage])

                json_shares = json.dumps(list_shares, ensure_ascii=False)
            except:
                print("无股权结构：", url)
                json_shares = ''
            print (json_shares)

            # 公司介绍:公司介绍、企业名称、工商注册号、成立时间、注册资本、所属行业
            company_info = driver.find_element_by_xpath("//*[@id='intrds_content']").text
            company_name = driver.find_element_by_xpath("//*[@id='projectBasicInfo']/tbody/tr[1]/td[2]").text
            company_id = driver.find_element_by_xpath("//*[@id='projectBasicInfo']/tbody/tr[2]/td[2]").text
            company_date_found = driver.find_element_by_xpath("//*[@id='projectBasicInfo']/tbody/tr[3]/td[2]").text
            company_capital = driver.find_element_by_xpath("//*[@id='projectBasicInfo']/tbody/tr[4]/td[2]").text
            company_sector = driver.find_element_by_xpath("//*[@id='projectBasicInfo']/tbody/tr[5]/td[2]").text

            # 查看该项目投资人
            # TODO: 项目投资人需要爬取全量列表，优先级较低
            # https://www.chinahtz.com/sizeContacts/queryStaOperationList.do?entpProjID=12897
            json_investors = ''

            # 联系方式：联系电话，联系邮箱
            try:
                contact_phone = driver.find_elements_by_xpath("//*[@id='project_lxfs']/ul/li[1]")[1].text.split(";")[1].strip()
            except:
                contact_phone = '互递名片后可见'
            try:
                contact_email = driver.find_element_by_xpath("//*[@id='project_lxfs']/ul/li[2]/a").text
            except:
                contact_email = '互递名片后可见'

            # 推荐单位
            referrer = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/div[2]/div/div[2]/ul/li/a").text
            referrer_url = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/div[2]/div/div[2]/ul/li/a").get_attribute('href')

            # 商业计划书
            url_bp_name = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/div[3]/div/div[2]/ul/li/a").get_attribute('onclick').split('(')[1].split(',')[0][1:-1]
            url_bp_title = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/div[3]/div/div[2]/ul/li/a").get_attribute('onclick').split(',')[1].split(',')[0][1:-1]
            url_bp_id = driver.find_element_by_xpath("/html/body/div[3]/div/div[2]/div[3]/div/div[2]/ul/li/a").get_attribute('onclick').split(',')[2].split(')')[0]
            url_bp = 'https://www.chinahtz.com/downLoad/openProjFileView.do?name={}&title={}&id={}'.format(url_bp_name, url_bp_title, url_bp_id)
            driver.get(url_bp)
            url_bp = driver.find_element_by_xpath("/html/body/div[1]/div[1]/div[3]/iframe").get_attribute('src')

            # 导出所有信息
            dict_single = {'项目名称': name,
                           '行业': industry,
                           '轮次': round,
                           '融资额': amount,
                           '城市': city,
                           '项目介绍': project_info,
                           '核心成员姓名': core_name,
                           '核心成员职位': core_title,
                           '核心成员介绍': core_info,
                           '股权结构': json_shares,
                           '公司介绍': company_info,
                           '企业名称': company_name,
                           '工商注册号': company_id,
                           '成立时间': company_date_found,
                           '注册资本': company_capital,
                           '所属行业': company_sector,
                           '查看该项目投资人':json_investors,
                           '联系电话': contact_phone,
                           '联系邮箱': contact_email,
                           '推荐单位': referrer,
                           '推荐单位链接': referrer_url,
                           '商业计划书': url_bp
                           }
            return dict_single

        def main(driver, keyword):
            """
            主运行函数。
            :param driver:
            :param keyword: 筛选条件，用于命名JSON文件。
            :return: df
            """
            # 获取符合当前筛选条件的所有项目链接
            list_urls = get_list_urls(driver=driver, sector=sector, sector_sub=sector_sub, area=area, amount=amount, stage=stage, label=label)

            # 循环获取单项目信息并保存为df
            print("开始获取项目具体信息。")
            print (list_urls)
            dict_all = {}
            list_sequence = 0
            df = pd.DataFrame()
            for url in tqdm(list_urls):
                try:
                    dict_single = get_list_info(driver=driver, url=url)
                    dict_all[list_sequence] = dict_single
                    df = df.append(pd.DataFrame(list(dict_all[list_sequence].items())).transpose(), ignore_index=True)
                    list_sequence += 1
                except Exception as e:
                    print("有报错，请检查:", e, url)
                    pass

            # 去除多余的表头
            df.drop_duplicates(inplace=True)
            df = df.reset_index()
            header = df.iloc[0]
            df = df[1:]
            df.columns = header

            # 保存列表为csv
            if export == 'csv':
                df.to_csv(keyword+'.csv', encoding='gb18030')
            elif export is None:
                pass
            else:
                print("请选择正确的输出格式，支持'csv'。")
                pass

            driver.quit()
            return df

        # 运行环节
        self.driver.get(url)
        df = main(self.driver, keyword)
        return df


if __name__ == "__main__":
    df_bizcircles = Chinaahtz(username='13661277904', password='Youcai123').chinaahtz_scraper_biz(url='https://www.chinahtz.com/FincProj/EntpFincProj.do', sector='高端制造及工业制造', sector_sub='半导体/芯片', keyword='高端制造及工业制造-半导体芯片', export='csv')
