import tweepy, folium
from flask import Flask, redirect, render_template, request
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable
from tweepy.error import TweepError

def auth(consumer_key, consumer_secret, access_token, access_token_secret):
    '''
    Sets up api for OAuth1. It requires w keys and 2 tokens.
    '''
    try:
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        api = tweepy.API(auth)
    except TweepError:
        return False
    
    
    return api

def get_location(user):
    '''
    Returns tuple with screen name and location of a user.
    '''
    location = user.location
    geolocator = Nominatim(user_agent="my_request")
    try:
        loc = geolocator.geocode(location)
    except GeocoderUnavailable:
        return False
    if loc is None:
        return False
    return user.screen_name, loc.latitude, loc.longitude

def friends_locations(screen_name, api):
    '''
    Operates over the user friends and creates a list of his 7 friends,
    who have valid location
    '''
    loc_lst = []
    try:
        user = api.get_user(screen_name)
    except TweepError:
        return False

    for friend in user.friends():
        loc = get_location(friend)
        if loc:
            loc_lst.append(loc)
        if len(loc_lst) > 7:
            break
    return loc_lst

def create_map(user, locations: list):
    '''
    Creates map with friends markers of a user
    '''
    user_loc = get_location(user)
    map_test = folium.Map()
    fg = folium.FeatureGroup(name='friends_locations')
    if user_loc:
        map_test = folium.Map(location=(user_loc[1], user_loc[2]), zoom_start=5)
        fg.add_child(folium.Marker(location=[user_loc[1], user_loc[2]],
                                    popup=f'User: {user_loc[0]}',
                                    icon=folium.Icon()))
    for name, lat, lon in locations:
        fg.add_child(folium.Marker(location=[lat, lon],
                                    popup=name,
                                    icon=folium.Icon()))
    map_test.add_child(fg)

    return map_test

def generate_map(screen_name):
    api = auth(CONSUMER_KEY, CONSUMER_KEY_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    loc = friends_locations(screen_name, api)
    test_map = create_map(api.get_user(screen_name), loc)
    return test_map

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/map', methods=["POST"])
def generate():
    screen_name = request.form.get('twit')
    consumer_key = request.form.get('consumer_key')
    consumer_key_secret = request.form.get('consumer_key_secret')
    access_token = request.form.get('access_token')
    access_token_secret = request.form.get('access_token_secret')
    if not (screen_name and consumer_key and consumer_key_secret and access_token and access_token_secret):
        return render_template('failure.html')

    api = auth(consumer_key, consumer_key_secret, access_token, access_token_secret)
    loc = friends_locations(screen_name, api)
    if not api or not loc:
        return render_template('failure.html')
    twitter_map = create_map(api.get_user(screen_name), loc)
    return twitter_map.get_root().render()

if __name__ == '__main__':
    app.run(debug=True)
