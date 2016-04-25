import execjs
import requests

def load_fb_sdk():
    response = requests.get('https://connect.facebook.net/en_US/sdk.js')
    return execjs.compile(response.text)

class FBLogin:

    fbsdk = load_fb_sdk()

    def __init__(self):
        pass

if __name__ == 'main':
    vm = load_fb_sdk()
    print vm.eval("'Facebook SDK loaded successfully!\n'")
