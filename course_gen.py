import os
from bs4 import BeautifulSoup
import requests
import csv
import pandas
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
        f = open(os.path.join("app", "career_files", filename.lower()), "w", encoding="utf-8")
        f.write(str(doc))
        f.close()


def process_csv(filename):
    exampleFile = open(filename, encoding="utf-8")
    exampleReader = csv.reader(exampleFile)
    exampleData = list(exampleReader)
    exampleFile.close()
    return exampleData


def ret_csv_data():
    csv_rows = process_csv(os.path.join("app", "all_data.csv"))
    header = csv_rows[0]
    data = csv_rows[1:]
    return header, data


#
# def ret_csv_codes():
#     csv_rows = process_csv(os.path.join(app", "Curricular subject areas with code.csv"))
#     header = csv_rows[0]
#     data = csv_rows[1:]
#     return header, data


def ret_csv_links():
    csv_rows = process_csv(os.path.join("app", "majors_links.csv"))
    header = csv_rows[0]
    data = csv_rows[1:]
    return header, data


# tuple_codes = ret_csv_codes()
# codes_header = tuple_codes[0]
# codes_data = tuple_codes[1]

tuple_csv = ret_csv_data()
csv_header = tuple_csv[0]
csv_data = tuple_csv[1]

tuple_links = ret_csv_links()
link_header = tuple_links[0]
link_data = tuple_links[1]


def cell_link(row_idx, col_name):
    col_idx = link_header.index(col_name)
    val = link_data[row_idx][col_idx]
    return val


def cell(row_idx, col_name):
    col_idx = csv_header.index(col_name)
    val = csv_data[row_idx][col_idx]
    return val


# def cell_code(row_idx, col_name):
#     col_idx = codes_header.index(col_name)
#     val = codes_data[row_idx][col_idx]
#     return val


def clean_up_text(text):
    unwanted_chars = ['\n', '\t', '\r', '\xa0', 'â\x80\x93']  # Edit this to include all characters you want to remove
    for char in unwanted_chars:
        text = text.replace(char, ' ')

    return text


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
    f = open(os.path.join("", "app", "career_files", "skills" + url_job_name + ".html"), encoding="utf-8")
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


def gen_group_desc(string, str_input):
    num_words = len(str_input.split(" "))
    array = string.split(" ")


# def map_career_name(str_input):
#     all_comb = list_all_combs(str_input)
#     list_fuzz = []
#     prio = []
#     list_c = []
#     list_name = []
#     list_desc = []
#     for k in range(len(csv_data)):
#         lemma_name = ret_lemmatized(cell(k, "Name").lower())
#         for i in range(len(all_comb)):
#             for word in all_comb[i]:
#                 flag = 0
#                 if " " not in word:
#                     for each_word in lemma_name.split(" "):
#                         if word in each_word:
#                             flag = 1
#                             break
#                 if flag == 1:
#                     break
#                 for each_word in lemma_name.split(" "):
#                     if fuzz.token_sort_ratio(word, each_word) > 80:
#                         list_name.append(cell(k, "Name"))
#                         list_c.append(cell(k, "Code"))
#                         list_desc.append(cell(k, "Description"))
#                         list_fuzz.append(fuzz.token_sort_ratio(word, each_word))
#                         prio.append(len(all_comb) - i)
#                 if word in lemma_name:
#                     list_name.append(cell(k, "Name"))
#                     list_c.append(cell(k, "Code"))
#                     list_desc.append(cell(k, "Description"))
#                     list_fuzz.append(fuzz.token_sort_ratio(word, lemma_name))
#                     prio.append(len(all_comb) - i)
#
#     dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "prio": prio, "list_fuzz": list_fuzz}
#     df_job = df(dict_vals)
#     df_job = df_job.sort_values(by=["prio", "list_fuzz"], ascending=[True, False])
#     df_job = df_job.reset_index(drop=True)
#     return df_job


# def map_career_desc(str_input):
#     list_c = []
#     list_name = []
#     list_desc = []
#     list_fuzz = []
#     prio = []
#     skip_val = 0
#     list_words = str_input.lower().split(" ")
#     for i in range(len(csv_data)):
#         lemma_name = ret_lemmatized(cell(i, "Description").lower())
#         if len(list_words) > 1:
#             if fuzz.token_sort_ratio(lemma_name.lower(), str_input) < 15:
#                 skip_val += 1
#                 continue
#         list_lemma = lemma_name.split(" ")
#         count = 0
#         for every_desc in list_lemma:
#             for each in list_words:
#                 if fuzz.token_sort_ratio(every_desc, each.lower()) > 80:
#                     count += 1
#             for each in list_words:
#                 if fuzz.token_sort_ratio(every_desc.lower(), each.lower()) > 80:
#                     list_name.append(cell(i, "Name"))
#                     list_c.append(cell(i, "Code"))
#                     list_desc.append(cell(i, "Description"))
#                     prio.append(count)
#                     list_fuzz.append(fuzz.token_sort_ratio(every_desc.lower(), each.lower()))
#
#     dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "prio": prio, "list_fuzz": list_fuzz}
#     df_desc = df(dict_vals)
#     df_desc = df_desc.sort_values(by=["prio", "list_fuzz"], ascending=[False, False])
#     df_desc = df_desc.reset_index(drop=True)
#     return df_desc


# def map_career_codes(str_input):
#     list_area = []
#     list_abb = []
#     list_fuzz = []
#     prio = []
#     list_words = str_input.lower().split(" ")
#     for i in range(len(codes_data)):
#         lemma_name = ret_lemmatized(cell_code(i, "subject area").lower())
#
#         if len(list_words) > 1:
#             if fuzz.token_sort_ratio(lemma_name.lower(), str_input) < 15:
#                 continue
#         list_lemma = lemma_name.split(" ")
#         count = 0
#         for every_code in list_lemma:
#             for each in list_words:
#                 if fuzz.token_sort_ratio(every_code, each.lower()) > 80:
#                     count += 1
#             for each in list_words:
#                 if fuzz.token_sort_ratio(every_code.lower(), each.lower()) > 80:
#                     list_abb.append(cell_code(i, "abbreviation"))
#                     list_area.append(cell_code(i, "subject area"))
#                     prio.append(count)
#                     list_fuzz.append(fuzz.token_sort_ratio(every_code.lower(), each.lower()))
#
#     dict_vals = {"abb": list_abb, "sub area": list_area, "prio": prio, "list_fuzz": list_fuzz}
#     df_codes = df(dict_vals)
#     df_codes = df_codes.sort_values(by=["prio", "list_fuzz"], ascending=[False, False])
#     df_codes = df_codes.reset_index(drop=True)
#     return df_codes
#
#
# def map_code_df(str_input):
#     list_c = []
#     list_name = []
#     list_desc = []
#     prio = []
#     df_codes = map_career_codes(str_input)
#     main_codes = []
#     if len(df_codes) > 0:
#         for i in range(len(df_codes)):
#             main_codes.append(df_codes.at[i, "abb"])
#     if len(main_codes) > 0:
#         count = 0
#         for i in range(len(csv_data)):
#             for j in range(len(main_codes)):
#                 if main_codes[j] in cell(i, "Code"):
#                     list_name.append(cell(i, "Name"))
#                     list_c.append(cell(i, "Code"))
#                     list_desc.append(cell(i, "Description"))
#                     prio.append(count)
#                     count += 1
#                     break
#
#     dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "prio": prio}
#     df_abbs = df(dict_vals)
#     df_abbs = df_abbs.sort_values(by=["prio"], ascending=[True])
#     df_abbs = df_abbs.reset_index(drop=True)
#     return df_abbs


# learn to jump within a page
def gen_html(original, df_job, df_cc):
    # don't forget to add description
    # still gotta do skills
    start = """<html>
                    <body>
                        <h1>Click <a href="#skills">here</a> to get skills-related courses</h1>
                        <table>
                            <tr>
                                <th>course</th>
                                <th>name</th>
                                <th>description</th>
                            </tr>"""
    for i in range(len(df_job)):
        start += "<tr>"
        start += "<td>" + df_job.at[i, 'course'] + "    " + "</td>" + "<td>" + df_job.at[i, 'name'] + "    " + "</td>"
        start += "<td>" + df_job.at[i, 'description'] + "</td>" + "</tr>"

    start += '</table> <a name="skills"></a>'
    start += """<table>
                    <tr>
                        <th>course</th>
                        <th>skills</th>
                    </tr>"""
    for i in range(len(df_cc)):
        start += "<tr>"
        start += "<td>" + df_cc.at[i, 'Course'] + "    " + "</td>"
        start += "<td>" + df_cc.at[i, 'Skill'] + "</td>" + "</tr>"
    start += "</table>"

    start += """        
                    </body>
                </html>"""
    f = open(os.path.join("", "app", "templates", original + "op.html"), "w", encoding="utf-8")
    f.write(start)
    f.close()


# def remove_and(str_input):
#     words = str_input.split(" ")
#     new_word = ""
#     for each in words:
#         if each[-4:] == "ists":
#             new_word += each[:-4] + " "
#         else:
#             new_word += each + " "
#     str_input = new_word
#
#     if "and" in words:
#         split = str_input.split("and")
#         str_input = split[0].strip() + " " + split[1].strip()
#     return str_input


def get_desc_text(course_code):
    if "/" in course_code:
        course_code = course_code.split("/")[-1]
    if course_code[-5:-3] == "  ":
        course_code = course_code[:-4] + course_code[-3:]
    for i in range(len(csv_data)):
        if course_code.lower() in cell(i, "Code").lower():
            return cell(i, "Name")


def ret_all_courses(str_input):
    f = open(os.path.join("", "app", "all_text_files", "list_careers.txt"), "r", encoding="utf-8")
    all_text = f.read()
    f.close()
    list_lines = all_text.split("\n")
    jobs = []
    majors = []
    for each in list_lines:
        parts = each.split("*")
        if len(parts) == 2:
            job = parts[0].strip()
            jobs.append(job)
            major = parts[1].strip()
            majors.append(major)

    if str_input in jobs:
        course = []
        desc = []
        list_desc = []
        fuzzy = []
        link = ""
        index = jobs.index(str_input)
        major = majors[index]
        for i in range(len(link_data)):
            if cell_link(i, "majors").lower() == major.lower():
                link = cell_link(i, "links")
                break
        download(str_input + ".html", link + "#requirementstext")
        f = open(os.path.join("", "app", "career_files", str_input + ".html"), encoding="utf-8")
        h_text = f.read()
        f.close()
        soup = BeautifulSoup(h_text, "html.parser")
        all_a = soup.find_all("a", {'class': "bubblelink code"})
        for each in all_a:
            course_text = clean_up_text(each.get_text()).replace("\u200b", "")
            if course_text[-3:].isnumeric():
                if course_text[:2] == "or":
                    course.append(course_text[2:-3] + " " + course_text[-3:])
                else:
                    course.append(course_text[:-3] + " " + course_text[-3:])
                desc_text = get_desc_text(course_text)
                if desc_text is None:
                    print(course_text, "None!")
                desc.append(desc_text)
                fuzzy.append(fuzz.token_sort_ratio(str_input, desc_text))
        for i in range(len(desc)):
            flag = 1
            for j in range(len(csv_data)):
                if cell(j, "Name").lower() in desc[i].lower():
                    flag = 0
                    list_desc.append(cell(j, "Description"))
                    break
            if flag == 1:
                list_desc.append("no desc found")
        dict_vals = {"course": course, "name": desc, "description": list_desc, "fuzz": fuzzy}
        df_courses = df(dict_vals)
        df_courses = df_courses.sort_values(by=["fuzz"], ascending=[False])
        df_courses = df_courses.reset_index(drop=True)
        df_courses = df_courses.drop_duplicates(subset=["course"], keep="first")
        df_courses = df_courses.reset_index(drop=True)
        return df_courses[df_courses["fuzz"]>30]
    else:
        print("job not in jobs list")


def ret_main_codes(df_courses):
    codes = []
    for i in range(len(df_courses)):
        text = df_courses.at[i, "course"].strip()
        if "&" in text or "/" in text:
            if "&" in text:
                parts = text.split("&")
                for each in parts:
                    if each.strip()[-3:].isnumeric():
                        codes.append(each.strip()[:-3].strip())
                    else:
                        codes.append(each.strip())
            if "/" in text:
                sections = text.split("/")
                for every in sections:
                    codes.append(every.strip())
        elif text[-3:].isnumeric():
            codes.append(text[:-3].strip())
    for one in codes:
        if one[-3:].isnumeric():
            codes.append(one[:-3].strip())
            codes.remove(one)
    set_c = set(codes)
    codes = list(set_c)
    return codes


def search_name_codes(str_input, codes):
    list_c = []
    list_name = []
    list_desc = []
    list_fuzz = []
    prio = []

    for each in codes:
        for i in range(len(csv_data)):
            count = 0
            if each in cell(i, "Code"):
                for every in str_input.split(" "):
                    for one in cell(i, "Description").split(" "):
                        if fuzz.token_sort_ratio(one, every) > 85:
                            count += 1
            if count > 0:
                list_c.append(cell(i, "Code"))
                list_name.append(cell(i, "Name"))
                list_desc.append(cell(i, "Description"))
                list_fuzz.append(fuzz.token_sort_ratio(cell(i, "Description"), str_input))
                prio.append(count)

    dict_vals = {"course": list_c, "name": list_name, "description": list_desc, "fuzz": list_fuzz, "prio": prio}
    df_script = df(dict_vals)
    df_script = df_script.sort_values(by=["prio", "fuzz"], ascending=[False, False])
    df_script = df_script.reset_index(drop=True)
    return df_script


def map_skill_career(str_input, codes):
    list_hits = []
    list_common = ["mathematics", "speaking", "writing", "critical thinking", "reading comprehension",
                   "english language", "time management", "complex problem solving"]
    list_codes = []
    df_skills = foi_skills(ret_skill_list(str_input))
    for j in range(len(df_skills)):
        for i in range(len(csv_data)):
            if cell(i, "Code")[:-4] in codes:
                c_name = ret_lemmatized(cell(i, "Name").lower())
                c_desc = ret_lemmatized(cell(i, "Description").lower())
                each = df_skills.at[j, "skill name"]
                if each.lower() in list_common:
                    continue
                each_lemma = ret_lemmatized(each.lower())
                each_list = each_lemma.split(" ")
                count_name = 0
                count_desc = 0
                for k in range(len(each_list)):
                    if each_list[k].lower() in c_name:
                        count_name += 1
                for k in range(len(each_list)):
                    if each_list[k].lower() in c_desc:
                        count_desc += 1

                sum_count = count_desc + count_name
                if sum_count == 0:
                    continue
                if len(each_list) > 1 and sum_count == 1:
                    continue
                list_hits.append("#" + each)
                list_hits.append(cell(i, "Code") + " " + cell(i, "Name"))
                list_codes.append(count_name + count_desc)
    only_courses = []
    skills_mapped = []
    foi_skill_list = []
    for i in range(len(list_hits)):
        if i % 2 == 1:
            only_courses.append(list_hits[i])
        else:
            skills_mapped.append(list_hits[i][1:])

    for skill in skills_mapped:
        ix = df_skills[df_skills["skill name"] == skill].index.values
        foi_skill_list.append(df_skills.at[int(ix[0]), "factor of importance"])
    dict_val = {"Course": only_courses, "Priority Val": list_codes, "Skill": skills_mapped, "foi": foi_skill_list}
    df_cc = df(dict_val)
    df_cc = df_cc.sort_values("foi", ascending=True)
    return df_cc


def main_career(job_selected):
    nltk.data.path.append('./nltk_data/corpora/')
    df_courses = ret_all_courses(job_selected)
    codes = ret_main_codes(df_courses)
    df_script = search_name_codes(job_selected, codes)
    df_final = pandas.concat([df_courses, df_script])
    df_final = df_final.drop_duplicates(subset='course', keep="first")
    df_final = df_final.reset_index(drop=True)
    df_cc = map_skill_career(job_selected, codes)
    gen_html(job_selected, df_final, df_cc)


main_career("cryptographer")
