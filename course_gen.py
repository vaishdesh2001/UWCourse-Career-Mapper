import os
from bs4 import BeautifulSoup
import requests
import csv
import pandas
from pandas import DataFrame as df
from fuzzywuzzy import fuzz
import time


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


def ret_csv_links():
    csv_rows = process_csv(os.path.join("app", "majors_links.csv"))
    header = csv_rows[0]
    data = csv_rows[1:]
    return header, data


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


def clean_up_text(text):
    unwanted_chars = ['\n', '\t', '\r', '\xa0', 'â\x80\x93']  # Edit this to include all characters you want to remove
    for char in unwanted_chars:
        text = text.replace(char, ' ')

    return text


def url_gen(str_input):
    base_url = "https://www.mymajors.com/career/"
    add = ""
    new = ""
    if "," in str_input:
        parts = str_input.split(",")
        for one in parts:
            add += one
    else:
        add = str_input
    spaces = add.split(" ")
    for part in spaces:
        new += part + "-"
    new = new[:-1]
    base_url += new + "/"
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
    download("skills" + url_job_name + ".html", url_gen(job_selected) + "skills/")
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


def extract_code(cou):
    index = -1
    for char in cou:
        if char.isdigit():
            index = cou.index(str(char))
            break
    return cou[:index - 1]


# learn to jump within a page
def gen_html(original, df_job, df_cc):
    # don't forget to add description
    # still gotta do skills
    start = ""
    f = open("allhtmlcode.txt", encoding="utf-8")
    start += f.read()
    f.close()
    start += """
    <div class="limiter">
    <div class="container-table100">
        <div class="wrap-table100">
            <div class="table100 ver1 m-b-110">
                <div class="table100-head">
                    <table>
                        <thead>
                        <tr class="row100 head">
                            <th class="cell100 column1">Course Code</th>
                            <th class="cell100 column2">Course Name</th>
                            <th class="cell100 column3">Course Description</th>
                        </tr>
                        </thead>
                    </table>
                </div>

                <div class="table100-body js-pscroll">
                <table>
    """
    for i in range(len(df_job)):
        start += "<tr>"
        start += "<td class='cell100 column1'>" + df_job.at[i, 'course'] + "    " + "</td>" + "<td class='cell100 " \
                                                                                              "column2'>" + \
                 df_job.at[i, 'name'] + "    " + "</td> "
        start += "<td class='cell100 column3'>" + df_job.at[i, 'description'] + "</td>" + "</tr>"
        if i == 15:
            break

    start += "</table>"
    start += """
                <a name="skills"></a>
                </div>
                </div>
            </div>
            </div>
        </div>
        """

    start += """
        <div class="limiter">
        <div class="container-table100">
            <div class="wrap-table100">
                <div class="table100 ver1 m-b-110">
                    <div class="table100-head">
                        <table>
                            <thead>
                            <tr class="row100 head">
                                <th class="cell100 column1">Course</th>
                                <th class="cell100 column2">Technical Skills</th>
                            </tr>
                            </thead>
                        </table>
                    </div>
    
                    <div class="table100-body js-pscroll">
                    <table>
        """
    for i in range(len(df_cc)):
        if i == 0:
            count = 0
            counter = df_cc.at[i, 'Skill']
        if counter == df_cc.at[i, 'Skill']:
            count += 1
        else:
            count = 0
            counter = df_cc.at[i, 'Skill']

        if count < 5:
            start += "<tr>"
            start += "<td class='cell100 column1'>" + df_cc.at[i, 'Course'] + "</td>"
            start += "<td class='cell100 column2'>" + df_cc.at[i, 'Skill'] + "</td>" + "</tr>"

    start += "</table>"
    start += """
            </div>
            </div>
        </div>
        </div>
    </div>
    </body>
    </html>"""
    f = open(os.path.join("", "app", "templates", original + "op.html"), "w", encoding="utf-8")
    f.write(start)
    f.close()


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
        # link = ""
        index = jobs.index(str_input)
        major = majors[index]
        if ":" in major:
            parts = major.split(":")
            major = parts[0] + parts[1]
        f = open(os.path.join("majors", major.lower() + ".html"), encoding="utf-8")
        h_text = f.read()
        f.close()
        soup = BeautifulSoup(h_text, "html.parser")
        all_a = soup.find_all("a", {'class': "bubblelink code"})
        for each in all_a:
            course_text = clean_up_text(each.get_text()).replace("\u200b", "")
            desc_text = get_desc_text(course_text)
            if desc_text is None:
                print(course_text, "None!")
                continue
            if course_text[-3:].isnumeric():
                if course_text[:2] == "or":
                    course.append(course_text[2:-3] + " " + course_text[-3:])
                else:
                    course.append(course_text[:-3] + " " + course_text[-3:])
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
        return df_courses[df_courses["fuzz"] > 30]
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

    for i in range(len(csv_data)):
        count = 0
        if cell(i, "Code")[:-4] in codes:
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
                c_name = (cell(i, "Name").lower())
                c_desc = (cell(i, "Description").lower())
                each = df_skills.at[j, "skill name"]
                if each.lower() in list_common:
                    continue
                each_lemma = (each.lower())
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


def gen_html_error(original):
    string = "<html><body><h1>Aw snap, couldn't fetch details for this job role, please <a href = " \
             "'https://vdflask.herokuapp.com/'>try another</a> one</h1></body></html> "
    f = open(os.path.join("", "app", "templates", original + "op.html"), "w", encoding="utf-8")
    f.write(string)
    f.close()


def main_career(job_selected):
    try:
        # nltk.data.path.append('./nltk_data/corpora/')
        df_courses = ret_all_courses(job_selected)
        codes = ret_main_codes(df_courses)
        if "" in codes:
            codes.remove("")
        df_script = search_name_codes(job_selected, codes)
        df_final = pandas.concat([df_courses, df_script])
        df_final = df_final.drop_duplicates(subset='course', keep="first")
        df_final = df_final.reset_index(drop=True)
        start = time.time()

        df_cc = map_skill_career(job_selected, codes)

        print("skill mapper")
        end = time.time()
        print(end - start)
        gen_html(job_selected, df_final, df_cc)
    except:
        gen_html_error(job_selected)

