import requests
import re

from tronclass_cli.api.auth import AuthProvider, AuthError

LOGIN_URL = ("https://sso.tku.edu.tw/auth/realms/TKU/protocol/openid-connect/auth"
            "?client_id=pdsiclass&response_type=code&redirect_uri=https%3A//iclass.tku.edu.tw/login"
            "&state=L2lwb3J0YWw=&scope=openid,public_profile,email")

class TkuamAuthProvider(AuthProvider):
    desc = 'TKU SSO Identity Authentication'

    def __init__(self, session):
        super().__init__()
        self.session = session
        #self.session.verify = False # due to the tku unable pass verify by some random 3 party TCL
        self.session.headers.update({'Referer': 'https://iclass.tku.edu.tw/'})

    def check_login_success(self,response):
        content = response.text
        match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)

        if match and match.group(1) == "淡江大學單一登入(SSO)":
            return False
        else:
            return True

    def login(self, username:str, password:str):
        self.session.get("https://iclass.tku.edu.tw/login?next=/iportal&locale=zh_TW")
        self.session.get(LOGIN_URL)

        login_page_url = f"https://sso.tku.edu.tw/NEAI/logineb.jsp?myurl={LOGIN_URL}"
        login_page = self.session.get(login_page_url)
        
        jsessionid = login_page.cookies.get("AMWEBJCT!%2FNEAI!JSESSIONID")
        if not jsessionid:
            raise ValueError("無法取得 JSESSIONID")

        image_headers = {
            'Referer': 'https://sso.tku.edu.tw/NEAI/logineb.jsp',
            'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
        }
        
        self.session.get("https://sso.tku.edu.tw/NEAI/ImageValidate", headers=image_headers)
        post_headers = {
            'Origin': 'https://sso.tku.edu.tw',
            'Referer': 'https://sso.tku.edu.tw/NEAI/logineb.jsp'
        }
        
        body = {'outType': '2'}
        response = self.session.post("https://sso.tku.edu.tw/NEAI/ImageValidate", headers=post_headers, data=body)
        vidcode = response.text.strip()

        payload = {
            "myurl": LOGIN_URL,
            "ln": "zh_TW",
            "embed": "No",
            "vkb": "No",
            "logintype": "logineb",
            "username": username,
            "password": password,
            "vidcode": vidcode,
            "loginbtn": "登入"
        }
        login_url = f"https://sso.tku.edu.tw/NEAI/login2.do;jsessionid={jsessionid}?action=EAI"
        
        response = self.session.post(login_url, data=payload)
        
        if self.check_login_success(response) != True:
            raise AuthError()
        headers = {'Referer': login_url, 'Upgrade-Insecure-Requests': '1'}
        user_redirect_url = (
            f"https://sso.tku.edu.tw/NEAI/eaido.jsp?"
            f"am-eai-user-id={username}&am-eai-redir-url={LOGIN_URL}"
        )
        self.session.get(user_redirect_url, headers=headers)

        return self.session