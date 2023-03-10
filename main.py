import os
from time import sleep
import secrets
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional,List
from fastapi.staticfiles import StaticFiles
import socket
import random
import string

######## CONFIG ###############################
ADMIN_LOGIN="set_me"
ADMIN_PASS="change-me"
###
DEBUG=False
ROOT="/etc"
CA_DIR=ROOT+"/openvpn/easy-rsa/pki/"
OVPN_DIR=ROOT+"/openvpn/server/"
EASYRSA=ROOT+"/openvpn/easy-rsa/easyrsa"
BASE_CONF=OVPN_DIR+"layer2.conf"
CA_FILE=CA_DIR+"ca.crt"
###############################################

# DEBUG
STDNULL=""
if DEBUG: STDNULL=" >/dev/null 2>&1"

app=FastAPI()
security = HTTPBasic()

def merge_cert_config(username): 
    CLIENT_CERT=CA_DIR+"inline/"+username+".inline"
    # Test if files exists and are readable
    for file in [ BASE_CONF, CLIENT_CERT ]:
        if os.path.isfile(file):
            if DEBUG: print("Testing if "+file+" exists.")
            with open(file,"r") as fp:
                if not fp.readable(): return False
                if DEBUG: print("Testing if "+file+" exists : OK")
        else: return False
    # Concatenate files
    fo=open("/run/vpn-"+username+".ovpn","x")
    with open(BASE_CONF,"r") as fp: fo.write(fp.read())
    with open(CLIENT_CERT,"r") as fp: fo.write(fp.read())
    fo.close()
    if DEBUG: print("Merge CONFIG and CERT : done")
    return True

def new_user(username,password=""):
    if not username.isalnum(): return { "user" : "Fatal error", "password" : "Username should be only alphanumeric." }
    if password=="":
        os.system(EASYRSA+" --vars="+CA_DIR+"vars --pki-dir="+CA_DIR+" --batch build-client-full "+username+" nopass"+STDNULL)
    else:
        os.system(EASYRSA+" --vars="+CA_DIR+"vars --pki-dir="+CA_DIR+" --batch --passout=pass:"+password+" build-client-full "+username+STDNULL)
    sleep(1)
    os.system(EASYRSA+" --vars="+CA_DIR+"vars --pki-dir="+CA_DIR+" --batch gen-crl"+STDNULL)
    sleep(1)
    os.system("/usr/sbin/service openvpn reload"+STDNULL)
    if merge_cert_config(username): return { "user" : username, "password" : password }
    else: return { "user" : "Fatal error", "password" : "Failed to merge certificate" }

def del_user(username):
    if not username.isalnum(): return { "user" : "Fatal error" }
    os.system(EASYRSA+" --vars="+CA_DIR+"vars --pki-dir="+CA_DIR+" --batch revoke "+username+STDNULL)
    sleep(1)
    os.system(EASYRSA+" --vars="+CA_DIR+"vars --pki-dir="+CA_DIR+" --batch gen-crl"+STDNULL)
    sleep(1)
    os.system("/usr/sbin/service openvpn reload"+STDNULL)
    return { "user" : username }

def get_vpn():
    ut=[]
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1",7505))
    except socket.error:
        raise HTTPException(status_code=400,detail="OpenVPN is not running")
    s.setblocking(False)
    s.send("status\r\n".encode("utf-8"))
    sf=s.makefile(mode='r',encoding='utf-8')
    while True:
        line=sf.readline()
        if line[:11]=="CLIENT_LIST":
            data=line.split(",")
            ut.append({"CN": data[1],"RemoteIP": data[2],"LocalIP": data[3],"Bytes_Recv": data[5],"Bytes_Sent": data[6],"Connected_Since": data[7]})
        if line[:3]=="END": break
    s.close()
    return { "usr" : ut }

def get_user():
    ul=[]
    with open(CA_DIR+'index.txt', 'r') as f:
        lines = f.read().splitlines()
        for line in lines:
            data=line.split('\t')
            if data[5]!="/CN=server":
                if data[0]=="V": data[0]="true"
                ul.append({"CN": data[5].split("=")[1],"State": data[0]})
    return { "usr" : ul } 

def gen_pass():
    characters = string.ascii_letters + string.digits 
    return ''.join(random.choice(characters) for i in range(8))

def check_cred(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username.encode("utf8"),ADMIN_LOGIN.encode("utf8"))
    is_correct_password = secrets.compare_digest(credentials.password.encode("utf8"),ADMIN_PASS.encode("utf8"))
    if not (is_correct_username and is_correct_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Incorrect login or password",headers={"WWW-Authenticate": "Basic"})
    return True

class User(BaseModel):
    CN: str
    RemoteIP: str
    LocalIP: str
    Bytes_Recv: int
    Bytes_Sent: int
    Connected_Since: str

class Users(BaseModel):
    usr: Optional[List[User]] = None

class UserList(BaseModel):
    CN: str
    State: str

class UsersList(BaseModel):
    usr: Optional[List[UserList]] = None

## API & Static

@app.get("/ovpn",response_model=Users,response_model_exclude_unset=True,dependencies=[Depends(check_cred)])
async def root():
    return get_vpn()

@app.get("/listusr",response_model=UsersList,response_model_exclude_unset=True,dependencies=[Depends(check_cred)])
async def root():
    return get_user()

@app.get("/delusr",dependencies=[Depends(check_cred)])
async def root(user: str = ""):
    return del_user(user)

@app.get("/newusr",dependencies=[Depends(check_cred)])
async def root(user: str = "", nopass: bool = False):
    if user=="": return
    if nopass: return new_user(user)
    else: return new_user(user,gen_pass())

@app.get("/dl",dependencies=[Depends(check_cred)])
async def root(user: str = ""):
    if not os.path.isfile("/run/vpn-"+user+".ovpn"): merge_cert_config(user)
    return FileResponse("/run/vpn-"+user+".ovpn")

@app.get("/",dependencies=[Depends(check_cred)])
async def root():
    return FileResponse("./static/index.html")

@app.get("/js/main.js",dependencies=[Depends(check_cred)])
async def root():
    return FileResponse("./static/js/main.js")

# no auth for other JS/CSS, because who cares...
app.mount("/",StaticFiles(directory="static",html=True),name="static")

