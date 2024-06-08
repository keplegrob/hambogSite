from flask import Flask
from flask import render_template
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
from dotenv import load_dotenv
import aiohttp
import asyncio
import pytz
from flask import jsonify

load_dotenv()

username = os.getenv('AC_USERNAME')
api_key = os.getenv('AC_KEY')

app = Flask(__name__)
app.secret_key = os.getenv('FLASKKEY')

headers = {
    "accept": "application/json",
}


### These three functions (generate_lastrun_timestamp, get_timestamp, and store_timestamp) are
# used to generate a timestamp the schedule was last updated, and/or store/load the schedule
# the last time it was updated.

def generate_lastrun_timestamp():
    # Get the current datetime
    current_datetime = datetime.now()
    # Convert the current datetime to Seattle timezone
    seattle_tz = pytz.timezone('America/Los_Angeles')
    current_datetime = current_datetime.astimezone(seattle_tz)
    # Format the datetime into the desired format
    formatted_datetime = current_datetime.strftime("%B %d %Y, %-I:%M %p")
    # Create the report string
    report = f"Last generated {formatted_datetime}"

    return report


def get_timestamp():
    try:
        with open('timestamp.txt', 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return 'N/A'


def store_timestamp():
    ts_now = generate_lastrun_timestamp()
    with open('timestamp.txt', 'w') as f:
        f.write(ts_now)


### START of Flask routing functions section BELOW
@app.route("/")
def home():
    return render_template('index.html')


@app.route("/vptwatcher.html")
@app.route("/vptwatcher")
def vpt():
    # Retrieve the timestamp from the session
    timestamp = get_timestamp()
    # func_last_run = session.get('func_last_run', 'N/A')
    return render_template('vptwatcher.html', timestamp=timestamp)


@app.route("/run_gargatron", methods=['POST'])
def run_gargatron():
    html_body = refresh_schedule()
    store_timestamp()
    timestamp = get_timestamp()
    with open('gargatron_output.html', 'w') as f:
        f.write(html_body)
    return jsonify({'html_body': html_body, 'timestamp': timestamp})


@app.route("/get_gargatron_output")
def get_gargatron_output():
    with open('gargatron_output.html', 'r') as f:
        html_body = f.read()
    return jsonify({'html_body': html_body})


### END of Flask routing section ABOVE

async def fetch(session, url):
    async with session.get(url) as response:
        return await response.json()


async def date_retrieval(trainer_id):
    dates_list = []
    # Get the current date
    now = datetime.now()
    # Format the current date to "yyyy-mm"
    current_month = now.strftime("%Y-%m")
    # Add one month to the current date
    next_month = (now + relativedelta(months=1)).strftime("%Y-%m")
    url = f"https://acuityscheduling.com/api/v1/availability/dates?month={current_month}&appointmentTypeID=3470658&calendarID={trainer_id}"
    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, api_key)) as session:
        async with session.get(url) as response:
            data = await response.json()
            for date in data:
                dates_list.append(date["date"])
    url = f"https://acuityscheduling.com/api/v1/availability/dates?month={next_month}&appointmentTypeID=3470658&calendarID={trainer_id}"
    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, api_key)) as session:
        async with session.get(url) as response:
            data = await response.json()
            for date in data:
                dates_list.append(date["date"])
    return dates_list


schedule_dump = []


async def trainer_schedule_retrieval(trainer_id, trainer_name):
    dates_list = await date_retrieval(trainer_id)
    async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(username, api_key)) as session:
        tasks = []
        for x in dates_list:
            url = f"https://acuityscheduling.com/api/v1/availability/times?date={x}&appointmentTypeID=3470658&calendarID={trainer_id}"
            tasks.append(fetch(session, url))
        responses = await asyncio.gather(*tasks)
        for response in responses:
            for x in response:
                x['trainer'] = trainer_name
                schedule_dump.append(x)


trainers = [
    (2407589, "Robert Wood"),
    (10042681, "Cody Novak"),
    (3012992, "Luke Besel"),
    (2609505, "Lisa Dimak"),
    (1294836, "Tyler Smith"),
    (1294851, "Kevin Anderson"),
    (1294854, "Kelli Wood"),
    (8405080, "April Kimmel"),
    (8405079, "Abbey Smith"),
    (9335645, "Zach Smith"),
    (1457187, "Josh Evans"),
    (1294839, "Lori Barber"),
    (7566793, "Josh Bond"),
    (1294860, "JJ Murphy"),
    (7566850, "Jared Klingenberg"),
    (1294848, "Darren Carrido"),
    (3008542, "Chris Warner"),
    (1294866, "Brittney Thornton"),
    (8059562, "Aaron Potoshnik"),
    (10178755, "Matt Pirie"),
    (9223905, "Serena Tedesco")
]

### this bit is to look up trainer ID for URL construction
# Convert the list of tuples to a dictionary
trainers_dict = {name: trainer_id for trainer_id, name in trainers}
# Function to get trainer ID from the dictionary
def get_trainer_id(trainer_name):
    return trainers_dict.get(trainer_name)


async def main():
    for trainer_id, trainer_name in trainers:
        await trainer_schedule_retrieval(trainer_id, trainer_name)


def refresh_schedule():
    asyncio.run(main())

    def get_date_time(entry):
        dt = datetime.strptime(entry['time'], "%Y-%m-%dT%H:%M:%S%z")
        return dt.date(), dt.time()

    sorted_schedule = sorted(schedule_dump, key=get_date_time)

    # Iterate through the sorted list

    # Initialize an empty list to store the HTML strings
    html_strings = []

    # Start the table
    html_strings.append("<table>")

    current_date = None
    for entry in sorted_schedule:

        dt = datetime.strptime(entry['time'], "%Y-%m-%dT%H:%M:%S%z")
        date_str = dt.strftime("%A - %B %d")
        if current_date != date_str:
            current_date = date_str
            html_strings.append(
                f"<tr><td colspan='1'><h4 style='margin-top:25px; margin-right:0; margin-bottom:0; margin-left:0;'>{dt.strftime('%A')}</h4></td>"

                f"<td colspan='1'><h4 style='margin-top:5px; margin-right:0; margin-bottom:0; margin-left:0;'></h4></td>"
                f"<td colspan='1'><h5 style='margin-top:20px; margin-right:0; margin-bottom:0; margin-left:0;'>{dt.strftime('%B %d')}</h5></td>"
                f"</tr>")

            html_strings.append(
                "<tr><td colspan='3'><hr style='border-top: 2px solid white; margin-top: 0; margin-bottom: 0;'></td></tr>")
        booking_url = f'https://vpt.as.me/schedule/92930363/appointment/3470658/calendar/{get_trainer_id(entry['trainer'])}/datetime/{entry['time']}'
        html_strings.append(
            f"<tr><td style='padding-right:15px;'>{entry['trainer']}</td> <td style='padding-left:10px; text-align: right'>{dt.strftime("%-I:%M %p")}</td> <td style='padding-left:15px;'><a href='{booking_url}'>Book it!</a></td></tr>")

    # End the table
    html_strings.append("</table>")
    html_body = '\n'.join(html_strings)
    print("Completed without error.")
    return html_body

### Comment out to run locally without Flask app is debugging/developing
# refresh_schedule()
