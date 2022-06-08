import requests
from bs4 import BeautifulSoup
import urllib.request
import json

urlbase = 'https://www.cpasbien.vip'

urlpage = urlbase + '/torrents_films.html'

user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
header={'User-Agent':user_agent}

token = 'secret_xxxx your Notion integration token'
databaseId = 'your database id'

headers = {
    "Authorization": "Bearer " + token,
    "Content-Type": "application/json",
    "Notion-Version": "2021-05-13"
}

#print(soup.find_all("tr"))

#_#_#--- Classes ---#_#_#
class Notion_NetFlo():
    notion_api_url = f'https://api.notion.com/v1/pages'
   
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
        "Notion-Version": "2021-05-13"
    }

    def CreateJson(self, name, type, link) -> dict:
        return {
            "parent": {
                "database_id": databaseId
            },
            "properties": {
                "Name": {
                    "title": [
                        {
                            "text": {
                                "content": name
                            }
                        }
                    ]
                },
            "Type": {
                "select": {
                    "name": (type.lower()).capitalize()
                }
            },
            "Lien Magnet": {
                "rich_text": [
                {
                    "text": {
                        "content": link
                    }
                }
            ]
        }
    }}

    def AddMovie(self, name: str, type: str, link: str) -> int:
        new_movie = self.CreateJson(name, type, link)

        request = requests.post(self.notion_api_url,
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": "2021-08-16",
                "Content-Type": "application/json"
            },
                data=json.dumps(new_movie))
        return request.status_code

class Movie():
    user_agent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
    header = {'User-Agent': user_agent}

    def Format_Title(self, title: str) -> str:
        words_list = title.split(" ")
        title = list()
        ban_words = ["MULTi", "x265", "HDLight", "1080p", "720p", "BluRay"]
        for index, word in enumerate(words_list):
            if( not word.isupper() and word not in ban_words): title.append(word)

        # delete the date
        title.pop( len(title)-1 )
        return " ".join(title)

    def __init__(self, data):
        self.resume = data
        self.name = data.find_all("a")[0].get_text()
        self.format_name = self.Format_Title(self.name)
        self.poid = data.find_all("div", {"class": "poid"})[0].get_text()
        self.url_details = urlbase + data.find_all("a", href=True)[0]["href"]

    def IsWeightOk(self) -> bool:
        ok = False
        if("Go" in self.poid and float(self.poid.removesuffix('Go')) > 1.5):
            ok = True
        return ok

    def GetMovieDetails(self):
        request = urllib.request.Request(self.url_details, None, self.header)
        response = urllib.request.urlopen(request)
        page = response.read()
        self.details = BeautifulSoup(page, 'html.parser')

    def IsAudioImageOk(self) -> bool:
        ok = True
        for span in self.details.find_all("span"):
            self.audio = span.get_text()
            if("Audio" in self.audio):
                ok = False
                break
        return ok

    def GetSynopsis(self) -> str:
        # Get synopsis
        self.synopsis = self.details.find("div", {"id": "textefiche"})
        self.synopsis = self.synopsis.find_all("p")[1].get_text()
        # Format synopsis with \n
        self.format_synopsis = ""
        cpt = 0
        for word in self.synopsis.split(" "):
            self.format_synopsis += (word + " ")
            cpt += len(word)
            if(cpt >= 100):
                self.format_synopsis += "\n"
                cpt = 0

        return self.format_synopsis


    def GetMagnetLink(self) -> str:
        # Get ID of movie
        id = self.details.find("div", {"id": "bigcover"})["classs"]
        # Post request
        payload = {'id': int(id)}
        data = requests.post(urlbase + "/download_magnet", data = payload)
        # Extract magnet link
        self.magnet_link = data.text.split("&")[0]
        return self.magnet_link

#_#_#--- Fonctions ---#_#_#

def Request(url, headers):
    request=urllib.request.Request(url,None,headers) #The assembled request
    response = urllib.request.urlopen(request)
    page = response.read()
    return BeautifulSoup(page, 'html.parser')


# Main
soup = Request(urlpage, header)
notion = Notion_NetFlo()


for m in soup.find_all("tr"):
    movie = Movie(m)
    print()
    print(f'#-> Name: {movie.name} | Size: {movie.poid}')

    # Est ce que le film n'est pas trop léger ?
    if( movie.IsWeightOk() ):
        key = input("#--> Veux-tu ce film ? (o/n)\n#--> ")
        while(key != "o" and key != "n"):
            key = input("#--> Erreur lettre incorrect. (o/n)\n#--> ")

        if(key == "o"):
            movie.GetMovieDetails()

            # Est-ce que l'audio est bien ?
            if( movie.IsAudioImageOk() ):
                print("#---> l'audio est nickel ")

                key = input("#----> Veux-tu le synopsis de ce film ? (o/n)\n#----> ")
                while(key != "o" and key != "n"):
                    key = input("#----> Erreur lettre incorrect. (o/n)\n#----> ")

                if(key == "o"):
                    movie.GetSynopsis()
                    print("#----> Synopsis :\n")
                    print(movie.format_synopsis, "\n")

                    key = input("#-----> Veux-tu ajouer le film ? (o/n)\n#-----> ")
                    while(key != "o" and key != "n"):
                        key = input("#-----> Erreur lettre incorrect. (o/n)\n#-----> ")

                    if(key == "o"):
                        print("#------> Ajout du film en cours ... ")
                        movie.GetMagnetLink()
                        Notion_NetFlo().AddMovie(movie.format_name, "film", movie.magnet_link)

                    else:
                        print("#------> Aller hop ça dégage film suivant ! ")

                else:
                    print("#----> Ajout du film en cours ... ")
                    movie.GetMagnetLink()
                    Notion_NetFlo().AddMovie(movie.format_name, "film", movie.magnet_link)

            else:
                print(f"#---> l'audio et l'image sont claqués: {movie.audio}")
        else:
            print("#---> Aller hop ça dégage film suivant ! ")
