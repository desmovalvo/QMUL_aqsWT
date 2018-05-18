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
            logging.info("Subscription to completion of search action output correctly initialized")

        ##############################################################
        #
        # ...or a notification
        #
        ##############################################################    
            
        else:

            # debug message
            logging.info("Search action completed!")

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
                print(updText)
                print("==============================")

                ##########################################
                #
                # discovery
                #
                ##########################################

                search_things = []
                status, res = self.kp.query(self.ysap.queryURI, self.ysap.getQuery("DISCOVER_SEARCH_ACTION", {}))
                for r in res["results"]["bindings"]:
                    search_things.append(r["thing"]["value"])
                logging.info("Found %s web things with search capabilities" % len(search_things))
                
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
                    logging.info("Invoking Search Web Thing")
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
                qText = """prefix xsd: <http://www.w3.org/2001/XMLSchema#>
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dc: <http://purl.org/dc/elements/1.1/> 
                PREFIX mo: <http://purl.org/ontology/mo/>	
                PREFIX af: <http://purl.org/ontology/af/>
                PREFIX ac: <http://audiocommons.org/ns/audiocommons#> 
                PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
                SELECT DISTINCT ?audioFile ?title ?value ?refValue
                WHERE {{
                  GRAPH  <{graphURI}> {{                
                    ?audioClip rdf:type ac:AudioClip .
                    ?audioClip dc:title ?title .
                    ?audioClip ac:available_as ?audioFile .
                    ?audioFile rdf:type ac:AudioFile .
                    ?audioFile mo:encodes ?signal .
                    ?signal af:hasEvent ?event .
                    ?event rdfs:label "(mean value, continuous-time average)" .
                    ?event af:feature ?value .
                    ?refAudioClip rdf:type ac:AudioClip .
                    <{refAudioFile}> rdf:type ac:AudioFile .
                    ?refAudioClip ac:available_as <{refAudioFile}> .
                    <{refAudioFile}> mo:encodes ?refSignal .
                    ?refSignal af:hasEvent ?refEvent .
                    ?refEvent rdfs:label "(mean value, continuous-time average)" .
                    ?refEvent af:feature ?refValue .
                    FILTER (?audioClip != ?refAudioClip) 
                    FILTER (?value > ?refValue || ?value < ?refValue )
                    BIND ( ((xsd:float(?refValue)) + (xsd:float(?refValue)) * 25 / 100) AS ?high )
                    BIND ( ((xsd:float(?refValue)) - (xsd:float(?refValue)) * 25 / 100) AS ?low )
                    FILTER ( xsd:float(?value) > ?low && xsd:float(?value) < ?high )
                    }}
                }}""".format(graphURI = outValue, refAudioFile = audioFile)
                print(qText)
                status, res = self.kp.query(self.ysap.queryURI, qText)
                print(res)

                # # TODO - perform a SPARQL query to detect similarities
                # #        based on the output of sonic annotator
                uText = """prefix xsd: <http://www.w3.org/2001/XMLSchema#>
                prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                PREFIX dc: <http://purl.org/dc/elements/1.1/> 
                PREFIX mo: <http://purl.org/ontology/mo/>	
                PREFIX af: <http://purl.org/ontology/af/>
                PREFIX ac: <http://audiocommons.org/ns/audiocommons#> 
                PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
                PREFIX rec:<http://purl.org/ontology/rec/core#>
                INSERT {{
                  GRAPH <{graphURI}> {{
                    ?recURI rdf:type rec:Recommendation .
                    ?audioClip rec:recommended_in ?recURI
                  }}
                }}
                WHERE {{
                  GRAPH  <{graphURI}> {{                
                    ?audioClip rdf:type ac:AudioClip .
                    ?audioClip dc:title ?title .
                    ?audioClip ac:available_as ?audioFile .
                    ?audioFile rdf:type ac:AudioFile .
                    ?audioFile mo:encodes ?signal .
                    ?signal af:hasEvent ?event .
                    ?event rdfs:label "(mean value, continuous-time average)" .
                    ?event af:feature ?value .
                    ?refAudioClip rdf:type ac:AudioClip .
                    <{refAudioFile}> rdf:type ac:AudioFile .
                    ?refAudioClip ac:available_as <{refAudioFile}> .
                    <{refAudioFile}> mo:encodes ?refSignal .
                    ?refSignal af:hasEvent ?refEvent .
                    ?refEvent rdfs:label "(mean value, continuous-time average)" .
                    ?refEvent af:feature ?refValue .
                    FILTER (?audioClip != ?refAudioClip) 
                    FILTER (?value > ?refValue || ?value < ?refValue )
                    BIND ( ((xsd:float(?refValue)) + (xsd:float(?refValue)) * 25 / 100) AS ?high )
                    BIND ( ((xsd:float(?refValue)) - (xsd:float(?refValue)) * 25 / 100) AS ?low )
                    FILTER ( xsd:float(?value) > ?low && xsd:float(?value) < ?high )
                    BIND(IRI(CONCAT('rec:rec_',STR(NOW()))) as ?recURI)               
                  }}
                }}""".format(graphURI = outValue, refAudioFile = audioFile)
                print(uText)
                self.kp.update(self.ysap.updateURI, uText)
                print(res)

                
                # # TODO - delete from the graph non-similar files

                # perform a SPARQL update with the timestamp
                logging.info("Request recommendation completed!")
                updText = self.ysap.getUpdate("INSERT_REC_RESPONSE", { "instanceURI": " <%s> " % instanceURI })
                self.kp.update(self.ysap.updateURI, updText)                                               
                
                
        # increment counter
        self.counter += 1
