import os
from bs4 import BeautifulSoup
import requests
import csv
import pandas as pd
from pandas import DataFrame as df
from fuzzywuzzy import fuzz
import nltk
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


def ret_csv_data():
    csv_rows = process_csv(os.path.join(".", "app", "all_data.csv"))
    header = csv_rows[0]
    data = csv_rows[1:]
    return header, data


def ret_csv_codes():
    csv_rows = process_csv(os.path.join(".", "app", "Curricular subject areas with code.csv"))
    header = csv_rows[0]
    data = csv_rows[1:]
    return header, data


tuple_codes = ret_csv_codes()
codes_header = tuple_codes[0]
codes_data = tuple_codes[1]


tuple_csv = ret_csv_data()
csv_header = tuple_csv[0]
csv_data = tuple_csv[1]


def cell(row_idx, col_name):
    col_idx = csv_header.index(col_name)
    val = csv_data[row_idx][col_idx]
    return val


def cell_code(row_idx, col_name):
    col_idx = codes_header.index(col_name)
    val = codes_data[row_idx][col_idx]
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


def map_career_name(str_input):
    all_comb = list_all_combs(str_input)
    list_fuzz = []
    prio = []
    list_c = []
    list_name = []
    list_desc = []
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
                    if fuzz.token_sort_ratio(word, each_word) > 80:
                        list_name.append(cell(k, "Name"))
                        list_c.append(cell(k, "Code"))
                        list_desc.append(cell(k, "Description"))
                        list_fuzz.append(fuzz.token_sort_ratio(word, each_word))
                        prio.append(len(all_comb) - i)
                if word in lemma_name:
                    list_name.append(cell(k, "Name"))
                    list_c.append(cell(k, "Code"))
                    list_desc.append(cell(k, "Description"))
                    list_fuzz.append(fuzz.token_sort_ratio(word, lemma_name))
                    prio.append(len(all_comb) - i)

    dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "prio": prio, "list_fuzz": list_fuzz}
    df_job = df(dict_vals)
    df_job = df_job.sort_values(by=["prio", "list_fuzz"], ascending=[True, False])
    df_job = df_job.reset_index(drop=True)
    return df_job


def map_career_desc(str_input):
    list_c = []
    list_name = []
    list_desc = []
    list_fuzz = []
    prio = []
    skip_val = 0
    list_words = str_input.lower().split(" ")
    for i in range(len(csv_data)):
        lemma_name = ret_lemmatized(cell(i, "Description").lower())
        if len(list_words) > 1:
            if fuzz.token_sort_ratio(lemma_name.lower(), str_input) < 15:
                skip_val += 1
                continue
        list_lemma = lemma_name.split(" ")
        count = 0
        for every_desc in list_lemma:
            for each in list_words:
                if fuzz.token_sort_ratio(every_desc, each.lower()) > 80:
                    count += 1
            for each in list_words:
                if fuzz.token_sort_ratio(every_desc.lower(), each.lower()) > 80:
                    list_name.append(cell(i, "Name"))
                    list_c.append(cell(i, "Code"))
                    list_desc.append(cell(i, "Description"))
                    prio.append(count)
                    list_fuzz.append(fuzz.token_sort_ratio(every_desc.lower(), each.lower()))

    dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "prio": prio, "list_fuzz": list_fuzz}
    df_desc = df(dict_vals)
    df_desc = df_desc.sort_values(by=["prio", "list_fuzz"], ascending=[False, False])
    df_desc = df_desc.reset_index(drop=True)
    return df_desc


def map_career_codes(str_input):
    list_area = []
    list_abb = []
    list_desc = []
    list_fuzz = []
    prio = []
    skip_val = 0
    list_words = str_input.lower().split(" ")
    for i in range(len(codes_data)):
        lemma_name = ret_lemmatized(cell_code(i, "subject area").lower())
        if len(list_words) > 1:
            if fuzz.token_sort_ratio(lemma_name.lower(), str_input) < 15:
                continue
        list_lemma = lemma_name.split(" ")
        count = 0
        for every_code in list_lemma:
            for each in list_words:
                if fuzz.token_sort_ratio(every_code, each.lower()) > 80:
                    count += 1
            for each in list_words:
                if fuzz.token_sort_ratio(every_code.lower(), each.lower()) > 80:
                    list_abb.append(cell_code(i, "abbreviation"))
                    list_area.append(cell_code(i, "subject area"))
                    prio.append(count)
                    list_fuzz.append(fuzz.token_sort_ratio(every_code.lower(), each.lower()))

    dict_vals = {"abb": list_abb, "sub area": list_area, "prio": prio, "list_fuzz": list_fuzz}
    df_codes = df(dict_vals)
    df_codes = df_codes.sort_values(by=["prio", "list_fuzz"], ascending=[False, False])
    df_codes = df_codes.reset_index(drop=True)
    return df_codes


def map_code_df(str_input):
    list_c = []
    list_name = []
    list_desc = []
    prio = []
    df_codes = map_career_codes(str_input)
    main_codes = []
    if len(df_codes) > 0:
        for i in range(len(df_codes)):
            main_codes.append(df_codes.at[i, "abb"])
    if len(main_codes) > 0:
        count = 0
        for i in range(len(csv_data)):
            for j in range(len(main_codes)):
                if main_codes[j] in cell(i, "Code"):
                    list_name.append(cell(i, "Name"))
                    list_c.append(cell(i, "Code"))
                    list_desc.append(cell(i, "Description"))
                    prio.append(count)
                    count += 1
                    break

    dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "prio": prio}
    df_abbs = df(dict_vals)
    df_abbs = df_abbs.sort_values(by=["prio"], ascending=[True])
    df_abbs = df_abbs.reset_index(drop=True)
    return df_abbs


def gen_html(str_input, df_job):
    # don't forget to add description
    # still gotta do skills
    start = "<html><body><table><tr><th>course</th><th>name</th><th>description</th></tr>"
    for i in range(len(df_job)):
        start += "<tr>"
        start += "<td>" + df_job.at[i, 'course'] + "    " + "</td>" + "<td>" + df_job.at[i, 'name'] + "    " + "</td>"
        start += "<td>" + df_job.at[i, 'description'] + "</td>" + "</tr>"
        if i == 15:
            break

    start += "</table></body></html>"
    f = open(os.path.join(".", "app", "templates", str_input + "op.html"), "w", encoding="utf-8")
    f.write(start)
    f.close()


def main(job_selected):
    nltk.data.path.append('./nltk_data/corpora/')
    df_abbs = map_code_df(job_selected)
    df_job = map_career_name(job_selected)
    df_desc = map_career_desc(job_selected)
    if len(df_abbs) > 0:
        df_final = pd.concat([df_abbs, df_job, df_desc])
    else:
        df_final = pd.concat([df_job, df_desc])
    df_final = df_final.drop_duplicates(subset='course', keep="first")
    df_final = df_final.reset_index(drop=True)
    print(df_final)
    gen_html(job_selected, df_final)
    # BRILLIANT
    # MATCH WITH THE FIRST MATCH YOU HAVE WITH THE CAREER MATCH


main("aerospace engineer")
