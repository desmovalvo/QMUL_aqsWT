#!/usr/bin/python3

# reqs
import os
import vamp
import numpy
import librosa
import os.path
import logging
import requests
import threading
import subprocess
from uuid import uuid4
from rdflib import Graph
from lib.utils import *


class ActHandler:

    def __init__(self, kp, ysap, clientID):

        # logger
        logger = logging.getLogger('sonicWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for ActHandler")

        # attributes
        self.clientID = clientID
        self.counter = 0
        self.ysap = ysap
        self.kp = kp

        
    def handle(self, added, removed):

        # check indication number
        if self.counter == 0:

            # skip initial results
            pass

        else:

            # debug message
            if len(added) > 0:
                logging.debug("Invoked sonic annotator (request #%s)" % self.counter)

            # cycle over added bindings
            for a in added:

                # read the action input                
                instanceURI = a["actionInstance"]["value"]
                inputData = a["inValue"]["value"]
                outputGraph = a["outValue"]["value"]
                
                # with a query get the transform
            
                # with a query get all the songs
                qtext = self.ysap.getQuery("SONGS", {"graphURI": " <%s> " % outputGraph})
                print(qtext)
                status, res = self.kp.query(self.ysap.queryURI, qtext)
                
                for r in res["results"]["bindings"]:
                    
                    # NOTE:
                    # this is the *old* way to use a vamp plugin, i.e. invoking sonic annotator as a subprocess
                    #
                    # invoke sonic
                    # 0. read notification data
                    songName = r["title"]["value"]
                    songFileUri = r["audioFile"]["value"]
                    songClipUri = r["audioClip"]["value"]

                    # now we should download the file and provide it to sonic annotator
                    # we could provide the file directly, but unfortunately freesound requires auth
                    print("Analysing song " + songFileUri)
                    subprocess.run(["sonic-annotator", "-t", "linearcentroid.n3", songFileUri, "--summary", "mean", "-w", "rdf", "--rdf-force", "-q"])        
                    logging.debug("ActionHandker::handle() -- writing results")
                    
                    # read the file ".n3" and put everything into the named graph
                    g = Graph()
                    print(os.getcwd())
                    with open(os.path.basename(songFileUri).split(".")[0] + ".n3", "r") as f:
                        result = g.parse(f, format="n3")

                        # perform a SPARQL update on the graph g to add the link between:
                        # the audioFile (the one passed by Jamendo, not the one downloaded by Sonic) and
                        # the mean value

                        g.update("""prefix dc: <http://purl.org/dc/elements/1.1/>
                        PREFIX ac: <http://audiocommons.org/ns/audiocommons#> 
                        PREFIX mo: <http://purl.org/ontology/mo/>
                        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                        PREFIX afo: <http://purl.org/ontology/af/> 
                        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>                       
                        INSERT { ?signal afo:hasEvent ?event }
                        WHERE { 
                        ?audioFile mo:encodes ?signal . 
                        ?event rdfs:label "(mean value, continuous-time average)" . 
                        ?event afo:feature ?p 
                        }""")
                        upd = getUpdateFromGraph(result, outputGraph)
                        self.kp.update(self.ysap.updateURI, upd)                                               


                # TODO -- check the results!
                # now we should check the mean value and see the most similar.. 
                        
                # write completion time
                updText = self.ysap.getUpdate("INSERT_SONIC_RESPONSE",
                                              { "graphURI": " <%s> " % outputGraph,
                                                "instanceURI": " <%s> " % instanceURI })
                self.kp.update(self.ysap.updateURI, updText)                                               

                # debug message
                logging.debug("Results of request #%s in named graph <%s>" % (self.counter, outputGraph))


        # increment indication count
        self.counter += 1
