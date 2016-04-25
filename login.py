import execjs
import requests

def load_fb_sdk():
    response = requests.get('https://connect.facebook.net/en_US/sdk.js')
    return execjs.compile(response.text)

def callback(response):
    if response.status == 'connected':
        # Logged into your app and into Facebook.
        pass
    elif response.status == 'not_authorized':
        # Logged into FB but not your app
        pass
    else:
        # Not logged into Facebook
        pass

class FBLogin:

    fbsdk = load_fb_sdk()

    def __init__(self):
        pass

vm = load_fb_sdk()

# Can't pass a function -- TypeError: not JSON serializable
vm.call("FB.login", callback)
#FB = vm.eval("FB")
#print FB
#print FB.login
