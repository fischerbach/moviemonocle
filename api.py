from flask import (Flask, jsonify, request, redirect, url_for, render_template,
                   abort, send_from_directory)
import pandas as pd
import requests
import sqlite3
import json

app = Flask(__name__)

conn = sqlite3.connect('final.db')
movies = pd.read_sql('select * from movies', con=conn)
ratings = pd.read_sql('select id from (select id, count(distinct userId) as uu from ratings group by 1 order by 2 desc limit 1000)', con=conn)

movies['genres'] = movies['genres'].apply(lambda x: x.split("|"))
genres = list(movies[['genres']].explode('genres')['genres'].unique())

class Pipeless:
    def __init__(self, key, app_id, base='https://api.pipeless.io/v1/apps', debug = False):
        self.base = f'{base}/{app_id}'
        self.debug = debug
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {key}"
        }
    
    def _chunks(self, lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]
    
    def events_batch(self, data):
        for chunk in self._chunks(data, 10):
            payload = {
                "events": chunk,
                "synchronous": False
            }

            url = f"{self.base}/events/batch"

            response = requests.request("POST", url, json=payload, headers=self.headers)
            if(self.debug):
                print(response.text)
                # print(chunk)
                pass
    

    def get_related_content(self, object_id, object_type):
        url = f"{self.base}/algos/recommendations/related-content"
        payload = {
            "object": {
                "id": object_id,
                "type": object_type
            },
            "positive_rel": "liked",
            "content_tagged_relationship_type": "taggedWith",
            "ontent_tagged_object_type": "tag"
            
        }

        response = requests.request("POST", url, json=payload, headers=self.headers)
        return response.json()
    
    def create_event(self, user_id, event_type, target_id):
        url = f"{self.base}/events"
        if(event_type not in ['liked', 'disliked']):
            return {}

        payload = {
            "event": {
                "start_object": {
                    "id": user_id,
                    "type": "user"
                },
                "relationship": {
                    "type": event_type
                },
                "end_object": {
                    "id": target_id,
                    "type": "film"
                }
            },
            "synchronous": False
        }


        response = requests.request("POST", url, json=payload, headers=self.headers)
        return response.json()
    
    def get_activities(self, object_id, object_types):
        url = f"{self.base}/algos/activity/object"

        payload = {
            "object":
                {
                    "id":object_id,
                    "type":object_types
                },
            "direction":"incoming"
        }

        response = requests.request("POST", url, json=payload, headers=self.headers)
        return response.json()

    

pipeless = Pipeless(key='API_KEY', app_id=APP_ID, debug=True)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/details/<imdb>')
def details(imdb):
    movie = movies.query(f'id == "{imdb}"')
    if len(movie):
        movie = movie.to_dict(orient='records')[0]
    else:
        movie = []
    return render_template('details.html', data=movie)

@app.route('/movies/')
@app.route('/movies/page/<int:page>')
def get_all_movies(page=0):

    def paginator(data, n, page):
        paginated = [data[i:i+n] for i in range(0, len(data), n)]
        try:
            page = paginated[page]
        except:
            page = []
        return page


    return jsonify(paginator(movies.to_dict(orient='records'), 8, page))

@app.route('/all_titles/')
def get_all_titles():
    result= movies[['id','title']].set_index('title').to_dict()
    return jsonify(result['id'])

@app.route('/movies/random/<int:n>')
def get_random_movies(n):

    return jsonify(movies.query(f'id in {json.dumps(list(ratings["id"].values))}').sample(n=n).to_dict(orient='records'))

@app.route('/movies/<imdb>')
def get_single_movie(imdb):
    movie = movies.query(f'id == "{imdb}"')
    if len(movie):
        return jsonify(movie.to_dict(orient='records'))
    return jsonify([])

@app.route('/movies/related/<imdb>')
@app.route('/movies/related/<imdb>/<recurrent>')
def get_related_movies(imdb, recurrent=False):
    related = pipeless.get_related_content(imdb, 'film')
    result = []

    try:
        result = [movie for movie in map(lambda x: x['object']['id'], related['items'])]
    except:
        pass

    if recurrent:
        result = movies.query(f'id in {result}').to_dict(orient='records')

    if len(result):
        return jsonify(result)
    return jsonify([])

@app.route('/activities/movie/<imdb>')
def get_activities(imdb):
    activities = pipeless.get_activities(imdb, 'film')
    return jsonify(activities)

@app.route('/genres/')
def get_genres():
    if len(genres):
        return jsonify(genres)

@app.route('/like/<user_id>/<imdb>', methods = ['POST'])
def like(user_id, imdb):
    pipeless.create_event(user_id, 'liked', imdb)
    return jsonify({})

@app.route('/dislike/<user_id>/<imdb>', methods = ['POST'])
def dislike(user_id, imdb):
    pipeless.create_event(user_id, 'disliked', imdb)
    return jsonify({})


@app.errorhandler(404)
def page_not_found_error(error):
    return jsonify({'status': 404})

if __name__ == '__main__':
    app.run()