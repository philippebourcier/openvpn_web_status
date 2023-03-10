OK, just wanted to try FastAPI (Python) on a basic use-case : display connected OpenVPN users.

Then, ended up adding admin capabilities...
Still a minimalist thing (running as root 😬) that should never be exposed on Internet.

To install :

```
cd /etc/openvpn/easy-rsa/
wget https://raw.githubusercontent.com/philippebourcier/openvpn_confs/main/vars
./easyrsa init-pki
./easyrsa build-ca nopass
./easyrsa build-server-full server nopass
./easyrsa gen-dh
./easyrsa gen-crl

wget -O/etc/openvpn/server/layer2.conf https://raw.githubusercontent.com/philippebourcier/openvpn_confs/main/layer2.conf
```
That last file is for a layer2 VPN (check full Tutorial at https://github.com/philippebourcier/openvpn_confs), but you can create your own config...
This is the static part of the final OVPN client file (a full OVPN file being a config file + the embedded certificates).

Update main.py with your own ADMIN_LOGIN and ADMIN_PASS.
If you change the layer2.conf file with something else, update the BASE_CONF variable too.
