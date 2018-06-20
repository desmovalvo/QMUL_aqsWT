#!/usr/bin/python3

# reqs
import time
import rdflib
from uuid import uuid4


def pingWorker(kp, ysap, pingPropData, interval=5):
    
    # endless loop
    while True:

        # wait...
        time.sleep(interval)

        # update the ping
        fb = {
            "pingPropData": " <%s> " % pingPropData,
            "newPingPropValue": " '%s' " % str(time.time())
        }
        updText = ysap.getUpdate("UPDATE_PING", fb)
        kp.update(ysap.updateURI, updText)


def getRandomURI(namespace):

    return namespace + str(uuid4())


def getTripleListFromN3(n3):

    # parse graph
    g = rdflib.Graph()
    g.parse(data=n3, format="n3")

    # iterate over the graph to get triples
    triples = []
    for triple in g:
        triple_string = " "
        for field in triple:
            if isinstance(field, rdflib.term.URIRef):
                triple_string += " <%s> " % field
            elif isinstance(field, rdflib.term.BNode):
                triple_string += " _:%s " % field
            else:
                triple_string += " '%s' " % field.replace("'", "\\'")
        triples.append(triple_string)
    return(triples)

