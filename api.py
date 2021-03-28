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

@app.route('/genres/')
def get_genres():
    if len(genres):
        return jsonify(genres)


@app.errorhandler(404)
def page_not_found_error(error):
    return jsonify({'status': 404})

if __name__ == '__main__':
    app.run()