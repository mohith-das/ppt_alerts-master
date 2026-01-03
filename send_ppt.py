import os
from config import in_production
from slack_sdk import WebClient
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "replace_slack_bot_token")
SMTP_USERNAME = os.getenv("ALERT_SMTP_USERNAME", "your_smtp_username")
SMTP_PASSWORD = os.getenv("ALERT_SMTP_PASSWORD", "your_smtp_password")


def send_text_to_slack(text, location):
    # if not in_production:
    location = 'watchdog-test'

    client = WebClient(token=SLACK_BOT_TOKEN)

    response = client.chat_postMessage(
        channel=location,
        text=text
    )


def is_email(text):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    return (re.search(regex, text.split(',')[0]))


def send_mail(recipient, subject, message, cc='', type='plain', filepath=None):
    username = SMTP_USERNAME
    password = SMTP_PASSWORD
    # username = "vigilanceassets@sarasanalytics.com"
    # password = 'ApmV679B^QL$'
    msg = MIMEMultipart()
    msg['From'] = username
    msg['To'] = recipient
    msg['Cc'] = cc
    msg['Subject'] = subject
    msg.attach(MIMEText(message, type))
    if filepath:
        filename = filepath.split('/')[-1]
        attachment = open(filepath, "rb")
        p = MIMEBase('application', 'octet-stream')
        p.set_payload((attachment).read())
        encoders.encode_base64(p)
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
        msg.attach(p)
    try:
        print('sending mail to ' + recipient + ' on ' + subject)
        mailServer = smtplib.SMTP('smtp-mail.outlook.com', 587)
        # mailServer = smtplib.SMTP('smtp.gmail.com', 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(username, password)
        mailServer.sendmail(username, msg["To"].split(","), msg.as_string())
        mailServer.close()
    except Exception as e:
        print(f'Error sending mail regarding msg - "{message}"')
        raise RuntimeError(str(e))


def send_ppt_to_slack(filepath, message, location):
    client = WebClient(token=SLACK_BOT_TOKEN)

    if not in_production:
        location = 'watchdog-test'
        # location = 'pointstory-watchdog'

    location = location.strip()

    if filepath is None:
        if is_email(location):
            send_mail(recipient=location, subject=f"Watchdog - {message}", message='')
        else:
            response = client.chat_postMessage(channel=location, text=message)

    else:
        if is_email(location):
            send_mail(recipient=location, subject=f"Watchdog - {message}", message='', filepath=filepath)
        else:
            response = client.files_upload(channels=location, file=filepath, filetype='pptx', initial_comment=message)

