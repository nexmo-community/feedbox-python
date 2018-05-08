import json
import os
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import aiy.audio
import aiy.voicehat


class FeedbackHook():
    def __init__(self):
        self.url = os.environ["WEBHOOK_URL"]
        self.url_receive = self.url + "/unread-comments-json"
        self.url_mark = self.url + "/mark-read"
        self.unread_messages = False

    def poll_endpoint(self):
        status_ui = aiy.voicehat.get_status_ui()
        while True:
            if self.unread_messages is False:
                response = urlopen(self.url_receive).read().decode("utf-8")
                feedbacks = json.loads(response)

                if len(feedbacks) > 0:
                    print("New Feedback Found, blink light.")
                    status_ui.status('thinking')
                    self.unread_messages = True
                else:
                    print("No feedback found checking agian in 10 seconds.")
                    time.sleep(10)
            else:
                aiy.voicehat.get_button().wait_for_press()
                self.button_action()
                status_ui.status("ready")

            def button_action(self):
                print('button pressed')
                response = urlopen(self.url_receive).read().decode("utf-8")
                feedbacks = json.loads(response)
                for feedback in feedbacks:
                    say(feedback['comment'])
                    request = Request(self.url_mark, urlencode({'id': feedback['id']}).encode())
                    urlopen(request).read()

                self.unread_messages = False


def say(words):
    aiy.audio.say(words, lang="en-GB", volume=10)


def main():
    FeedbackHook().poll_endpoint()


if __name__ == '__main__':
    main()
