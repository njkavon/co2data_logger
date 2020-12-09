__version__ = 0

import mh_z19
import time
import datetime
import subprocess
import sys


# what hour day starts, different measuring interval
day_start = 6
day_end = 22

# measuring interval, every nth minute synced to local time
day_r_rate = 15
night_r_rate = 60

# every alert level adds audible beep
alert1 = 1000
alert2 = 1100
alert3 = 1200

print_shell_output = False


def main():
    """Measure, log and check value against alerts set. At set nth minute."""
    while True:
        now = datetime.datetime.now()
        timestamp = now.strftime("%H:%M:%S %Y-%m-%d")
        rawvalue = mh_z19.read()
        # rawvalue = {"co2": 1200}  # debug value
        value = rawvalue["co2"]

        if print_shell_output:
            print(f"{value} CO2 at {timestamp}")

        # save measurement
        with open("co2data_log.csv", "a") as f:
            f.write(f"{timestamp}, {value}\n")

        check_alert(value)

        # measuring interval, every nth minute synced to local time
        if day_start <= now.hour < day_end:
            # print((day_r_rate - now.minute % day_r_rate))  # debug
            # time.sleep(5 - now.second % 5)  # debug refresh rate
            sleep_mins = day_r_rate - now.minute % day_r_rate
            time.sleep(sleep_mins * 60)
        else:
            sleep_mins = night_r_rate - now.minute % night_r_rate
            time.sleep(sleep_mins * 60)


def check_alert(value):
    """Check CO2 level and beep accordingly to alert levels set."""
    first_loop = True
    alerts = [alert1, alert2, alert3]
    for _ in alerts:
        if _ <= value:
            if print_shell_output and first_loop:
                print(f"The carbon dioxide level is at {value} ppm. Get ready for a sweet headache!")
            subprocess.Popen("(speaker-test -t sine -f 1000 -c 2 -s 1)& pid=$!; sleep 0.1; kill -9 $pid",
                             shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            first_loop = False
            time.sleep(0.5)


# to be able to continue without dependencies needed for webserver
try:
    import threading
    import pygal
    from flask import Flask
except ImportError as err:
    print(f"No webserver/plots, because of {str(err)[16:]} module is missing.")
    # sys.exit()
    print("Running only with shell & csv output with audible alerts.\n")
    if __name__ == "__main__":
        main()


app = Flask(__name__)


def flaskThread():
    app.run(debug=False, host="0.0.0.0", use_reloader=False)


@app.route("/")
def line_route():
    times, values = [], []
    with open("co2data_log.csv") as f:
        for row in f:
            times.append(row.strip().split(",")[0][:5])
            values.append(int(row.strip().split(",")[1]))
    chart = pygal.Line(legend_at_bottom=True, fill=False, x_label_rotation=90)
    chart.x_labels = times[-66:]
    chart.add("CO2", values[-66:], dots_size=2.5, show_only_major_dots=False)
    return chart.render_response()


if __name__ == "__main__":
    try:
        threading.Thread(target=flaskThread).start()
        main()
    except KeyboardInterrupt:
        sys.exit()  # when ctrl-c, end the program


# todo:
# make it run as service - autostart
# make reading from pi's serial port bundled in
# handle secs in intervals a little better
