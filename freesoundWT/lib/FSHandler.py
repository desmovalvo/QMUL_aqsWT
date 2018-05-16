#!/usr/bin/python3

# reqs
import json
import rdflib
import logging
import requests

# constants
NAMESEARCH_URL = "http://freesound.org/apiv2/search/text/?query=%s&token=%s&fields=id,url,download,name,previews&page=1&page_size=3"

class FSHandler:

    def __init__(self, kp, ysap, clientID):

        # initialize the logging system
        logger = logging.getLogger('freesoundWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for JamHandler")

        # initialize attributes
        self.clientID = clientID
        self.counter = 0
        self.ysap = ysap
        self.kp = kp


    def handle(self, added, removed):

        ##############################################################
        #
        # check if it is the confirm message
        #
        ##############################################################    
        
        if (self.counter == 0):

            # debug message
            logging.info("Subscription to actions correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:
            
            # debug message
            logging.info("Search request #%s" % self.counter)
            
            # cycle over added bindings
            triples = []
            instanceURI = None
            outputGraph = None
            for a in added:

                ##############################################################
                #
                # read the input
                #
                ##############################################################    
                
                # read the action configuration
                # inValue is a string containing tags
                # outValue is the URI for a graph
                instanceURI = a["actionInstance"]["value"]
                inputData = json.loads(a["inValue"]["value"])
                outputGraph = a["outValue"]["value"]
                logging.info("Action output will be in %s" % outputGraph)

                ##############################################################
                #
                # search on freesound
                #
                ##############################################################    
            
                searchPattern = "+".join(inputData["tags"])
                r = requests.get(NAMESEARCH_URL % (searchPattern, self.clientID))
                logging.info("Asking Freesound for songs matching %s" % searchPattern)
                res = json.loads(r.text)
                for r in res["results"]:
                    logging.info(r["name"])

                # experimental part -- contacting the local sparql generate server
                searchuri = NAMESEARCH_URL % (searchPattern, self.clientID)   
                query = """PREFIX ac: <http://audiocommons.org/ns/audiocommons#>
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                PREFIX iter: <http://w3id.org/sparql-generate/iter/>
                PREFIX fn: <http://w3id.org/sparql-generate/fn/>
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>                
                GENERATE { 
                  ?audioClip rdf:type ac:AudioClip .
                  ?audioClip ac:available_as ?audioFile .
                  ?audioClip dc:title ?title .
                  ?audioFile rdf:type ac:AudioFile
                }
                SOURCE <%s> AS ?source
                ITERATOR iter:JSONPath(?source,"$..results[*]") AS ?res
                WHERE {
                BIND(fn:JSONPath(?res, ".id" ) AS ?id)
                BIND(IRI(fn:JSONPath(?res, "url")) AS ?audioClip)
                BIND(IRI(fn:JSONPath(?res, "previews.preview-lq-ogg")) AS ?audioFile)
                BIND(fn:JSONPath(?res, "name") AS ?title)
                }""" % searchuri
                
                response = requests.post('http://localhost:5000/sparqlgen', data={"query":query})
                sg_res = json.loads(response.text)
                print(sg_res["result"])

                g = rdflib.Graph()
                g.parse(data=sg_res["result"], format="n3")
                for triple in g:
                    triple_string = " "
                    for field in triple:
                        if isinstance(field, rdflib.term.URIRef):
                            triple_string += " <%s> " % field
                        elif isinstance(field, rdflib.term.BNode):
                            triple_string += " _:%s " % field
                        else:
                            triple_string += " '%s' " % field
                    triples.append(triple_string)
                
            # put results into SEPA
            if len(added) > 0:
                tl = ".".join(triples)
                updText = self.ysap.getUpdate("INSERT_SEARCH_RESPONSE",
                                              { "graphURI": " <%s> " % outputGraph,
                                                "instanceURI": " <%s> " % instanceURI,
                                                "tripleList": tl })
                self.kp.update(self.ysap.updateURI, updText)                                               
                logging.info("Task completed!")
                
                
        # increment counter
        self.counter += 1
