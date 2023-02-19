import pickle
from .tcore.instances import PLAYER



class LocalDatabase:
    def __init__(self):
        self.db = self.load_db()

    def load_db(self):
        db = pickle.load(open("localdata.db", "rb"))
        self.database = db
        return db


    def save_db(self):
        for player in PLAYER.values():
            steamid = player.steamid
            self.db[steamid] = \
            {'weapon_preference_pistol':player.weapon_preference_pistol,
             'weapon_preference_rifle': player.weapon_preference_rifle,
             'weapon_preference_nades': player.weapon_preference_nades,
             'weapon_preference_knife': player.weapon_preference_knife,
             'model_preference' : player.model_preference
            }

        pickle.dump(self.db, open("localdata.db", "wb"))

