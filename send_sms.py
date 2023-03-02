"""
send sms message to user with GSM modem
"""

import subprocess


def run_bash_command(command):
    """docstring"""

    bash_command = command
    try:
        process = subprocess.Popen(bash_command, stdout=subprocess.PIPE)
        output, error = process.communicate()
    except Exception as error_exception:
        print('cannot run command: ', error_exception)
        exit(1)
    return output


def scan_gsm_modem():
    """scan for gsm modems connected to system"""
    run_bash_command(["mmcli", "-S"])


def get_modem_list():
    """return list of modems"""
    return run_bash_command(["mmcli", "-L"])


def init_gsm_modem():
    """initialize modem"""
    scan_gsm_modem()
    return get_modem_list()


def send_sms_to_number(msg, phone_number):
    """sending sms thru gsm modem"""
    # get one GSM modem
    output = init_gsm_modem()
    modem = ' '.join(output.decode('utf-8').split()[0:]).split(' ')[0]

    if modem and phone_number:
        # create text message
        # bash_command = f"mmcli -m {modem} --messaging-create-sms=text='{msg}',number={phone_number}"
        bash_command = [
            'mmcli', '-m', f'{modem}', f"--messaging-create-sms=text='{msg}',number={phone_number}"
        ]
        output = run_bash_command(bash_command)

        message = " ".join(output.decode('utf-8').split()
                           [0:]).split(' ')[-1].split('/')[-1]
        modem_number = modem.split('/')[-1]

        # send to phone_number
        bash_command = [
            'mmcli', '-m', f'{modem_number}', '--sms', f'{message}', '--send']
        output = run_bash_command(bash_command)

        # [todo]: logs
        print(output)
    else:
        print('modem or number not valid')
