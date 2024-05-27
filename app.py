from flask import Flask
from flask import render_template
from flask import session
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService


from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import jsonify


#todo maybe later for organizaiton move static and templates
# in a folder called website in root

app = Flask(__name__)
app.secret_key = os.getenv('FLASKKEY')

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/vptwatcher.html")
def vpt():
    # Retrieve the timestamp from the session
    func_last_run = session.get('func_last_run', 'N/A')
    return render_template('vptwatcher.html', func_last_run=func_last_run)

@app.route("/run_gargatron", methods=['POST'])
def run_gargatron():
    now = datetime.now()
    func_last_run = now.strftime("%m/%d/%Y, %-I:%M %p")
    html_body = gargatron()
    with open('gargatron_output.html', 'w') as f:
        f.write(html_body)
    session['func_last_run'] = func_last_run

    return jsonify({'html_body': html_body, 'func_last_run': func_last_run})

@app.route("/get_gargatron_output")
def get_gargatron_output():
    with open('gargatron_output.html', 'r') as f:
        html_body = f.read()
    return jsonify({'html_body': html_body})


def gargatron():

    def get_trainer_id(name):
        # Create a dictionary mapping names to IDs
        # As new trainers are added, update this dictionary
        # To add a trainer, you will need to find their ID in the URL of their schedule
        # We use this function later to build the scheduling URL for the trainer
        name_to_id = {
            'Aaron Potoshnik': 8059562,
            'Abbey Smith': 8405079,
            'April Kimmel': 8405080,
            'Brittney Thornton': 1294866,
            'Chris Warner': 3008542,
            'Cody Novak': 10042681,
            'Darren Carrido': 1294848,
            'Jared Klingenberg': 7566850,
            'JJ Murphy': 1294860,
            'Josh Bond': 7566793,
            'Josh Evans': 1457187,
            'Kelli Wood': 1294854,
            'Kevin Anderson': 1294851,
            'Lisa Dimak': 2609505,
            'Lori Barber': 1294839,
            'Luke Besel': 3012992,
            'Matt Pirie': 10178755,
            'Robert Wood': 2407589,
            'Serena Tedesco': 9223905,
            'Tiff Kelley': 2351392,
            'Tyler Smith': 1294836,
            'Zach Smith': 9335645
        }
        # Use the dictionary to get the ID corresponding to the name
        trainer_id = name_to_id.get(name)
        return trainer_id



    def time_to_iso(time_str):
        # Parse the time string on the trainer's available appointment
        input_datetime = datetime.strptime(time_str + f" {datetime.today().year}", "%b %d %I:%M %p %Y")

        # Convert the datetime object to ISO 8601 format with timezone information
        iso_format_str = input_datetime.strftime("%Y-%m-%dT%H:%M:%S-07:00")

        # URL-encode the ISO format string
        encoded_iso_format_str = urllib.parse.quote(iso_format_str, safe='')

        # The final datetime URL part for construction in the individual appointment booking URL
        return encoded_iso_format_str


    def go_trainer_full():
        ## LOCAL TESTING SETTINGS
        #driver = webdriver.Chrome()
        ## END LOCAL TESTING SETTINGS




        ## REMOTE (HEROKU) SETTINGS
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        service = ChromeService(executable_path='/app/.chrome-for-testing/chromedriver-linux64/chromedriverls')
        driver = webdriver.Chrome(service=service, options=options)
        ## END REMOTE SETTINGS








        # Landing Page
        driver.get('https://vpt.as.me/schedule/92930363/appointment/3470658')


        # Wait until the page loads and trainers are visible
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-1ud922y')))

        # Get all links to each trainer's schedule by their CSS class element
        trainers = driver.find_elements(By.CLASS_NAME, 'css-1ud922y')


        # Loop through each trainer's schedule
        for i in range(len(trainers)):

            trainers = driver.find_elements(By.CLASS_NAME, 'css-1ud922y')

            # This if i == 0 is to skip the first link/schedule, which is a master schedule and not a trainer
            if i == 0:
                continue

            # Click on the trainer's schedule link
            trainers[i].click()

            # Wait until the page loads and the available slots are visible
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-vw844s')))

            # If the element is found, skip to the next iteration
            try:
                no_training = driver.find_element(By.CLASS_NAME, 'css-nppf68')

                driver.back()
                continue

            except NoSuchElementException:
                pass

            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-8evebl')))


            # get and print the dates
            daily_schedule_dates = driver.find_elements(By.CLASS_NAME, 'css-r80kbn')


            column_1_78gpzl_list = []
            column_2_91hgmg_list = []
            column_3_9qgxg6_list = []
            column_4_e7qfr2_list = []
            column_5_rnm8cy_list = []

            # Parse the HTML with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            trainer_name = soup.find('p', class_='css-1h8w7w6')
            trainer_name = trainer_name.text.replace("One on One Session with ", "")

            column_1_78gpzl_list.append(trainer_name)
            column_2_91hgmg_list.append(trainer_name)
            column_3_9qgxg6_list.append(trainer_name)
            column_4_e7qfr2_list.append(trainer_name)
            column_5_rnm8cy_list.append(trainer_name)

            # date css: css-r80kbn
            # the day css: css-vw844s

            # find all dates
            dates_elements_list = []
            dates_elements = driver.find_elements(By.CSS_SELECTOR, '.css-r80kbn') # This finds all the *dates*
            for date in dates_elements:
                dates_elements_list.append(date.text)

            # column1
            elements = driver.find_elements(By.CSS_SELECTOR, '.css-78gpzl .css-8evebl')
            for element in elements:
                column_1_78gpzl_list.append(element.text)
            try:
                first_date = dates_elements_list.pop(0)
                column_1_78gpzl_list.append(first_date)

            except:
                pass
            # column2
            elements = driver.find_elements(By.CSS_SELECTOR, '.css-91hgmg .css-8evebl')
            for element in elements:
                column_2_91hgmg_list.append(element.text)
            try:
                first_date = dates_elements_list.pop(0)
                column_2_91hgmg_list.append(first_date)
            except:
                pass

            # column3
            elements = driver.find_elements(By.CSS_SELECTOR, '.css-9qgxg6 .css-8evebl')
            for element in elements:
                column_3_9qgxg6_list.append(element.text)
            try:
                first_date = dates_elements_list.pop(0)
                column_3_9qgxg6_list.append(first_date)
            except:
                pass

            # column4
            elements = driver.find_elements(By.CSS_SELECTOR, '.css-e7qfr2 .css-8evebl')
            for element in elements:
                column_4_e7qfr2_list.append(element.text)
            try:
                first_date = dates_elements_list.pop(0)
                column_4_e7qfr2_list.append(first_date)
            except:
                pass

            # column5
            elements = driver.find_elements(By.CSS_SELECTOR, '.css-rnm8cy .css-8evebl')
            for element in elements:
                column_5_rnm8cy_list.append(element.text)
            try:
                first_date = dates_elements_list.pop(0)
                column_5_rnm8cy_list.append(first_date)

            except:
                pass

            # jam it all together
            all_slots.append(column_1_78gpzl_list)
            all_slots.append(column_2_91hgmg_list)
            all_slots.append(column_3_9qgxg6_list)
            all_slots.append(column_4_e7qfr2_list)
            all_slots.append(column_5_rnm8cy_list)

            driver.back()

            # We end up back at the main page, so we need to get the trainers each loop, incase the page has changed
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, 'css-1ud922y')))

            trainers = driver.find_elements(By.CLASS_NAME, 'css-1ud922y')

        return all_slots

        driver.quit()

    def send_email():
        # Load the environment variables from the .env file where email credentials are stored
        load_dotenv()

        # Email login credentials. These must be stored in a .env file in the same directory as this script
        # Gmail can generate an app password for this purpose; it is NOT your regular email password
        # EMAIL='email'
        # APP_PASSWORD='app password'
        sender = os.getenv('EMAIL')
        app_password = os.getenv('APP_PASSWORD')

        # Set the SMTP server and port
        smtp_server = 'smtp.gmail.com'
        smtp_port = 465

        # Set the sender's and recipients' email addresses
        recipients = ['bpsmith@gmail.com']

        # Set the email subject
        today = datetime.today()
        abbreviated_date = today.strftime('[%a, %b %d]')
        subject = f'VPT Availability {abbreviated_date}'

        # Create the email
        msg = MIMEMultipart()
        msg.attach(MIMEText(html_body, 'html'))

        msg['Subject'] = subject
        msg['From'] = 'VPT Watcher'
        msg['To'] = 'bpsmith@gmail.com, '.join(recipients)

        # Send the email
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender, app_password)
        server.sendmail(sender, recipients, msg.as_string())
        server.quit()

    # create a list to contain all the scraped data from VPT
    all_slots = []

    go_trainer_full()


    avail = []


    # This iterates through each list in the massive all_slots list of lists.
    # As it iterates, it is assigning elements of the list to variable names
    for sublist in all_slots:
        # this length check is in case a list has more than 3 elements, indicating the trainer has multiple slots that day
        if len(sublist) >= 3:
            name = sublist[0]
            date = sublist[-1]
            for time in sublist[1:-1]:
                avail.append([name, time, date])




    def parse_date_time(date_str, time_str):
        parsed_dt = datetime.strptime(f"{date_str} {time_str}", "%b %d %I:%M %p")
        parsed_dt = parsed_dt.replace(year=datetime.now().year)
        return parsed_dt


    # Create a list of (datetime, name) tuples
    entries = []
    for record in avail:
        name = record[0]
        time = record[1]
        date = record[2]
        dt = parse_date_time(date, time)
        iso_time = time_to_iso(f"{date} {time}")
        trainer_id = get_trainer_id(name)
        url = f'https://vpt.as.me/schedule/92930363/appointment/3470658/calendar/{trainer_id}/datetime/{iso_time}'
        entries.append((dt, name, time, url))

    # Sort the entries by datetime
    sorted_entries = sorted(entries, key=lambda x: x[0])


    # Initialize an empty list to store the HTML strings
    html_strings = []

    # Start the table
    html_strings.append("<table>")

    # Print the sorted list of slots
    current_date = None
    for dt, name, time, url in sorted_entries:
        date_str = dt.strftime("%A - %B %d")
        time_str = dt.strftime("%-I:%M %p")
        if current_date != date_str:
            current_date = date_str
            html_strings.append(
                f"<tr><td colspan='1'><h4 style='margin-top:25px; margin-right:0; margin-bottom:0; margin-left:0;'>{dt.strftime('%A')}</h4></td>"
                
                f"<td colspan='1'><h4 style='margin-top:15px; margin-right:0; margin-bottom:0; margin-left:0;'></h4></td>"
                f"<td colspan='1'><h5 style='margin-top:15px; margin-right:0; margin-bottom:0; margin-left:0;'>{dt.strftime('%B %d')}</h5></td>"
                f"</tr>")

            html_strings.append("<tr><td colspan='3'><hr style='border-top: 2px solid white;'></td></tr>")
        html_strings.append(
            f"<tr><td style='padding-right:15px;'>{name}</td> <td style='padding-left:10px; text-align: right'>{time_str}</td> <td style='padding-left:15px;'><a href='{url}'>Book it!</a></td></tr>")

    # End the table
    html_strings.append("</table>")

    # Join the list into a single string with '\n'.join()
    html_body = '\n'.join(html_strings)


    #send_email()
    print("Completed without error.")
    return html_body