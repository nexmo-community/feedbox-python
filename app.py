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
    all_feedback = Feedback.query.order_by('-id').limit(3).all()
    return render_template('comments.html', all_feedback = all_feedback)


@app.route('/all-comments')
def all_comments():
    all_feedback = Feedback.query.order_by('-id').all()
    return render_template('comments.html', all_feedback = all_feedback)


@app.route('/sms-webhook', methods=['POST'])
def sms_webhook():
    if int(request.form.get('concat-part', 0)) == 1 or bool(request.form.get('concat', False)) is False:
        feedback = Feedback(
            message_id=request.form['messageId'],
            sender=request.form['msisdn'],
            comments=request.form['text'],
            message_timestamp=datetime.datetime.utcnow()
        )

        db.session.add(feedback)
        db.session.commit()
        return "Thanks for your comments"
    return "Ignoring your message as it's too long"


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message_id = db.Column(db.String)
    sender = db.Column(db.BigInteger)
    comments = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    message_timestamp = db.Column(db.DateTime)

    def __str__(self):
        return self.comments


if __name__ == '__main__':
    app.run()
