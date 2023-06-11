from cryptography.fernet import Fernet
T=None
i=open
G=print
from base64 import b64encode,b64decode
import os
import json
a=json.load
def v(palavra):
 l=K()
 N=b64decode(l)
 y=Fernet(N)
 J=y.encrypt(palavra.encode('utf8'))
 return J
def D(palavra=T):
 l=K()
 N=b64decode(l)
 y=Fernet(N)
 return y.decrypt(palavra).decode('utf8')
def K():
 with i('./chave.key','rb')as arquivo:
  l=arquivo.read()
  l=l.decode('utf8')
  return l.split('|')[1]
def F(cred):
 with i('pain.json','r')as arquivo:
  return D(a(arquivo)[cred])
if __name__=='__main__':
 G(F('client_id'))