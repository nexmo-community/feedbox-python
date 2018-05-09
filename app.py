import datetime
import os

from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


@app.route('/')
def index():
    return render_template('index.html', phone_number=os.environ['PHONE_NUMBER'])


@app.route('/recent-comments-json')
def resent_comments_json():
    recent_comments = get_all_feedback()
    return jsonify(extract_feedback_properties(recent_comments))


@app.route('/unread-comments-json')
def unread_comments_json():
    unread_comments = get_all_unread_feedback()
    return jsonify(extract_feedback_properties(unread_comments))


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


@app.route('/mark-read', methods=['POST'])
def mark_read():
    feedback = Feedback.query.filter_by(id=request.form['id']).first()
    if feedback.concat_ref is 0:
        feedback.read = True
    else:
        related_feedback = Feedback.query.filter_by(concat_ref=feedback.concat_ref).all()
        for related in related_feedback:
            related.read = True

    db.session.commit()
    return "Message %s marked read." % request.form['id']


def get_all_feedback():
    all_feedback = Feedback.query.order_by('id desc').all()
    return concatenate_feedback(all_feedback)


def get_all_unread_feedback():
    all_unread_feedback = Feedback.query.order_by('id desc').filter_by(read=False).all()
    return concatenate_feedback(all_unread_feedback)


def concatenate_feedback(feedbacks):
    all_feedback = []
    for feedback in feedbacks:
        # Message is not concatenated
        if feedback.concat_ref is 0:
            all_feedback.append(feedback)

        # First concatenated message
        elif feedback.concat_part is 1:
            # Search the original list for the rest of the message and sort by the part.
            components = [component for component in feedbacks if component.concat_ref is feedback.concat_ref]
            components.sort(key=lambda x: x.concat_part)

            # Concatenate all of the parts to the first part and add the first part to the feedback list.
            for component in components[1:]:
                components[0].comments += component.comments
            all_feedback.append(components[0])

    return all_feedback


def extract_feedback_properties(feedbacks):
    output_feedback = []
    for feedback in feedbacks:
        output_feedback.append(
            {
                'id': feedback.id,
                'comment': feedback.comments,
                'message_timestamp': str(feedback.message_timestamp),
                'read': feedback.read
            }
        )
    return output_feedback


class Feedback(db.Model):
    """
    Model that represents the feedback information.
    """
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
