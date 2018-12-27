from pdb import set_trace as T
import numpy as np

import sys
import json

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.python import log
from twisted.web.server import Site
from twisted.web.static import File

from autobahn.twisted.websocket import WebSocketServerFactory, \
    WebSocketServerProtocol

from autobahn.twisted.resource import WebSocketResource

def sign(x):
    return int(np.sign(x))

def move(orig, targ):
    ro, co = orig
    rt, ct = targ
    dr = rt - ro
    dc = ct - co
    if abs(dr) > abs(dc):
        return ro + sign(dr), co
    elif abs(dc) > abs(dr):
        return ro, co + sign(dc)
    else:
        return ro + sign(dr), co + sign(dc)

class EchoServerProtocol(WebSocketServerProtocol):
    def __init__(self):
        super().__init__()
        print("CREATED A SERVER")
        self.frame = 0
        self.packet = {'pos': {'0': (5, 0)} }

    def onOpen(self):
        print("Opened connection to server")
        self.realm = self.factory.realm
        self.frame += 1

        env = self.realm.envs[0]
        if len(env.desciples) > 0:
            idx = min(int(e) for e in env.desciples.keys())
            ent = env.desciples[str(idx)]
            pos = ent.client.pos
            data = {'pos': pos}

        data = self.packet
        packet = json.dumps(data).encode('utf8')
        self.sendMessage(packet, False)

        #packet = json.dumps(data).encode('utf8')
        #self.sendMessage(packet, True)

    def onClose(self, wasClean, code=None, reason=None):
        print('Connection closed')

    def onConnect(self, request):
        print("WebSocket connection request: {}".format(request))

    def onMessage(self, payload, isBinary):
        print("Message", payload)

        payload = json.loads(payload)
        #self.sendMessage(payload, isBinary)
        pos = payload['pos']

        data = self.packet
        for playerI in pos.keys():
            if playerI not in data["pos"]:
                data["pos"][playerI] = (0, 0)
            data["pos"][playerI] = move(data["pos"][playerI], pos[playerI])

        self.packet = data
        packet = json.dumps(data).encode('utf8')
        self.sendMessage(packet, False)

class WSServerFactory(WebSocketServerFactory):
    def __init__(self, ip, realm):
        super().__init__(ip)
        self.realm = realm

class Application:
    def __init__(self, realm, step):
        self.realm = realm
        data = {'pos':(0, 0)}
        #log.startLogging(sys.stdout)
        port = 8080

        #factory = WSServerFactory(u'ws://localhost:'+str(port), realm)
        factory = WSServerFactory(u"ws://127.0.0.1:8080", realm)
        #factory = WebSocketServerFactory(u"ws://127.0.0.1:8080")
        factory.protocol = EchoServerProtocol

        resource = WebSocketResource(factory)

        # we server static files under "/" ..
        root = File(".")

        # and our WebSocket server under "/ws" (note that Twisted uses
        # bytes for URIs)
        root.putChild(b"ws", resource)

        # both under one Twisted Web Site
        site = Site(root)

        lc = LoopingCall(step)
        lc.start(0.6)

        reactor.listenTCP(port, site)

        reactor.run()

