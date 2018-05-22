#!/usr/bin/python3

# reqs
import json
import time
import logging
import requests
from uuid import uuid4
from termcolor import colored

class SearchHandler:

    def __init__(self, kp, ysap, waitValue, instance):

        # initialize the logging system
        logger = logging.getLogger('recommenderWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for SearchHandler")
                
        # initialize attributes
        self.counter = 0
        self.ysap = ysap
        self.kp = kp
        self.waitValue = waitValue
        self.instance = instance

    def handle(self, added, removed):

        ##############################################################
        #
        # check if it is the confirm message
        #
        ##############################################################    

        if (self.counter == 0):

            # debug message
            logging.debug("Subscription to completion of search action output correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:

            # debug message
            logging.debug("Search action completed!")

            # delete action request
            # self.kp.update(self.ysap.updateURI, self.ysap.getUpdate("DELETE_REQUEST", {"instance": " <%s> " % self.instance}))
            
            # set waiting to False
            self.waitValue = False

        self.counter += 1
        return


class SonicHandler:

    def __init__(self, kp, ysap, waitValue, instance):

        # initialize the logging system
        logger = logging.getLogger('recommenderWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for SonicHandler")
                
        # initialize attributes
        self.counter = 0
        self.ysap = ysap
        self.kp = kp
        self.waitValue = waitValue
        self.instance = instance

    def handle(self, added, removed):

        ##############################################################
        #
        # check if it is the confirm message
        #
        ##############################################################    

        if (self.counter == 0):

            # debug message
            logging.debug("Subscription to sonic output correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:

            # debug message
            logging.debug("SonicWT completed its task!")

            # delete action request
            # self.kp.update(self.ysap.updateURI, self.ysap.getUpdate("DELETE_REQUEST", {"instance": " <%s> " % self.instance}))
            
            # set waiting to False
            self.waitValue = False

        self.counter += 1
        return
        

class RecHandler:

    def __init__(self, kp, ysap):

        # initialize the logging system
        logger = logging.getLogger('recommenderWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for RecHandler")

        # initialize URI for search actions
        self.searchActionURI = ysap.getNamespace("qmul") + "searchAction"
                
        # initialize URIs of sonic
        self.sonicThingURI = ysap.getNamespace("qmul") + "SonicAnnotatorWT"
        self.sonicActionURI = ysap.getNamespace("qmul") + "execVampPlugin"
        
        # initialize attributes
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
            logging.debug("Subscription to actions correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:
            
            # debug message
            if len(added) > 0:
                logging.debug("Recommendation request #%s" % self.counter)
            
            # cycle over added bindings
            for a in added:

                ##########################################
                #
                # preliminary stuff
                #
                ##########################################
                
                # save instance uri and in/out fields
                instanceURI = a["actionInstance"]["value"]
                inValue = a["inValue"]["value"]
                outValue = a["outValue"]["value"]

                # the request contains also the song for which the recommendation is requested
                # so we need to map this song into SEPA
                song = json.loads(a["inValue"]["value"])
                audioFile = song["details"]["previews"]["preview-lq-ogg"]
                audioClip = song["details"]["url"]
                name = song["details"]["name"]
                
                updText = """PREFIX ac:    <http://audiocommons.org/ns/audiocommons#> 
                PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
                PREFIX dc:    <http://purl.org/dc/elements/1.1/> 
                INSERT DATA {{ GRAPH <{graphURI}> {{
                <{audioClip}> dc:title '{name}' .
                <{audioClip}> rdf:type ac:AudioClip .
                <{audioClip}> ac:available_as <{audioFile}> .
                <{audioFile}> rdf:type ac:AudioFile }}
                }}""".format(audioClip = audioClip, audioFile = audioFile, name = name, graphURI = outValue)
                self.kp.update(self.ysap.updateURI, updText)

                ##########################################
                #
                # discovery
                #
                ##########################################

                search_things = []
                status, res = self.kp.query(self.ysap.queryURI, self.ysap.getQuery("DISCOVER_SEARCH_ACTION", {}))
                for r in res["results"]["bindings"]:
                    search_things.append(r["thing"]["value"])
                logging.debug("Found %s web things with search capabilities" % len(search_things))
                
                ###########################################
                #
                # invocation of search/freesound/europeana
                #
                ###########################################

                waiting = []
                for thing in search_things:
                
                    # before invoking search web thing, we subscribe to its output
                    waitValue = True
                    searchInstance = self.ysap.getNamespace("qmul") + str(uuid4())
                    subText = self.ysap.getQuery("ACTION_COMPLETION_TIME", {"instance": " <%s> " % searchInstance})
                    s =  SearchHandler(self.kp, self.ysap, waitValue, searchInstance)
                    subid = self.kp.subscribe(self.ysap.subscribeURI, subText, "search output", s)
                
                    # invoke the search web thing
                    logging.debug("Invoking Search Web Thing")
                    updText = self.ysap.getUpdate("INSERT_SEARCH_REQUEST", {"thingURI": ' <%s> ' % thing,
                                                                            "actionURI": " <%s> " % self.searchActionURI,
	                                                                    "dataValue": " '%s' " % inValue,
	                                                                    "instance": " <%s> "  % searchInstance,
                                                                            "graphURI": " <%s> "  % outValue });
                    self.kp.update(self.ysap.updateURI, updText)
                    waiting.append(s)

                # wait for completion of Search's task
                while len(waiting) > 0:                    
                    time.sleep(1)
                    for w in waiting:
                        if not(w.waitValue):
                            i = waiting.index(w)
                            del waiting[i]
                    logging.debug("waiting...")
                    
                # before invoking sonic web thing, we subscribe to its output
                sonicInstance = self.ysap.getNamespace("qmul") + str(uuid4())
                subText = self.ysap.getQuery("ACTION_COMPLETION_TIME", {"instance": " <%s> " % sonicInstance})
                s =  SonicHandler(self.kp, self.ysap, waitValue, sonicInstance)
                subid = self.kp.subscribe(self.ysap.subscribeURI, subText, "sonic output", s)
                    
                # discover the best sonic instance
                qText = self.ysap.getQuery("BEST_SONIC_INSTANCE", {})
                status, res = self.kp.query(self.ysap.queryURI, qText)
                action = res["results"]["bindings"][0]["action"]["value"]
                
                # invoke sonic annotator web thing
                logging.debug("Invoking Sonic Annotator Web Thing")                
                updText = self.ysap.getUpdate("INSERT_SONIC_REQUEST", {"actionURI": " <%s> " % action,
	                                                    	       "instance": " <%s> "  % sonicInstance,
                                                                       "graphURI": " <%s> "  % outValue });
                self.kp.update(self.ysap.updateURI, updText)

                # wait for completion of Sonic's task
                while s.waitValue:
                    time.sleep(1)

                # perform a SPARQL update to detect similarities
                uText = self.ysap.getUpdate("TD_DETECT_SIMILARITIES", {"graphURI": " <%s> " % outValue,
                                                                       "refAudioFile": " <%s> " % audioFile})
                self.kp.update(self.ysap.updateURI, uText)

                # perform a SPARQL update with the timestamp
                updText = self.ysap.getUpdate("INSERT_REC_RESPONSE", { "instanceURI": " <%s> " % instanceURI })
                self.kp.update(self.ysap.updateURI, updText)
                logging.debug("Request recommendation completed!")
                                
        # increment counter
        self.counter += 1
