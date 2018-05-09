#!/usr/bin/python3

# reqs
import json
import logging
import requests

# constants
NAMESEARCH_URL = "http://freesound.org/apiv2/search/text/?query=%s&token=%s&fields=id,url,download,"

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
            for a in added:

                print(a)

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

                ##############################################################
                #
                # write results to SEPA
                #
                ##############################################################    

                # TODO -- use mappings!
                triples = []
                for r in res["results"]:                
                    triples.append(" <%s> rdf:type ac:AudioClip " % r["url"])
                    triples.append(" <%s> dc:title '%s' " % (r["url"], r["name"].replace("'", "")))
                    triples.append(" <%s> ac:available_as <%s>  " % (r["url"], r["audiodownload"]))
                    triples.append(" <%s> rdf:type ac:AudioFile " % r["download"])
                    logging.info(r["name"])
                tl = ".".join(triples)

                # put results into SEPA
                updText = self.ysap.getUpdate("INSERT_SEARCH_RESPONSE",
                                              { "graphURI": " <%s> " % outputGraph,
                                                "instanceURI": " <%s> " % instanceURI,
                                                "tripleList": tl })
                self.kp.update(self.ysap.updateURI, updText)                                               

            logging.info("Task completed!")
                
        # increment counter
        self.counter += 1
