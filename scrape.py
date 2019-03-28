#Importing packages
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import selenium.webdriver.support.ui as ui
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
import pandas as pd
import os
import time 
import json
from credentials import *
from selenium.webdriver.firefox.options import Options

url = "https://apps.mohawkcollege.ca/login"
driver = webdriver.Firefox()


# login to Mohawk APPS using credentials found in crednetials.py
def login(driver):
    # navigate to Mohawk APPS
    driver.get("https://apps.mohawkcollege.ca/login")
    driver.find_element_by_id("username").click()
    driver.find_element_by_id("username").clear()
    # send username variable from credentials
    driver.find_element_by_id("username").send_keys(username)
    driver.find_element_by_id("password").click()
    driver.find_element_by_id("password").clear()
    # send password variable from credentials
    driver.find_element_by_id("password").send_keys(password)
    driver.find_element_by_xpath("(.//*[normalize-space(text()) and normalize-space(.)='This field is required.'])[4]/following::button[1]").click()
    # wait for confirmation of app popup
    ui.WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id('welcome-setup'))
    time.sleep(10)
    driver.find_element_by_id("welcome-continue").click()
    time.sleep(20)
    # wait for bottom communication notification
    driver.find_element_by_class_name("button--approve").click()
    # wait for app-list to appear
    ui.WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id('app-list'))
    # validation successful validation-banner__title
    ui.WebDriverWait(driver, 10)

# Retrieve application details
def getInfo(driver, apps):
    apps_list = {}
    # get soup
    element = ui.WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id('tab--details'))
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # get title
    title = soup.findAll("h2", {"class": "more-information__name"})[0].decode_contents()
    apps_list["title"] = title
    # get image src
    for image in soup.findAll('img', {'class': 'more-information__icon'}):
        apps_list["image_url"] = "https://apps.mohawkcollege.ca" + image['src']
    # get app information
    count = 0
    # cycle through all the dd and split them into it's correct variable
    for item in soup.findAll("dd"):
        if count == 0:
            apps_list["vendor"] = item.decode_contents()
        if count == 1:
            apps_list["description"] = item.decode_contents()
        if count == 2:
            apps_list["categories"] = item.decode_contents()
        count += 1
    
    # get compatibility
    count = 0
    for item in soup.findAll('span', {'class': 'app-compatibility__item'}):
        if count == 0:
            apps_list["android"] = item['title']
        if count == 1:
            apps_list["ios"] = item['title']
        if count == 2:
            apps_list["linux"] = item['title']
        if count == 3:
            apps_list["macos"] = item['title']
        if count == 4:
            apps_list["windows"] = item['title']
        count += 1
        
    # get app requirement
    count = 0
    for item in soup.findAll('div', {'class': 'app-requirement'}):
        if count == 0:
            apps_list["domain"] = item['title']
        if count == 1:
            apps_list["offsite"] = item['title']
        if count == 2:
            apps_list["user_owned"] = item['title']
        if count == 3:
            apps_list["region"] = item['title']
        if count == 4:
            apps_list["availability"] = item['title']
        if count == 5:
            apps_list["any_devices"] = item['title']
        count += 1

    # click delivery method
    driver.find_element_by_id("tab--delivery-methods").click()
    element = ui.WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id('tab-panel--delivery-methods'))

    delivery = []
    deliverydictionary = {}
    # count for delivery variable name
    count = 1
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    # loop through all delivery methods
    while True:
        deliver_title = ""
        delivery_method = soup.findAll("a", {"id": re.compile('tab--delivery-method-' + str(count) + '')})
        # holds value for restrictions of delivery method
        restrictions = {}
        restriction_status = []
        restriction_titles = []
        # break out of loop if it's empty
        if not delivery_method:
            break
        else:
            # only append those not found in list
            if any(str(delivery_method[0].decode_contents()) in s for s in delivery):
                break
            # keep track of delivery method to avoid duplicates
            delivery.append(delivery_method[0].decode_contents())
            # get restriction title and restriction status
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            for item in soup.findAll('div', {'class': 'restriction__title'}):
                restriction_titles.append(item.decode_contents())
            for item in soup.findAll('strong', {'class': 'restriction__status'}):
                restriction_status .append(item.decode_contents())
            # add them to dictionary
            restriction_counter = 0
            for restriction in restriction_titles:
                if restriction_counter == 0:
                    restrictions["method"] = delivery_method[0].decode_contents()
                restrictions[restriction] = restriction_status[restriction_counter]
                restriction_counter += 1
            apps_list["delivery" + str(count)] = restrictions
            count += 1
    # append dictionary to given apps list
    apps.append(apps_list)

    # close details and wait
    driver.find_element_by_class_name("more-information-close").click()
    element = ui.WebDriverWait(driver, 10).until(lambda x: x.find_element_by_id('app-list'))


login(driver)
apps = []
# determine counter for More Info button
num_links = len(driver.find_elements_by_class_name('app-more-info'))

# check existing apps on Mohawk Apps - to be used to compare to json file
apps_name = []
soup = BeautifulSoup(driver.page_source, 'html.parser')
for item in soup.findAll('span', {'class': 'app__name'}):
    apps_name.append(item.decode_contents())

# open existing apps.txt file and check  if there's any update within Mohawk APPS
try:
    with open('apps.txt', 'r') as f:
        data =  json.load(f)

    # Get change in apps
    app_difference = []
    # Read existing apps.txt and count number of apps to compare to number of apps found on Mohawk APPS
    json_apps_name =  []
    jsonCounter = 0

    for d in data:
        if d["title"] != "":
            json_apps_name.append(d["title"])
            jsonCounter += 1
    # Run if there's inconsistency in json file and website
    if num_links != jsonCounter:
        # remove apps from json that doesn't exist on Mohawk APPS
        indices = []
        for i, d in enumerate(data):
            if d["title"] not in apps_name:
                indices.append(i)
                app_difference.append(d["title"])
        
        if len(indices) > 0:        
            for i in indices:
                del data[i]

        # add new apps found on Mohawk APPS to json
        for d in apps_name:
            if d not in json_apps_name:
                app_difference.append(d)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    indexOfApp = []
    # Get index of where json app is not found in Mohawk APPS
    count = 0
    for item in soup.findAll('button', {'class': 'app-more-info'}):
        if len(app_difference) > 0:
            for app in app_difference:
                if app in item.text:
                    indexOfApp.append(count)
        count += 1
    # Find app in Mohawk apps to get information
    for i in indexOfApp:
        button = driver.find_elements_by_class_name('app-more-info')[i]
        button.click()
        getInfo(driver, apps)
    # append to apps
    for a in apps:
        data.append(a)
        
    driver.quit()    
    # write to JSON
    s = json.dumps(data, indent=4)
    open("apps.txt", "w").write(s)

# If apps.txt does not exist, rescrape Mohawk APPS  to get data again - FULL OUT SCRAPE
except IOError as e:
    begin = 0
    while begin < num_links:
        # get more information 
        button = driver.find_elements_by_class_name('app-more-info')[begin]
        button.click()
        getInfo(driver , apps)
        begin += 1
    driver.quit()
    # write to JSON
    s = json.dumps(apps, indent=4)
    open("apps.txt", "w").write(s)
