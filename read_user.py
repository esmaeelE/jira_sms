"""parse user.txt file to make a dictionary for use in python script"""


LINES = ''
with open('./user.txt', 'r', encoding='utf-8') as fd:
    LINES = fd.readlines()


def get_lookup_number():
    """split each line and get dictionray"""

    lookup_number = {}

    for item in LINES:
        a = item.split(',')
        lookup_number.update({a[0]: a[2]})
    return lookup_number
