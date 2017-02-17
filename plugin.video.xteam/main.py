import SteamAPI
from urlparse import parse_qsl
from urllib import urlencode
import xbmcgui,xbmcplugin,xbmcaddon,xbmc,xbmcvfs
import os

_url = sys.argv[0]
_handle = int(sys.argv[1])

def format_url(**kwargs):
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def check_params(_steamAPI,parameters):
    params = dict(parse_qsl(parameters))
    if params:
        if params['category'] == "Settings":
            xbmcaddon.Addon().openSettings()
        elif params['category'] == "Downloads":
            download = xbmcgui.Dialog()
            download.ok("NOT AVAILABLE YET!","THIS FEATURE IS IN DEVELOPMENT!")
            main_screen(_steamAPI.LIBRARY)
        elif params['category'] == "Installed":
            list_games(_steamAPI,"Installed")
            if params['action'] == 'play':
                if params['platform'] == 'linux':
                    _steamAPI.linux(params['game'])
                    dialog = xbmcgui.DialogProgress()
                    dialog.create("Xteam...","Launching the Following app ID:",params['game'])
                    while not SteamAPI.pgrep('steam'):
                        dialog.create("Xteam...","Launching the Following app ID:",params['game'])
                    dialog.close()
                elif params['platform'] == 'windows':
                    _steamAPI.wine(params['game'])
                else:
                    list_games(_steamAPI,"Installed")
            else:
                list_games(_steamAPI,"Installed")
        elif params['category'] == "Library":
            list_games(_steamAPI,"Library")
            if params['action'] == 'play':
                library = xbmcgui.Dialog()
                library.ok("NOT AVAILABLE!","THIS ADDON CAN'T INSTALL GAMES YET!","THIS FEATURE WILL BE AVAILABLE SOON!")
        else:
            raise ValueError("Invalid Paramstring:{0}!".format(parameters))
    else:
        main_screen(_steamAPI.LIBRARY)

def main_screen(categories):
    
    main_categories = ["Library","Installed","Downloads","Settings"]
    for category in main_categories:
        list_item=xbmcgui.ListItem(label=category)
        #list_item.setArt({'thumb':categories[category]["logo"][0]["logo"],'icon':categories[category]["logo"][0]["logo"],'fanart':categories[category]["logo"][0]["logo"]})
        list_item.setArt({'thumb':"/home/calebe945/Imagens/LOGOS/Xteam.jpg",'icon':"/home/calebe945/Imagens/LOGOS/Xteam.jpg",'fanart':"/home/calebe945/Imagens/LOGOS/Xteam.jpg"})
        list_item.setInfo('video',{'title':category,'genre':category})
        xbmcplugin.addDirectoryItem(_handle,format_url(action='listing', category=category),list_item,True)
    xbmcplugin.addSortMethod(_handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)
    
def list_games(steam,categories):
    #Solucao tecnica alternativa
    games = dict()
    if categories == "Installed":
        games = steam.getInstalledGames()
    if categories == "Library":
        games = steam.getOwnedGames()
    #elif:??? else: ??? 
    
    for game in range(0,len(games['name'])):
        list_item = xbmcgui.ListItem(label=games['name'][game]['name'])
        list_item.setInfo('video', {'title': games['name'][game]['name'], 'genre': games['platform'][game]['platform']})
        list_item.setArt({'thumb':games['logo'][game]['logo'],'icon':games['logo'][game]['logo'],'fanart':games['logo'][game]['logo']})
        xbmcplugin.addDirectoryItem(_handle,format_url(action='play',category=categories,platform=games['platform'][game]['platform'],game=games['appID'][game]['appID']),list_item,False)
    xbmcplugin.addSortMethod(_handle,xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)
    
def main(paramstring):
    params = dict(parse_qsl(paramstring))
    # First of all I need to Verify the settings before put it into the class
    _settings = xbmcaddon.Addon()
    dialog = xbmcgui.DialogProgress()
    dialog.create("Xteam...","Loading your Games")
    addonID = _settings.getAddonInfo('id')
    addonPath = _settings.getAddonInfo('path')
    userdata = xbmc.translatePath('special://profile/addon_data/'+addonID)
    profilesFolder = os.path.join(userdata,"profiles")
    
    #Parsing Folders
    if not os.path.isdir(userdata):
        os.mkdir(userdata)
    if not os.path.isdir(profilesFolder):
        os.mkdir(profilesFolder)
    WINE = _settings.getSetting("steam_wine")
    steamID = _settings.getSetting("steam_id")
    if os.path.isdir(WINE) is not True:
        error_wine = xbmcgui.Dialog()
        error_wine.ok("ERROR!","WINE PATH IS NOT A VALID PATH!")
    if os.path.isdir(os.getenv('HOME')+"/.steam/steam/") is not True:
        error_steam = xbmcgui.Dialog()
        error_steam.ok("ERROR!","DOES NOT FIND THE STEAM PATH","CHECK IF STEAM IS INSTALLED!")
    steam = SteamAPI.SteamAPI(WINE,steamID,userdata)
    dialog.close()
    
    check_params(steam,paramstring)

if __name__ == "__main__":
    main(sys.argv[2][1:])
