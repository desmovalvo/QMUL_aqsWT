#!/usr/bin/python3

# reqs
import json
import time
import logging
import requests
from uuid import uuid4

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
            logging.info("Subscription to jamendo output correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:

            # debug message
            logging.info("JamendoWT completed its task!")

            # delete action request
            # self.kp.update(self.ysap.updateURI, self.ysap.getUpdate("DELETE_REQUEST", {"instance": " <%s> " % self.instance}))
            
            # set waiting to False
            self.waitValue = False

        self.counter += 1


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
            logging.info("Subscription to sonic output correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:

            # debug message
            logging.info("SonicWT completed its task!")

            # delete action request
            # self.kp.update(self.ysap.updateURI, self.ysap.getUpdate("DELETE_REQUEST", {"instance": " <%s> " % self.instance}))
            
            # set waiting to False
            self.waitValue = False

        self.counter += 1
        

class RecHandler:

    def __init__(self, kp, ysap):

        # initialize the logging system
        logger = logging.getLogger('recommenderWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for RecHandler")
        
        # initialize URIs of jamendo
        # TODO - this should be discovered automatically
        self.jamendoThingURI = ysap.getNamespace("qmul") + "JamendoWT"
        self.jamendoActionURI = ysap.getNamespace("qmul") + "searchAction"

        # initalize URIs of sonic
        # TODO - this should be discovered automatically
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
            logging.info("Subscription to actions correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:
            
            # debug message
            if len(added) > 0:
                logging.info("Recommendation request #%s" % self.counter)
            
            # cycle over added bindings
            for a in added:

                # save instance uri and in/out fields
                instanceURI = a["actionInstance"]["value"]
                inValue = a["inValue"]["value"]
                outValue = a["outValue"]["value"]

                # before invoking jamendo web thing, we subscribe to its output
                waitValue = True
                jamendoInstance = self.ysap.getNamespace("qmul") + str(uuid4())
                subText = self.ysap.getQuery("ACTION_COMPLETION_TIME", {"instance": " <%s> " % jamendoInstance})
                s =  SearchHandler(self.kp, self.ysap, waitValue, jamendoInstance)
                subid = self.kp.subscribe(self.ysap.subscribeURI, subText, "jamendo output", s)
                
                # invoke the jamendo web thing
                logging.info("Invoking Jamendo Web Thing")
                updText = self.ysap.getUpdate("INSERT_SEARCH_REQUEST", {"actionURI": " <%s> " % self.jamendoActionURI,
	                                                                "dataValue": " '%s' " % inValue,
	                                                                "instance": " <%s> "  % jamendoInstance,
                                                                        "graphURI": " <%s> "  % outValue });
                self.kp.update(self.ysap.updateURI, updText)

                # wait for completion of Jamendo's task
                while s.waitValue:                    
                    time.sleep(1)
                    
                # before invoking sonic web thing, we subscribe to its output
                waitValue = True
                sonicInstance = self.ysap.getNamespace("qmul") + str(uuid4())
                subText = self.ysap.getQuery("ACTION_COMPLETION_TIME", {"instance": " <%s> " % sonicInstance})
                s =  SonicHandler(self.kp, self.ysap, waitValue, sonicInstance)
                subid = self.kp.subscribe(self.ysap.subscribeURI, subText, "sonic output", s)
                    
                # invoke sonic annotator web thing
                logging.info("Invoking Sonic Annotator Web Thing")                
                updText = self.ysap.getUpdate("INSERT_SONIC_REQUEST", {"actionURI": " <%s> " % self.sonicActionURI,
	                                                    	       "instance": " <%s> "  % sonicInstance,
                                                                       "graphURI": " <%s> "  % outValue });
                self.kp.update(self.ysap.updateURI, updText)

                # wait for completion of Sonic's task
                while s.waitValue:
                    time.sleep(1)
                
                # # TODO - perform a SPARQL query to detect similarities
                # #        based on the output of sonic annotator

                # # TODO - delete from the graph non-similar files

                # perform a SPARQL update with the timestamp
                logging.info("Request recommendation completed!")
                updText = self.ysap.getUpdate("INSERT_REC_RESPONSE", { "instanceURI": " <%s> " % instanceURI })
                self.kp.update(self.ysap.updateURI, updText)                                               
                
                
        # increment counter
        self.counter += 1
