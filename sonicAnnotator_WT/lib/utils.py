#!/usr/bin/python3

# global reqs
from rdflib import *

def getN3FromBindings(bindings, filename):

    """This function is used to write an N3 file from
    bindings obtained with a SPARQL CONSTRUCT query"""

    # init an empty graph
    g = Graph()

    # iterate over bindings
    for binding in bindings:
    
        # subject
        s = None
        if binding["subject"]["type"] == "uri":
            s = URIRef(binding["subject"]["value"])
        else:
            s = BNode(binding["subject"]["value"])
            
        # predicate
        p = None
        if binding["predicate"]["type"] == "uri":
            p = URIRef(binding["predicate"]["value"])
        else:
            p = BNode(binding["predicate"]["value"])
        
        # object
        o = None
        if binding["object"]["type"] == "uri":
            o = URIRef(binding["object"]["value"])
        elif binding["object"]["type"] == "litearl":
            o = Literal(binding["object"]["value"])
        else:
            o = BNode(binding["object"]["value"])
        
        # triple
        g.add((s,p,o))

    # write the n3 file
    g.serialize(destination=filename, format='n3')


def getUpdateFromGraph(triples, graphUri = None):

    """This function is used to create the list of triple
    patterns to put into the SPARQL UPDATE request"""

    # initialize a dict for bnodes
    bnodes = {}

    # initialize SPARQL Update
    upd = "INSERT DATA { "
    if graphUri:
        upd += " GRAPH <%s> { " % graphUri
    
    for t in triples:

        # subject
        s = t[0]
        if isinstance(s, URIRef):
            upd += " <%s> " % str(s) 
        elif isinstance(s, BNode):
            if not str(s) in bnodes:
                bnodes[str(s)] = "_:" + str(len(bnodes))
            upd += " %s " % bnodes[str(s)]
        else:
            upd += " '%s' " % sanitize(str(s)) 
        
        # predicate
        p = t[1]
        if isinstance(p, URIRef):
            upd += " <%s> " % str(p) 
        elif isinstance(p, BNode):
            if not str(p) in bnodes:
                bnodes[str(p)] = "_:" + str(len(bnodes))
            upd += " %s " % bnodes[str(p)]
        
        # object
        o = t[2]
        if isinstance(o, URIRef):
            upd += " <%s> . " % str(o) 
        elif isinstance(o, BNode):
            if not str(o) in bnodes:
                bnodes[str(o)] = "_:" + str(len(bnodes))
            upd += " %s . " % bnodes[str(o)]
        else:            
            upd += " '%s' . " % sanitize(str(o))
        
    # finalize update
    upd += " }"
    if graphUri:
        upd += " }"

    # return
    return upd


def sanitize(s):

    """This function is mainly used to sanitize literals before
    insertion in a SPARQL UPDATE request"""

    s = s.replace(":", str(hex(ord(":"))))
    s = s.replace("'", str(hex(ord("'"))))
    s = s.replace('"', str(hex(ord('"'))))
    return s
