import os
from bs4 import BeautifulSoup
import requests
from fast_autocomplete import AutoComplete
import csv
from pandas import DataFrame as df
from nltk.corpus import words
from fuzzywuzzy import fuzz
from nltk.stem import WordNetLemmatizer


def download(filename, url):
    if os.path.exists(os.path.join("career_files", filename)):
        return
    resp = requests.get(url)
    resp.raise_for_status()
    if ".html" in filename:
        doc = BeautifulSoup(resp.text, "html.parser")
        f = open(os.path.join("career_files", filename.lower()), "w", encoding="utf-8")
        f.write(str(doc))
        f.close()


def process_csv(filename):
    exampleFile = open(filename, encoding="utf-8")
    exampleReader = csv.reader(exampleFile)
    exampleData = list(exampleReader)
    exampleFile.close()
    return exampleData


def cell(row_idx, col_name):
    col_idx = csv_header.index(col_name)
    val = csv_data[row_idx][col_idx]
    return val


def url_gen(str_input):
    base_url = "https://www.mymajors.com/search/?q="

    if " " in str_input:
        parts = str_input.split(" ")
        for each in parts:
            if each == parts[-1]:
                base_url += each
            else:
                base_url += each + "+"
    else:
        base_url += str_input
    return base_url


def ret_list_careers(str_input, base_url):
    careers_found = []
    download("career_results" + str_input + ".html", base_url)
    f = open(os.path.join("career_files", "career_results" + str_input + ".html"), encoding="utf-8")
    html_text = f.read()
    f.close()
    soup = BeautifulSoup(html_text, "html.parser")
    all_h2 = soup.find_all("h2")
    flag = -1
    for each in all_h2:
        if each.get_text().lower() == "careers":
            flag = 0
            break
    if flag == -1:
        careers_found.append("no search results")
        return careers_found
    the_div = soup.find("div", {"class": "panel-body"})
    the_ul = the_div.find("ul")
    all_a = the_ul.find_all("a")
    for each_a in all_a:
        if "career" in each_a.get('href'):
            careers_found.append(each_a.get_text())
    return careers_found


def word_dic_gen(careers_found):
    download("comp_list.html", "https://www.mymajors.com/career-list/")
    all_careers = []
    f = open(os.path.join("career_files", "comp_list.html"), encoding="utf-8")
    html_text = f.read()
    f.close()
    soup = BeautifulSoup(html_text, "html.parser")
    all_li = soup.find_all("li", {"class": "leaf"})
    for each in all_li:
        all_careers.append(each.get_text().lower())
    career_words = {}
    for career in all_careers:
        career_words[career.lower()] = {}

    for each in careers_found:
        career_words[each.lower()] = {}

    return career_words


def ret_hit_list(str_input, careers_found):
    careers_words = word_dic_gen(careers_found)
    autocomplete = AutoComplete(words=careers_words)
    return autocomplete.search(word=str_input, max_cost=3, size=3)


def job_choices(str_input, careers_found):
    choices = []
    auto_list = ret_hit_list(str_input, careers_found)
    for each in auto_list:
        name_job = ""
        if type(each) == list:
            name_job = each[0]
        choices.append(name_job)

    # what if you layer it, autocomplete inside autocomplete yes/
    word_list = words.words()
    list_matches = []
    for one in str_input.split(" "):
        if one.lower() in word_list:
            continue
        all_words = {}
        # find a method to do this
        word_list.append("biomedical")
        for each in word_list:
            if each[0] == one[0]:
                all_words[each] = {}
        autocomplete = AutoComplete(words=all_words)
        list_matches.extend(autocomplete.search(word=one, max_cost=3, size=3))

    new_str = ""
    for each in list_matches:
        if type(each) == list:
            for every in str_input.split(" "):
                if len(new_str.split(" ")) == (len(str_input.split(" ")) + 1):
                    break
                if every.lower() in word_list:
                    new_str += every + " "
                    continue
                if fuzz.token_sort_ratio(every.lower(), each[0].lower()) > 80:
                    new_str += each[0].lower() + " "

    new_str = new_str.strip()
    new_matches = []
    if new_str != "":
        new_matches = ret_list_careers(new_str, url_gen(new_str))

    for each in new_matches:
        choices.append(each.lower())

    if "no search results" in choices:
        choices.remove("no search results")

    choices.sort()
    return choices


def which_job(choices):
    set_choices = set(choices)
    choices = list(set_choices)
    choices.sort()
    print("Choose a career from this list by entering a number from 1 -", len(choices))
    for i in range(len(choices)):
        print((i + 1), choices[i])
    # val = input()
    # remember to change
    # chosen = choices[int(val) - 1]
    return choices[0]


def ret_skill_list(job_selected):
    skills = []
    url_job_name = ""
    if " " in job_selected:
        parts = job_selected.split(" ")
        for each in parts:
            url_job_name += each + "-"
    else:
        url_job_name = job_selected
    download("skills" + url_job_name + ".html", "https://www.mymajors.com/career/" + url_job_name + "/skills/")
    f = open(os.path.join("career_files", "skills" + url_job_name + ".html"), encoding="utf-8")
    html_text = f.read()
    f.close()
    soup = BeautifulSoup(html_text, "html.parser")
    table = soup.find_all("tbody")
    for i in range(2):
        try:
            all_td = table[2 - i - 1].find_all("td")
        except IndexError:
            return "No skill information found"
        for each in all_td:
            if "-" in each.get_text():
                skills.append(each.get_text().split("-")[0].strip())

    return skills


def foi_skills(skills):
    filtered_skills = []
    imp_factor = 0
    imp_list = []
    for each in skills:
        if each in filtered_skills:
            continue
        if "and" in each:
            parts = each.split("and")
            filtered_skills.append(parts[0].strip() + parts[1])
        elif "of" in each:
            parts = each.split("of")
            filtered_skills.append(parts[0].strip() + parts[1])
        else:
            filtered_skills.append(each)
        imp_factor += 1
        imp_list.append(imp_factor)

    data = {"skill name": filtered_skills, "factor of importance": imp_list}
    df_skills = df(data)
    return df_skills


def ret_csv_data():
    csv_rows = process_csv("all_data.csv")
    header = csv_rows[0]
    data = csv_rows[1:]
    return header, data


def ret_lemmatized(in_string):
    lemmatizer = WordNetLemmatizer()
    final = ""
    if " " in in_string.lower():
        list_words = in_string.split(" ")
        for i in range(len(list_words)):
            lemma = lemmatizer.lemmatize(list_words[i])
            if lemma.strip()[-3:] == "ing":
                lemma = list_words[i][:-3]
            final += lemma + " "
        final = final.strip()
        return final
    else:
        final = lemmatizer.lemmatize(in_string)
        if final[-3:] == "ing":
            final = final[:-3]
        return final


def extract_code(cou):
    index = -1
    for char in cou:
        if char.isdigit():
            index = cou.index(str(char))
            break
    return cou[:index - 1]


def printCombination(arr, n, r):
    sel_words = []
    data = [0] * r
    combinationUtil(arr, data, 0, n - 1, 0, r, sel_words)
    return sel_words


def combinationUtil(arr, data, start, end, index, r, sel_words):
    if index == r:
        out = ""
        for j in range(r):
            out += (str(data[j]) + " ")
        sel_words.append(out.strip())
        return
    i = start
    while i <= end and end - i + 1 >= r - index:
        data[index] = arr[i]
        combinationUtil(arr, data, i + 1, end, index + 1, r, sel_words)
        i += 1


def return_groups(in_string):
    full_comb = []
    list_words = in_string.split(" ")
    num_words = len(list_words)
    for i in range(num_words):
        full_comb.extend(printCombination(list_words, len(list_words), i + 1))
    return full_comb


def grouper(str_input, list_ret):
    grouped = []
    for i in range(len(str_input.split(" "))):
        smaller = []
        for each in list_ret:
            if len(each.split(" ")) == i + 1:
                smaller.append(each)
            if smaller in grouped:
                continue
            grouped.append(smaller)
    return grouped


def list_all_combs(str_input):
    job_lemma = ret_lemmatized(str_input)
    list_ret = return_groups(job_lemma)
    all_comb = grouper(job_lemma, list_ret)
    return all_comb


def map_career_name(all_comb):
    list_fuzz = []
    prio = []
    list_c = []
    list_name = []
    # gotta check description too
    # see if you can extend this to the skill checker too
    for k in range(len(csv_data)):
        lemma_name = ret_lemmatized(cell(k, "Name").lower())
        for i in range(len(all_comb)):
            for word in all_comb[i]:
                flag = 0
                if " " not in word:
                    for each_word in lemma_name.split(" "):
                        if word in each_word:
                            flag = 1
                            break
                if flag == 1:
                    break
                for each_word in lemma_name.split(" "):
                    if fuzz.token_sort_ratio(word, each_word) > 85:
                        list_name.append(cell(k, "Name"))
                        list_c.append(cell(k, "Code"))
                        list_fuzz.append(fuzz.token_sort_ratio(word, each_word))
                        prio.append(len(all_comb) - i)
                if word in lemma_name:
                    list_name.append(cell(k, "Name"))
                    list_c.append(cell(k, "Name") + " " + cell(k, "Code"))
                    list_fuzz.append(fuzz.token_sort_ratio(word, lemma_name))
                    prio.append(len(all_comb) - i)
    #
    # dict_vals = {"course": list_c, "prio": prio, "list_fuzz": list_fuzz}
    # df_job = df(dict_vals)
    # df_job = df_job.sort_values(by=["prio", "list_fuzz"], ascending=[True, False])
    # return df_job
    return 


def remove_common(list_words):
    filtered = []
    common = []
    download("common.html", "https://www.rypeapp.com/most-common-english-words/")
    f = open(os.path.join("career_files", "common.html"), encoding="utf-8")
    text = f.read()
    f.close()
    soup = BeautifulSoup(text, "html.parser")
    all_td = soup.find_all("td")
    for each in all_td:
        common.append(each.get_text().split(" ")[1])
    for every in list_words:
        if not every.lower() in common:
            if every.lower()[-1:] == ";" or every.lower()[-1:] == ",":
                filtered.append(every.lower()[:-1])
                continue
            filtered.append(every.lower())
    return filtered


def map_career_desc(all_comb):
    list_c = []
    list_desc = []
    for i in range(len(csv_data)):
        list_desc.append(cell(i, "Description").lower())
    dict_df = {"Description": list_desc}
    df_desc = df(dict_df)

    for i in range(len(all_comb)):
        searchfor = []
        for word in all_comb[i]:
            searchfor.append(word)
        found = df_desc["Description"].str.contains('|'.join(searchfor))
        for j in range(len(found)):
            if found[j]:
                list_c.append(cell(j, "Name"))
    return list_c


tuple_csv = ret_csv_data()
csv_header = tuple_csv[0]
csv_data = tuple_csv[1]


def main():
    # BRILLIANT
    # MATCH WITH THE FIRST MATCH YOU HAVE WITH THE CAREER MATCH!! BRILLIANT
    # this is where the job goes
    str_input = "stock analyst"
    # careers_found = ret_list_careers(str_input, url_gen(str_input))
    # chosen = (which_job(job_choices(str_input, careers_found)))
    all_comb = list_all_combs(str_input)
    # df_job = map_career_name(all_comb)
    print(map_career_desc(all_comb))
    # skills = ret_skill_list(chosen)
    # if type(skills) == str:
    #     if skills.lower() == "no skill information found":
    #         return "we don't have the necessary information for this job. Pick another!"


print(main())
