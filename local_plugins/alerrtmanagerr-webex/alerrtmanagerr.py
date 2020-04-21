import string

from errbot import BotPlugin, webhook
from datetime import datetime
import pytz
import string
import iso8601
import requests


alert_call = 'https://devops-api-prod.toolsfdg.net/alertmanager'


def date_convert(date):
    datetime_obj = iso8601.parse_date(date)
    shanghai_tz = pytz.timezone("Asia/Shanghai")
    return datetime_obj.astimezone(shanghai_tz).strftime('%Y-%m-%d %H:%M:%S')


def divide_chunks(alert_list, n):
    for i in range(0, len(alert_list), n):
        yield alert_list[i:i + n]


def alert_message(alerts):
    text = ''
    for alert in alerts:
        title = string.capwords(alert['labels']['alertname'])
        ends_str = ''
        if 'severity' in alert['labels']:
            title_str = F"#### {title} - " \
                        F"{alert['labels']['severity']} \n"
        else:
            title_str = F"#### {title} \n"
        details = "#### Details: \n"
        if 'job' in alert['labels']:
            job_str = f"> Job: {alert['labels']['job']} \n"
        else:
            job_str = ''
        starts_str = f"> StartsAt: {date_convert(alert['startsAt'])} CST \n"
        if 'description' in alert['annotations']:
            des_str = f"**Description**: ```{alert['annotations']['description']}``` \n"
        else:
            des_str = ""
        if 'instance' in alert['labels']:
            instance_str = f"> Instance: {alert['labels']['instance']} \n"
        else:
            instance_str = ''
        if alert['status'] == 'firing':
            status_str = f"### [{alert['status'].capitalize()}] 🔥 \n"
        else:
            status_str = f"### [{alert['status'].capitalize()}] 😁 \n"
            ends_str = F"> EndsAt: {date_convert(alert['endsAt'])} CST"
        if 'graph' in alert['annotations']:
            graph_str = f"**Graph**: [Link]({alert['annotations']['graph']}) \n"
        else:
            graph_str = ''

        text = text + '\n' + status_str + title_str + des_str + graph_str + details \
               + job_str + instance_str + starts_str + ends_str

    if alerts[0]['status'] == 'firing':
        if 'phone_call' in alerts[0]['labels']:
            for phone in alerts[0]['labels']['phone_list'].split():
                r = requests.get(url=f"{alert_call}?call={phone}&msg={alerts[0]['labels']['phone_msg']}")

    return text


class AlerrtmanagerrWebex(BotPlugin):
    """
    Get alerts from Prometheus Alertmanager via webhooks
    """
    @webhook('/alerrt-webex/<recipient>/<server>/')
    def alerrt(self, data, recipient, server):
        identifier = self.build_identifier(recipient + "@" + server)
        for alert in data['alerts']:
            if 'description' in alert['annotations']:
                title = alert['annotations']['description']
            else:
                title = alert['annotations']['message']
            self.send_card(
                to=identifier,
                summary='[{}] {}'.format(
                    data['status'].upper(),
                    alert['labels']['alertname']
                ),
                title=title,
            )

    @webhook('/alerrt-webex-room/<room>/')
    def alerrtt(self, data, room):
        identifier = self.query_room(room)
        if len(data['alerts']) > 10:
            alert_list = divide_chunks(data['alerts'], 10)
            for alert in alert_list:
                text = alert_message(alert)
                self.send(identifier, text=text)
        else:
            text = alert_message(data['alerts'])
            self.send(identifier, text=text)


