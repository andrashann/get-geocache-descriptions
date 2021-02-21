# geolada-leirasok
A very basic api to download geocache data and descriptions from [geocaching.hu](https://geocaching.hu) (for printing, storing as one html on a phone, etc.)

Check it out live: [https://geolada-leirasok.herokuapp.com](). You can also check out [this sample response](https://geolada-leirasok.herokuapp.com/caches/70).

## Why?

It is sometimes a good idea to have the information of the geocaches I am planning to find at hand on paper. It is rather cumbersome to copy these manually from the website; using its API is much faster. 

The results I get here are not beautiful but they do their job perfectly: allow me to read about the caches without wasting battery life.

## How?

I send a simple request to the [geocaching.hu API](https://api.geocaching.hu/), format it using some regex/BeautifulSoup/Jinja magic and return it to the user via a very basic FastAPI backend.

## Note

This service works on the Hungarian [geocaching.hu](https://geocaching.hu) website. The caches there are not the same as on [geocaching.com](https://geocaching.com), although there is an overlap. All the descriptions are in Hungarian. 