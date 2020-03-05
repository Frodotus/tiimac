import json
import os
import sys
import time
from datetime import datetime, timedelta

import rumps
from tiima import Tiima

API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxx"
COMPANY = "xxxxxxxx"
USERNAME = "xxxxxxxxx"
PASSWORD = "xxxxxxxxxx"

ICON_DIR = "icons"
TIMER_ICON = os.path.join(ICON_DIR, "timer.png")
TIMER_OFF_ICON = os.path.join(ICON_DIR, "timer_off.png")


class TiiMac(rumps.App):
    def __init__(self):
        super(TiiMac, self).__init__(
            "TiiMac",
            icon=TIMER_OFF_ICON,
            menu=[
                "Check in",
                "Check out",
                "To lunch",
                "From lunch",
                None,
                "Update hours",
                None,
            ],
        )
        self.tiima = Tiima(company_id=COMPANY, api_key=API_KEY)
        self.tiima.login(username=USERNAME, password=PASSWORD)
        self.refresh_counter = 0
        self.refresh()

    def refresh(self):
        print("refresh!")
        self.hours = self.tiima.workinghours()
        self.state = self.tiima.user_state()
        self.day_length = self.state.get("dayLength")
        self.work_delta = timedelta(seconds=self.day_length * 60)
        self.delta = self.work_delta
        now = datetime.now()
        current = now
        past = timedelta()
        last = now.replace(hour=0, minute=0, second=0, microsecond=0)
        hours = self.hours.get("hours")
        for h in hours:
            start = datetime.fromtimestamp(h.get("startTime"))
            end = datetime.fromtimestamp(h.get("endTime"))
            if last < end:
                last = end
            if start < now and end > now:
                current = start
            elif start < now:
                if h.get("addsHours") == True:
                    past = past + (end - start)
        if len(hours) > 0 and current == now:
            current = last
        self.wt = {"current": current, "past": past}
        self.work_delta = self.work_delta - self.wt.get("past")
        self.checkin = self.wt.get("current")
        self.render_state_bar(self)
        self.refresh_counter = 0

    @rumps.timer(60)
    def render_state_bar(self, sender):
        self.refresh_counter += 1
        if self.refresh_counter >= 60:
            self.refresh()
        now = datetime.now()
        time_left = timedelta()
        prefix = ""
        if self.state.get("statusCode") == "In":
            self.icon = TIMER_ICON
            end_date = self.checkin + self.work_delta
            if end_date > datetime.now():
                time_left = end_date - datetime.now()
            else:
                time_left = datetime.now() - end_date
                prefix = "+"
        else:
            self.icon = TIMER_OFF_ICON
            if self.work_delta > timedelta():
                time_left = self.work_delta
            else:
                time_left = -self.work_delta
                prefix = "+"

        self.title = "{} {}".format(prefix, ":".join(str(time_left).split(":")[0:2]))

    @rumps.clicked("Check in")
    def check_in(self, _):
        resp = self.tiima.user_enter()
        if resp.get("success") == True:
            rumps.notification("TiiMac", "Checked you in!", "")
        else:
            rumps.notification("TiiMac", "Couldn't check you in!", "")
        self.refresh()

    @rumps.clicked("Check out")
    def check_out(self, _):
        resp = self.tiima.user_leave()
        if resp.get("success") == True:
            rumps.notification("TiiMac", "Checked you out!", "")
        else:
            rumps.notification("TiiMac", "Couldn't check you out!", "")
        self.refresh()

    @rumps.clicked("To lunch")
    def to_lunch(self, _):
        resp = self.tiima.user_to_lunch()
        if resp.get("success") == True:
            rumps.notification("TiiMac", "Checked you out to lunch!", "")
        else:
            rumps.notification("TiiMac", "Couldn't check you out to lunch!", "")
        self.refresh()

    @rumps.clicked("From lunch")
    def from_lunch(self, _):
        resp = self.tiima.user_from_lunch()
        if resp.get("success") == True:
            rumps.notification("TiiMac", "Checked you back from lunch!", "")
        else:
            rumps.notification("TiiMac", "Couldn't check you back from lunch!", "")
        self.refresh()

    @rumps.clicked("Update hours")
    def update_hours(self, _):
        self.refresh()


def main(argv):
    TiiMac().run()


if __name__ == "__main__":
    main(sys.argv[1:])
