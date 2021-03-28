import pandas as pd
import sqlite3
import requests

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
            st.write(chunk)
            response = requests.request("POST", url, json=payload, headers=self.headers)
            if(self.debug):
                print(response.text)
                pass

    def get_related_content(self, object_id, object_type):
        url = f"{self.base}/algos/recommendations/related-content"
        payload = {
            "object": {
                "id": object_id,
                "type": object_type
            },
            "positive_rel": "liked"
        }

        response = requests.request("POST", url, json=payload, headers=self.headers)
        return response.json()

pipeless = Pipeless(key='APP_KEY', app_id=APP_ID, debug=True)

conn = sqlite3.connect('final.db')
query = '''
SELECT 
    userId,  
    CASE
        WHEN rating >= 4.5
            THEN  "liked"
        WHEN rating <= 1
            THEN "disliked"
        ELSE
            "viewed"
    END AS relationship_type, 
    id AS movieId 
FROM ratings
WHERE 
    relationship_type != 'viewed'
'''
events = pd.read_sql(query, con=conn)
data = events

result = pd.DataFrame()
result['start_object'] = data['userId'].apply(lambda x: {'id': str(x), 'type': 'user'})
result['end_object'] = data['movieId'].apply(lambda x: {'id': str(x), 'type': 'film'})
result['relationship'] = data['relationship_type'].apply(lambda x: {'type':x})
pipeless.events_batch(result.to_dict(orient='records'))


movies = pd.read_sql('select * from movies', con=conn)
movies['tag'] = movies['genres'].apply(lambda x: x.split("|"))
movies = movies.explode('tag')
data = movies.copy()

result = pd.DataFrame()
result['start_object'] = data['id'].apply(lambda x: {'id': str(x), 'type': 'film'})
result['end_object'] = data['tag'].apply(lambda x: {'id': str(x), 'type': 'tag'})
result['relationship'] = data['tag'].apply(lambda x: {'type':'taggedWith'})

pipeless.events_batch(result.to_dict(orient='records'))