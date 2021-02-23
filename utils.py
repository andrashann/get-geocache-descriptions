import requests

from bs4 import BeautifulSoup

from icon_mapping import icon_mapping


def replace_coord_tag(coord_tag_string: str):
    '''instead of the <coord ...> tag we found, return
    a simple string with its useful content'''
    soup = BeautifulSoup(coord_tag_string, 'lxml')
    coord = soup.find_all("coord")[0]
    params = []
    # coords should have an icon. if so, add this icon to the output
    icon = coord.get('icon')
    # "icon" might be a Hungarian/English word instead of an ID, let's
    # map it to the nubmer (which will be the file name)
    if icon:
        if icon.lower().strip() in icon_mapping:
            icon = icon_mapping[icon.lower().strip()]
        # The icon might be something else (as a mistake). in this case,
        # subsitute it with the "waypoint" icon, "76". If it is still not
        # a number stored as a string, it is a mistake and we need to
        # replace it.
        try:
            _ = int(icon)
        except ValueError:
            icon = "76"
        params += [
            f'<img src="https://geocaching.hu/terkepek/ikonok/{icon}.png" style="position: relative; top: 2px;" width="14" height="12" border="0">']

    params += [x for x in [
        coord.get('description'),
        coord.get('lat'),
        coord.get('lon'),
        coord.get('altitude')
    ] if x is not None]
    new_string = f"<b>[{' '.join(params)}]</b>"
    return(new_string)


def get_logs_for_cache(cache_id: str, n_logs: int, ignore_default_logs: bool = True):
    headers = {'accept': 'application/json'}
    params = (
        ('cacheid', cache_id),
        ('fields', 'date,member,userphone,notes'),
        ('dir', 'desc')
    )

    r = requests.get('https://api.geocaching.hu/logsbycache',
                     headers=headers, params=params)
    data = r.json()

    logs = []
    # Some apps frequently used by cachers have default log texts
    # which are not informative. They have the version number in
    # the log in brackets.
    if ignore_default_logs:
        for l in data:
            if not (
                # Geoládák app
                (l['notes'].startswith(
                    'Megtaláltam, köszönöm a rejtést! [Geoládák v') and l['notes'].endswith(']'))
                or
                # g:hu app
                (l['notes'].startswith(
                    'Megtaláltam. Köszönöm a lehetőséget. [g:hu') and l['notes'].endswith(']'))
                or
                # g:hu+ app
                (l['notes'].startswith(
                    'Megtaláltam.\nKöszönöm a lehetőséget.\n[g:hu+') and l['notes'].endswith(']'))
            ):
                logs.append(l)
    else:
        logs = data

    return logs[:n_logs]
