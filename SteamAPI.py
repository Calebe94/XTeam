from subprocess import Popen,PIPE
import xml.etree.ElementTree as ET
import sys,os,json,time,AcfParser

if sys.version_info[0] < 3:
    # I am using it because of the debug test
    from urllib import urlopen
else:
    from urllib.request import urlopen

class SteamAPI(object):
    """
        library Dictionary works like this: library[state][platform][appid][keys]
        #STATE:
        installed: All the games installed in your computer, can be Wine or Linux.
        library: All the steam user's games
        #PLATFORM:
        linux: Linux installed games
        windows: Windows games installed by Wine
        #APPID:
        is the game's appid that you want to get information
        #KEYS:
        name:   Game's name
        appid:  Games's appid. Again ?? Yes, I'll use it to return to the addon.
        header: game's header
        installdir: game's installed dir
        executable: game's executable
        controller_support: return if the game's have gamepad support
        oslist: show the platforms
        images: list of screenshots
        movies: list of movies
        description: short description about the game
    """
    WINE_PATH=str()
    LINUX_PATH=str()
    PUBLIC_ID=str()
    #GET_APP_INFO = "https://steampics-mckay.rhcloud.com/info?apps=200900&prettyprint=1"
    ALL_GAMES = 'http://api.steampowered.com/ISteamApps/GetAppList/v0002/?format=xml'
    LINUX_GAMES = 'https://raw.githubusercontent.com/SteamDatabase/SteamLinux/master/GAMES.json'
    LIBRARY=dict()
    profilefolder=str()

    LIBRARY['installed'] = dict()
    LIBRARY['library'] = dict()

    def __init__(self,wine,public_id,profiles_folder):
        #Verification is did outside
        self.profilefolder = profiles_folder
        self.LINUX_PATH=os.getenv('HOME')+"/.steam/steam/"
        self.WINE_PATH=wine
        self.PUBLIC_ID=public_id
        self.LIBRARY["installed"] = self.getInstalledGames()
        self.LIBRARY["library"] = self.getOwnedGames()

    def linux(self,command):
        logfile = open(self.profilefolder+"/_linux_.log","a")
        pid = os.fork()
        steam = pgrep("Steam.exe")
        if(steam):
            os.system("wine %sSteam.exe -shutdown"%(self.path2UNIX(self.WINE_PATH)))
            while(pgrep("Steam.exe")):
                time.sleep(1)
        if pid == 0:
            # PIPE : stderr > stdout > logfile
            os.dup2(logfile.fileno(),1)
            os.dup2(1,2)
            os.system("steam -applaunch %s -silent"%command)
            time.sleep(5)
        return str(self.LIBRARY['installed']['linux'][command]['executable'])

    def wine(self,command):
        logfile = open(self.profilefolder+"/_wine_.log","a")
        pid = os.fork()
        steam = pgrep("steam")
        if(steam):
            os.system("steam -shutdown")
            while(pgrep("steam")):
                    time.sleep(1)
        if pid == 0:
            # PIPE : stderr > stdout > logfile
            os.dup2(logfile.fileno(),1)
            os.dup2(1,2)
            os.system("wine %sSteam.exe -applaunch %s -silent"%(self.path2UNIX(self.WINE_PATH),command))
            time.sleep(5)
        return self.LIBRARY['installed']['windows'][command]['executable']

    def getInstalledGames(self):
        client_wine = self.WINE_PATH + "steamapps/"
        client_linux = self.LINUX_PATH + "steamapps/"
        my_list ={"linux":client_linux,"windows":client_wine}
        file_installed = self.profilefolder+"/"+self.PUBLIC_ID+"_installed.json"
        if os.path.exists(file_installed):
            with open(file_installed, 'r') as fp:
                AUX = json.load(fp)
        else:
            AUX = dict()
            AUX['linux']=dict()
            AUX['windows']=dict()

            for client in my_list:
                for file in os.listdir(my_list[client]):
                    if file.endswith(".acf"):
                        acf=AcfParser.parse_acf(my_list[client]+file)
                        AUX[client][acf['AppState']['appid']] = self.getInfo(client,acf['AppState']['appid'])
                with open(file_installed, 'w') as fp:
                    json.dump(AUX, fp)
        return AUX

    def getOwnedGames(self):
        owned_games = "http://steamcommunity.com/id/%s/games?tab=all&xml=1"%self.PUBLIC_ID
        tree=ET.ElementTree(file=urlopen(owned_games))
        root = tree.getroot()
        Owned = dict()

        for game in root.iter('game'):
            gameID = game.find('appID').text
            Owned[gameID]=dict()
            Owned[gameID]['appid'] = gameID
            Owned[gameID]['name'] = game.find('name').text
            Owned[gameID]['logo'] = game.find('logo').text
            Owned[gameID]['platform'] = self.isInstalled(gameID)
        return Owned

    def path2UNIX(self,path):
        aux=str()
        for index in range(0,len(path)):
            if path[index] == '\'':
                aux=aux+'\\'
            elif path[index] == ' ':
                aux=aux+'\\'
            aux=aux+path[index]
            index=index+1
        return aux

    def isInstalled(self,gameid):
        return_list = []

        for installed in list(self.LIBRARY['installed']['windows'].keys()):
            if gameid == installed:
                return_list=return_list + [str(self.LIBRARY['installed']['windows'][gameid]['platform'])]
        for installed in list(self.LIBRARY['installed']['linux'].keys()):
            if gameid == installed:
                return_list=return_list + [str(self.LIBRARY['installed']['linux'][gameid]['platform'])]

        if not return_list:
            return "not installed"
        else:
            return return_list

    def getInfo(self,platform,appID):
        # Strings to be used in this function
        name = str()
        logo = str()
        icon=str()
        oslist=str()
        controller_support=str()
        installdir=str()
        executable = str()
        gameID = str()
        # Dictionary to be used
        aux_dict = dict()

        controller_support = "None"

        url = "https://steampics-mckay.rhcloud.com/info?apps=%s&prettyprint=1"%appID
        response=urlopen(url)
        data = json.loads(response.read())

        name = data['apps'][appID]['common']['name']
        gameID = data['apps'][appID]['appid']
        logo = "http://cdn.akamai.steamstatic.com/steam/apps/%s/header.jpg?t=1466791207"%(appID)
        oslist = str(data['apps'][appID]['common']['oslist'])
        common_keys = list(data['apps'][appID]['common'])

        for key in common_keys:
            if "controller_support" in key:
                controller_support = data['apps'][appID]['common']['controller_support']

        installdir = data['apps'][appID]['config']['installdir']
        keys=list(data['apps'][appID]['config']['launch'].keys())
        if 'library' not in platform:
            for index in keys:
                if len(list(oslist.split(','))) == 1:
                    executable = data['apps'][appID]['config']['launch'][index]['executable']
                elif platform in data['apps'][appID]['config']['launch'][index]['config']['oslist']:
                    executable = data['apps'][appID]['config']['launch'][index]['executable']
        else:
            platform = str(",".join(self.isInstalled(appID)))

        aux_dict['name'] = name
        aux_dict['appid'] = gameID
        aux_dict['header'] = logo
        aux_dict['installdir'] = installdir
        aux_dict['executable'] = executable
        aux_dict['controller_support'] = controller_support
        aux_dict['oslist'] = oslist
        aux_dict['platform'] = platform

        short_description=str()
        images_url = "http://store.steampowered.com/api/appdetails/?appids=%s&format=json"%appID
        image_response=urlopen(images_url)
        image_data = json.loads(image_response.read())

        short_description = image_data[appID]['data']['short_description']
        my_images = list(image_data[appID]['data']['screenshots'])
        my_movies = list(image_data[appID]['data']['movies'])

        images_list = list()
        for index in range(0,len(my_images)):
            images_list.append(my_images[index]['path_thumbnail'])

        aux_dict['images'] = str(",".join(images_list))

        movies_list = list()
        for index in range(0,len(my_movies)):
            movies_list.append(my_movies[index]['webm']['max'])

        aux_dict['movies'] = str(",".join(movies_list))
        aux_dict['description'] = short_description

        return aux_dict

def pgrep(pattern):
    """
    Return the pattern pid
    """
    pid=str()
    process = Popen(['pgrep',pattern],stdout=PIPE,stderr=PIPE)
    out = str(process.communicate()).split()

    if out is not None:
        for digit in out[0]:
            if digit.isdigit():
                pid=pid+digit
    return pid
"""
wines = "/home/calebe945/PlayOnLinux's virtual drives/calebe945/drive_c/Program Files/Steam/"
if __name__ == '__main__':
    steam = SteamAPI(wines,"calebenovequatro","/home/calebe945/Projetos")
    #print(list(steam.LIBRARY['installed']['linux']['200900']['movies'].split(',')))
    #print(steam.isInstalled("227600"))
    #print(steam.LIBRARY['installed']['linux']['200900'].keys())
    print(steam.LIBRARY['library']['200900']['platform'])
    #print("Numero de Jogos:",len(steam.LIBRARY['library'].keys()))
    #print("Oniken:",steam.isInstalled('252010'))
    #gameID = str(steam.linux("200900"))
    #gameID = steam.wine('280790')
    #print(gameID)
"""
