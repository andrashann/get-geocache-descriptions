from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

import requests

import re
from bs4 import BeautifulSoup

import jinja2

from icon_mapping import icon_mapping


tags_metadata = [
    {
        "name": "caches",
        "description": "Geoláda-leírások letöltése / Download geocache descriptions",
    }
]


app = FastAPI(
    title="Geocaching.hu ládaleírások / Geocaching.hu cache descriptions",
    description='''Egy egyszerű API, ami a ládák URL-jében található azonosítók alapján
  egy minimálisan formattált ládaleírás-gyűjteményt ad vissza.

  A simple API that returns geocache descriptions from geocaching.hu with minimal
  formatting based on the ID found in the URL of the caches.

  [https://github.com/andrashann/get-geocache-descriptions](https://github.com/andrashann/get-geocache-descriptions)
  ''',
    version="0.0.1",
    docs_url="/", redoc_url=None,
    openapi_tags=tags_metadata
)


def replace_coord_tag(coord_tag_string):
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


@app.get("/caches/{caches}", tags=["caches"], response_class=HTMLResponse)
def get_caches(caches: str, json: bool = False, two_col: bool = False):
    '''Egy vesszővel elválasztott azonosítólista (pl. 237,361,858) alapján visszaadja
    a ládainformációkat. Alapbeállításként egy HTML választ ad, de ha ?json=true, a
    nyers adatokat kapjuk meg egy JSON objektumban.

    Returns  cache info based on a comma-separated list of IDs – e.g. 237,361,858.
    By default, it returns a HTML response. By passing ?json=true, we can get
    the raw data in a JSON object.'''

    # fields we will get from the api
    FIELDS = "id,dateid,waypoint,nickname,lat_h,lat_mmss,lat,long_h,long_mmss,lon,altitude,member,userphone,fulldesc"

    headers = {'accept': 'application/json'}
    params = (('id_list', caches), ('fields', FIELDS))

    # api documentation: https://api.geocaching.hu/
    r = requests.get('https://api.geocaching.hu/cachesbyid',
                     headers=headers, params=params)
    data = r.json()

    # sort data according to input cache ids
    sorted_data = []
    for id in caches.split(','):
        # get the cache with the given id
        sorted_data.append([x for x in data if x['id'] == id][0])

        # replace line breaks with actual line breaks that will render in the
        # html output
        sorted_data[-1]['fulldesc'] = sorted_data[-1]['fulldesc'].replace(
            '\n\n', '\n').replace('\n', '<br/>\n')

        # replace relative links of icons that are used on the website with
        # absolute links
        sorted_data[-1]['fulldesc'] = sorted_data[-1]['fulldesc'].replace(
            r'/terkepek/ikonok/', r'https://geocaching.hu/terkepek/ikonok/')

        # we have to remove the custom '<coord ...>' tags which carry useful
        # information but they break the html output.
        # I cannot rely on BeautifulSoup to find the tags as they are
        # part of a large block of text submitted by the users and sometimes
        # they have mistakes in them.
        sorted_data[-1]['fulldesc'] = re.sub(
            r"(< ?coord .*?>)",
            lambda x: replace_coord_tag(x.group()),
            sorted_data[-1]['fulldesc']
        )

    if json:
        return JSONResponse(content=sorted_data)

    with open('template.html') as f:
        template = jinja2.Template(f.read())

    return(template.render(caches=sorted_data, two_col=two_col))
