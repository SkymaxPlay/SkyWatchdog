import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from smtplib import SMTP_SSL, SMTP

from app.objects.task import Task
from app.utils import dtutils

server = None
port = None
ssl = None
user = None
password = None
recipients = []
templates = {}


def setup(configuration):
    global server, port, ssl, user, password, recipients, templates

    server = configuration.get("server")
    port = configuration.get("port")
    ssl = configuration.get("ssl")
    user = configuration.get("user")
    password = configuration.get("password")
    recipients = configuration.get("recipients")
    templates = configuration.get("templates")


def send_mail(subject, content):
    msg = MIMEMultipart()
    msg['From'] = "SkyWatchdog <%s>" % user
    msg['To'] = ";".join(recipients)
    msg['Subject'] = subject
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg.attach(MIMEText(content, 'plain', "utf-8"))

    constructor = SMTP_SSL if ssl else SMTP

    with constructor(server, port) as conn:
        conn.login(user, password)
        conn.set_debuglevel(False)
        conn.sendmail(user, recipients, msg.as_string())


def send_system_started_mail():
    template = templates.get("on-startup")

    if template is None:
        return

    subject = replace_placeholders(template.get("subject", ""))
    content = replace_placeholders(template.get("content", ""))

    send_mail(subject, content)


def send_notify_mail(task: Task):
    template = templates.get("on-task-error" if task.last_check_good else "on-task-rescued")

    if template is None:
        return

    subject = replace_placeholders(template.get("subject", ""), task)
    content = replace_placeholders(template.get("content", ""), task)

    send_mail(subject, content)


def replace_placeholders(msg, task: Task = None):
    if isinstance(msg, list):
        msg = "\n".join(msg)

    return msg \
        .replace("{NAME}", task.name if task else "") \
        .replace("{TIME}", dtutils.format_dt()) \
        .replace("{RESCUE-ENABLED}", "Tak" if task and task.rescue_mode_enabled() else "Nie")
