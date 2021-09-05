from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from fastapi.staticfiles import StaticFiles
import socket
import json

def get_vpn():
    ut=[]
    s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(("127.0.0.1",7505))
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

class User(BaseModel):
    CN: str
    RemoteIP: str
    LocalIP: str
    Bytes_Recv: int
    Bytes_Sent: int
    Connected_Since: str

class Users(BaseModel):
    usr: Optional[List[User]] = None

app=FastAPI()

@app.get("/ovpn",response_model=Users,response_model_exclude_unset=True)
async def root():
    return get_vpn()

app.mount("/", StaticFiles(directory="static",html=True), name="static")

