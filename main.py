from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

import requests

import re
from bs4 import BeautifulSoup

import jinja2


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
  formatting based on the ID found in the URL of the caches.''',
    version="0.0.1",
    docs_url="/", redoc_url=None,
    openapi_tags=tags_metadata
)


def replace_coord_tag(coord_tag_string):
    '''instead of the <coord ...> tag we found, return
    a simple string with its useful content'''
    soup = BeautifulSoup(coord_tag_string, 'lxml')
    coord = soup.find_all("coord")[0]
    params = [x for x in [
        coord.get('description'),
        coord.get('lat'),
        coord.get('lon'),
        coord.get('altitude')
    ] if x is not None]
    new_string = f"<b>[{' '.join(params)}]</b>"
    return(new_string)


@app.get("/caches/{caches}", tags=["caches"], response_class=HTMLResponse)
def get_caches(caches: str, json: bool = False):
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
        sorted_data[-1]['fulldesc'] = sorted_data[-1]['fulldesc'].replace(
            '\n\n', '\n').replace('\n', '<br/>\n')

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

    template_html = '''<html><head>
    <style>
    .info { border: 1px solid black; display: block;}
    .gray { color: gray; }
    * { font-family: "Arial Narrow" !important; }
    </style></head><body>
    {% for c in caches %}
    <h2>{{ c.dateid }}. {{ c.waypoint }} {{ c.nickname }}</h2>
    <p>
    <span class="info">
    {{ c.lat_h }}°{{ c.lat_mmss }}';{{ c.long_h }}°{{ c.long_mmss }}' 
    <span class="gray">({{ c.lat }}°;{{ c.lon }}°)</span>
    {{ c.altitude }}m
    {{ c.member }} {{ c.userphone }} <br />
    </span>
    {{ c.fulldesc }}
    </p>
    {% endfor %}
    </body></html>'''

    template = jinja2.Template(template_html)
    return(template.render(caches=sorted_data))
