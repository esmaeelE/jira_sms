"""
Middle server that listen to receive data from jira server and
send sms to appropriate contact to inform him/her
created issues.
"""

from send_sms import init_gsm_modem
from flask import Flask, render_template, request
import json
from read_user import get_lookup_number
from send_sms import send_sms_to_number

import logging
import logging.config
import yaml

with open('/home/jira_sms/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

app = Flask(__name__)


def effify(non_f_str: str):
    """convert field to actual string"""
    return eval(f'f"""{non_f_str}"""')


def is_behzad(project_name):
    """
    send technical project for behzad
    """
    lst = ["test project"]
    if project_name in lst:
        return True


def get_number(name):
    """get number corresponding for name"""
    lookup_number = get_lookup_number()
    return lookup_number.get(name)


def get_self_user(json_request):
    """return name of user that change issue"""
    if json_request.get('user'):
        return json_request.get('user').get('self')


def get_uniq_audience(my_data):
    """return only uniq names"""

    audience = set()

    # if my_data.get('user'):
    #     user_name = my_data.get('user').get('name')
    #     audience.add(user_name)

    if my_data.get('issue'):

        project_name = my_data.get('issue').get(
            'fields').get('project').get('name')
        issue_creator = my_data.get('issue').get(
            'fields').get('creator').get('name')
        issue_reporter = my_data.get('issue').get(
            'fields').get('reporter').get('name')
        issue_assignee = my_data.get('issue').get(
            'fields').get('assignee').get('name')
        if issue_creator:
            audience.add(issue_creator)
        if issue_reporter:
            audience.add(issue_reporter)
        if issue_assignee:
            audience.add(issue_assignee)
        if project_name:
            if is_behzad(project_name):
                audience.add('b.khoshbakht')

    return audience


def get_issue_key(json_request):
    """return uniq KEY for each issue"""
    issue_key = ""
    if json_request.get('issue'):
        issue_key = json_request.get('issue').get('key')
        return issue_key


def get_duedate(json_resquest):
    """return issue due date"""
    if json_resquest.get('issue'):
        return json_resquest.get('issue').get('fields').get('duedate')


def get_issue_summary(json_request):
    """name of issue title in jira is, summary"""
    if json_request.get('issue'):
        return json_request.get('issue').get('fields').get('summary')


def get_issue_priority(json_request):
    """issue priority"""
    if json_request.get('issue'):
        issue_priority = json_request.get('issue').get(
            'fields').get('priority').get('name')
        return (issue_priority.upper())


def get_emoji(value):
    """emoji"""
    a = {
        'NEW ISSUE': '',
        'UPDATE ISSUE': '❗',
        '': '',
        '': ''
    }
    return a.get(value)


def get_issue_type(value):
    """simple lookup table for issue type"""
    issue_type = {
        'issue_created': 'NEW ISSUE',

        'issue_updated': 'UPDATE ISSUE',

        'issue_commented': 'COMMENT',
        'issue_comment_edited': 'COMMENT_EDITED',
        'issue_comment_deleted': 'COMMENT_DELETED',

        'issue_assigned': 'REASSIGNED',
        'issue_generic': 'UPDATE STATUS'
    }
    if issue_type.get(value) == 'UPDATE ISSUE':
        return get_emoji('UPDATE ISSUE') + issue_type.get(value)
        #  issue_type.get(value)
    return issue_type.get(value)


def get_url(json_request, issue_key):
    """construct issue url as json request not send it"""
    user_self = get_self_user(json_request)
    # # construct correct issue url by parsing json
    if user_self:
        # base_url = user_self[7:].split('/')[0]
        base_url = "http://jira.bonyansystem.com:18009"
        task_url = base_url+'/browse/' + issue_key
        return task_url
    else:  # get from comment
        return None

# [TODO]: removeCOMMENT


def get_changelog(json_request):
    """empty description"""
    if json_request.get('changelog'):
        items = json_request.get('changelog').get('items')
        if items:
            for item in items:
                print("***get changes***", item.get('field'),
                      item.get('toString'))


def get_status(json_request, event):
    """return status """

    if event == 'NEW ISSUE' or 'COMMENT' in event or event == 'REASSIGNED':
        ret = json_request.get('issue').get('fields').get('status').get('name')
        return ret

    if json_request.get('changelog'):
        ret = json_request.get('changelog').get('items')[0].get('toString')
        if not ret:
            return 'Done'
        return ret


@app.route('/', methods=['POST', 'GET'])
def data():
    """run when an issue created on jira"""

    if request.method == 'POST':

        print("**** CALL **********\n\n\n")

        # [TODO] REMOVE initialize variables
        comment = None
        event = None
        user_name = None

        request_readable = request.data.decode("utf-8")

        # convert json to dictionary
        json_request = json.loads(request_readable)

        with open('json_request.log', 'w', encoding='utf-8') as file_desc:
            file_desc.write(json.dumps(json_request, indent=8))
            # print(json.dumps(json_request, indent=8))

        my_audience = get_uniq_audience(my_data=json_request)
        # if len(my_audience):
        #     print(my_audience)

        event_parse = json_request.get(
            'webhookEvent')
        issue_event = json_request.get('issue_event_type_name')
        # change_log = json_request.get('changelog')
        # changes_log = json_request.get('changelog').get('fields').get('summary')

        issue_key = get_issue_key(json_request)
        # if issue_key:
        #     print("#key ", issue_key)

        if issue_event:
            # print(issue_event, get_issue_type(issue_event))
            event = get_issue_type(issue_event)
        issue_priority = get_issue_priority(json_request)

        if json_request.get('user'):
            # add user_name to set when send sms done release set
            user_name = json_request.get('user').get('displayName')

        # for comments
        if event == 'COMMENT' or event == 'COMMENT_EDITED':
            comment = json_request.get('comment').get('body')
        # cant work for comment deletion
        if event == 'COMMENT_DELETED':
            return f"The URL / is accessed directly."
        elif issue_event == None:
            """dont create extra sms for empty request"""
            return f"The URL / is accessed directly."

        if issue_event == 'issue_assigned':
            assigned_to = json_request.get(
                'changelog').get('items')[0].get('toString')
            # print('task assiged to', assigned_to)

        issue_summary = get_issue_summary(json_request)

        issue_duedate = get_duedate(json_request)
        status = get_status(json_request, event)
        task_url = get_url(json_request, issue_key)

        # get_changelog(json_request)
        if not comment:
            send_str = [
                f'# {issue_key}\t {event}\n',
                f'{issue_summary}\n',
                f'[{status}]\n',
                f'{issue_priority} {issue_duedate}\n',
                f'"{user_name}"\n',
                f'{task_url}'
            ]
        else:
            send_str = [
                f'# {issue_key} {event}\n',
                f'{issue_summary}\n',
                f'[{status}]\n',
                f'{issue_priority} {issue_duedate}\n',
                f'"{user_name}"\n',
                "---\n",
                f'{comment}\n',
                "---\n",
                f'{task_url}'
            ]

        # with open('sms_format.config', 'r') as fd:
        #     send_str = fd.readlines()

        # print("send this: ", send_str)
        # print("all is: ", effify(send_str))

        # logger.debug(send_str)

        # convert list to string
        string = "".join(str(x) for x in send_str)
        print(string)
        # send to all audience
        for item in my_audience:
            number = get_number(item)
            print(item, number)
            if number:
                send_sms_to_number(string, number)

        return f"The URL / is accessed directly."

    return False


init_gsm_modem()

# send_sms_to_number("✅", '09929988365')
# run a http server on this ip:port address
app.run(host='0.0.0.0', port=5050)
