# UW Course Career Mapper

A Python driven web application that maps relevant courses in UW-Madison to specific skills required for a given career.
https://vdflask.herokuapp.com/

## Description

This app accepts a career choice from the user to select specific courses in UW-Madison based on skills required for that job role. Given a career choice, the program looks up a list of relevant skills and then uses this information to search through UW-Madison courses to generate a list that would be helpful for students. This is something students can use to explore various options before they speak to a course advisor.

##  Getting Started 

This is a Flask application that runs on the Heroku platform. 
- In the root directory, wsgi.py, runtime.txt, requirements.txt, nltk.txt, Procfile are all the files required for the deployment of this Flask app. 
- Within the app directory, main.py is the Flask runner application 
  - all the front-end files(HTML, CSS and JS files) accessed by main.py are stored within the folder named static. The main html files are stored under the templates directory.
  - all files generated during the course of execution of the program are stored in the career_files folder and the templates folder
  - this flask app runs course_gen.py that runs the main part of the program like searching courses and generating an html file for output.
- course_gen.py contains the main search algorithm for displaying the courses(root directory)
  - course_gen.py utilizes data from all_data.csv, majors_links.csv, files under all_text_files and allhtmlcode.txt(root directory)
  
## Running the Code

To run this application from your local machine, navigate to the root directory and run this from the command line
```bash
python wsgi.py
```
Copy and paste the link displayed onto your browser.
The Course Career Mapper is up and running!

## Usage

Simply enter your career choice and hit enter!
