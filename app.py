import datetime
import os

from flask import Flask, request, render_template
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html')


# Render HTML template after page loads so we can periodically update via AJAX
@app.route('/recent-comments')
def recent_comments():
    all_feedback = get_all_feedback()[:3]
    return render_template('comments.html', all_feedback=all_feedback)


@app.route('/all-comments')
def all_comments():
    all_feedback = get_all_feedback()
    return render_template('comments.html', all_feedback=all_feedback)


@app.route('/sms-webhook', methods=['POST'])
def sms_webhook():
    feedback = Feedback(
        message_id=request.form['messageId'],
        concat_ref=request.form.get('concat-ref', 0),
        concat_part=request.form.get('concat-part', 0),
        sender=request.form['msisdn'],
        comments=request.form['text'],
        message_timestamp=datetime.datetime.utcnow()
    )

    db.session.add(feedback)
    db.session.commit()
    return "Thanks for your comments"


def get_all_feedback():
    feedback_in_parts = Feedback.query.order_by('-id').all()
    all_feedback = []
    for feedback in feedback_in_parts:
        # Message is not concatenated
        if feedback.concat_ref is 0:
            all_feedback.append(feedback)

        # First concatenated message
        elif feedback.concat_part is 1:
            # Search the original list for the rest of the message and sort by the part.
            components = [component for component in feedback_in_parts if component.concat_ref is feedback.concat_ref]
            components.sort(key = lambda x: x.concat_part)

            # Concatenate all of the parts to the first part and add the first part to the feedback list.
            for component in components[1:]:
                components[0].comments += component.comments
            all_feedback.append(components[0])

    return all_feedback


"""
Model that represents the feedback information.
"""
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.String)
    concat_ref = db.Column(db.Integer)
    concat_part = db.Column(db.Integer)
    sender = db.Column(db.BigInteger)
    comments = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    message_timestamp = db.Column(db.DateTime)

    def __str__(self):
        return self.comments


if __name__ == '__main__':
    app.run()
