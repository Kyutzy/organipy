from cryptography.fernet import Fernet
T=None
i=open
G=print
from base64 import b64encode,b64decode
J=b64decode
import json
a=json.load
def D(Z=T):
 l=K()
 N=b64decode(l)
 y=Fernet(N)
 return y.decrypt(Z).decode('utf8')
def K():
 with i(J(b'Li9jaGF2ZS5rZXk='),'r')as B:
  l=B.read()
  l=l.split('|')[1]
  return l
def F(P):
 with i(J(b'cGFpbi5qc29u'),'r')as B:
  return D(a(B)[P])