import os
from bs4 import BeautifulSoup
import requests
import csv


def download(filename, url):
    if os.path.exists(os.path.join("departments", filename)):
        return
    resp = requests.get(url)
    resp.raise_for_status()
    if ".html" in filename:
        doc = BeautifulSoup(resp.text, "html.parser")
        f = open(os.path.join("departments", filename), "w", encoding="utf-8")
        f.write(str(doc))
        f.close()


def download_all_departments():
    download("alpha.html", "https://guide.wisc.edu/courses/")
    f = open(os.path.join("departments", "alpha.html"), encoding="utf-8")
    html_text = f.read()
    f.close()
    soup = BeautifulSoup(html_text, "html.parser")
    div = soup.find_all("div", id="atozindex")
    div = div[0]
    head = "https://guide.wisc.edu"
    list_rest = []
    list_urls = []
    all_li = div.find_all("li")
    for each in all_li:
        tagaa = each.find("a")
        rest = tagaa.get("href")
        list_urls.append(head + rest)
        list_rest.append(rest)

    types = []
    for each in list_rest:
        text = each.split("/")[2]
        types.append(text)
    for i in range(len(list_urls)):
        download(types[i] + ".html", list_urls[i])
    return types


def split_slash(text):
    slashes = "/"
    if slashes in text:
        split_list = text.split(slashes)
        first = split_list[0]
        second = split_list[-1][-3:]
        text = first + " " + second
    return text


def ret_dict(filename):
    each_dict = {}
    f = open(os.path.join("departments", filename), encoding="utf-8")
    each_text = f.read()
    f.close()
    soup = BeautifulSoup(each_text, "html.parser")
    paras = soup.find_all("p", {"class": "courseblocktitle noindent"})
    for each_para in paras:
        span = each_para.find("span")
        text = span.get_text()
        text = text.replace(u'\xa0', u' ')
        text = split_slash(text)
        each_dict[text] = each_para.get_text().split("—")[1][1:]
    return each_dict


def write_classes(types):
    if not os.path.exists(os.path.join("all_text_files", "all_classes.txt")):
        all_list_courses = []
        for i in range(len(types)):
            all_list_courses.append(ret_dict(types[i] + ".html"))
        all_courses_list = []
        for each_dict in all_list_courses:
            for each_entry in each_dict:
                dict_entry = {}
                dict_entry[each_entry] = each_dict[each_entry]
                all_courses_list.append(dict_entry)
        f = open("all_classes.txt", "w", encoding="utf-8")
        for each_element in all_courses_list:
            f.write(list(each_element.keys())[0] + "\n")
        f.close()


def main():
    types = download_all_departments()
    write_classes(types)

main()