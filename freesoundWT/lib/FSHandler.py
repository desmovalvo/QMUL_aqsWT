

#!/usr/bin/python3

# reqs
import json
import rdflib
import logging
import requests

# constants
NAMESEARCH_URL = "http://freesound.org/apiv2/search/text/?query=%s&token=%s&fields=id,url,download,name,previews&page=1&page_size=6"

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

            # cycle over added bindings to check that all the notifications
            # belongs to the same action instance
            instances = {}
            for a in added:
                instanceURI = a["actionInstance"]["value"]                
                if not instanceURI in instances:
                    instances[instanceURI] = []
                instances[instanceURI] = a                

            # cycle over instances:
            for instance in instances:
        
                # debug message
                logging.info("Search request #%s" % self.counter)
                
                # cycle over added bindings
                triples = []
                outputGraph = None
                for a in instances[instance]:
    
                    ##############################################################
                    #
                    # read the input
                    #
                    ##############################################################    
                    
                    # read the action configuration
                    # inValue is a string containing tags
                    # outValue is the URI for a graph
                    inputData = json.loads(a["inValue"]["value"])
                    outputGraph = a["outValue"]["value"]
                    logging.info("Action output will be in %s" % outputGraph)
    
                    ##############################################################
                    #
                    # search on freesound
                    #
                    ##############################################################    
                
                    searchPattern = "+".join(inputData["tags"])
                    try:
                        logging.info("Asking Freesound for songs matching %s" % searchPattern)
                        r = requests.get(NAMESEARCH_URL % (searchPattern, self.clientID), timeout=15)
                    except ConnectionError:
                        logging.error("Connection to Freesound failed")
                        break
                        
                    res = json.loads(r.text)
                    logging.info("Freesound says:")
                    if len(res["results"]) > 0:
                        for r in res["results"]:
                            logging.info(r["name"])
                    else:
                        logging.info("...no results!")
                            
                    ##############################################################
                    #
                    # SPARQL-generate
                    #
                    ##############################################################    
                        
                    # contacting the sparql generate server
                    searchuri = NAMESEARCH_URL % (searchPattern, self.clientID)
                    qText = self.ysap.getQuery("SPARQL_GENERATE_CONVERSION", {"searchURI": searchuri})
                    try:
                        response = requests.post('http://localhost:5000/sparqlgen', data={"query":qText}, timeout=15)
                    except ConnectionError:
                        logging.error("Connection to SPARQL-generate server failed")
                        break
    
                    sg_res = json.loads(response.text)
                    triples.append(getTripleListFromN3(sg_res["results"]))
    
                    
                # put results into SEPA
                if len(instances[instanceURI]) > 0:
                    tl = ".".join(triples)
                    updText = self.ysap.getUpdate("INSERT_SEARCH_RESPONSE",
                                                  { "graphURI": " <%s> " % outputGraph,
                                                    "instanceURI": " <%s> " % instance,
                                                    "tripleList": tl })
                    self.kp.update(self.ysap.updateURI, updText)
                    logging.info("Task completed!")
                
                
                # increment counter
                self.counter += 1
