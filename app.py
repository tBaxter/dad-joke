import random
import requests
from flask import Flask, render_template
from flask_caching import Cache

from settings import UNSPLASH_API_KEY

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'  # Choose cache type, e.g., 'simple', 'redis', etc.
cache = Cache(app)


#@cache.memoize(60) # Here, get_photo()'s output is cached for 60 seconds.
def get_photo():
    headers = {'Authorization': 'Client-ID ' + UNSPLASH_API_KEY}
    r = requests.get("https://api.unsplash.com/photos/random?query=older%20man&orientation=landscape", headers=headers)
    resp = r.json()
    photo = {
        'image': resp['urls']['regular'],
        'photog': resp['user']['name'],
        'photog_link': resp['user']['links']['html'],
        'alt': resp['alt_description']
    }
    return photo

@app.route("/")
@cache.cached(timeout=20)  # Cache this view for 60 seconds
def index():
    """
    Return a dad joke. 
    We give preference to the Fatherhood.gov API, because we think it's cool that it exists.
    Failing that, we'll go to icanhazdadjoke.
    The json 403s without a user agent header. 
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    r = requests.get("https://www.fatherhood.gov/jsonapi/node/dad_jokes", headers=headers)
    joke = None
    if r.status_code == 200:
        resp = r.json()
        randomJoke = random.choice(resp['data'])
        # do we want the main page, or do we want to extract the link to exact joke?
        joke = {
            'opener': randomJoke['attributes']['field_joke_opener'],
            'punchline': randomJoke['attributes']['field_joke_response'],
            'source': "fatherhood.gov",
            'permalink': "https://fatherhood.gov" + randomJoke['attributes']['path']['alias'] ,
        }
    else:
        # we failed to get a joke from fatherhood.gov. Let's try icanhazdadjoke.
        r = requests.get("https://icanhazdadjoke.com/", headers={'Accept': 'application/json'})
        if r.status_code == 200:
            resp = r.json()
            splitJoke = resp['joke'].split('?')
            # Check if the sample joke has a question setup or not.
            if len(splitJoke) > 1:
                opener =  splitJoke[0] + '?'
                punchline = splitJoke[1]
            else:
                opener =  splitJoke[0]
                punchline = ''
            joke = {
                'opener': opener,
                'punchline': punchline,
                'source': "icanhazdadjoke",
                'permalink': "https://icanhazdadjoke.com/j/" + resp['id'],
            }
        else:
            return "We failed to get a joke"
    if not joke:
        return "we failed to get a joke"
    # now that we have a joke, let's get an image for it (cached or otherwise)
    photo = get_photo()
    templateData = {
        'joke': joke,
        'photo': photo
    }
    return render_template('index.html', **templateData)

@app.route("/about")
def about():
    return render_template('about.html')