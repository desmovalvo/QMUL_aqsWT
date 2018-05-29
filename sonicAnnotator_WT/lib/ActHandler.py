#!/usr/bin/python3

# reqs
import os
import vamp
import logging
import requests
import threading
import subprocess
from uuid import uuid4
from rdflib import Graph
from lib.utils import *
from termcolor import colored


class ActHandler:

    def __init__(self, kp, ysap):

        # logger
        logger = logging.getLogger('sonicWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for ActHandler")

        # attributes
        self.maxThreads = 5
        self.counter = 0
        self.ysap = ysap
        self.kp = kp

        
    def handle(self, added, removed):

        # check indication number
        if self.counter == 0:

            # skip initial results
            self.counter += 1

        else:

            # collect the notifications about the same instance
            instances = {}        
            for a in added:
                instanceURI = a["actionInstance"]["value"]
                if not instanceURI in instances:
                    instances[instanceURI] = []
                instances[instanceURI].append(a)

            # iterate over instances
            for instance in instances:

                # increment counter
                self.counter += 1
                            
                # debug message
                if len(added) > 0:
                    logging.debug("Invoked sonic annotator (request #%s)" % self.counter)
    
                # cycle over added bindings
                for a in instances[instance]:
    
                    # update the load
                    utext = self.ysap.getUpdate("INCREMENT_LOAD", {})
                    self.kp.update(self.ysap.updateURI, utext)                
                    
                    # read the action input                
                    instanceURI = a["actionInstance"]["value"]
                    inputData = a["inValue"]["value"]
                    outputGraph = a["outValue"]["value"]
    
                    # create a lock
                    lock = threading.Lock()
                    
                    # with a query get all the songs
                    qtext = self.ysap.getQuery("SONGS", {"graphURI": " <%s> " % outputGraph})
                    status, res = self.kp.query(self.ysap.queryURI, qtext)
    
                    # list of threads
                    threads = []
                    
                    for r in res["results"]["bindings"]:
    
                        def worker(r, lock):
                            
                            # read notification data
                            songName = r["title"]["value"]
                            songFileUri = r["audioFile"]["value"]
                            songClipUri = r["audioClip"]["value"]
    
                            # download audio file
                            response = requests.get(songFileUri, stream=True)
                            localFile = str(uuid4())
                            open(localFile, "wb").write(response.content)
    
                            # analysis with sonic...
                            logging.debug("Analysing song " + songFileUri)
                            
                            try:
    
                                # acquire the lock
                                lock.acquire()
                                
                                # invoke sonic
                                subprocess.run(["sonic-annotator", "-t", "linearcentroid.n3", localFile, "--summary", "mean", "-w", "rdf", "--rdf-force", "-q", "--rdf-track-uri", songFileUri])        
                                logging.debug("Writing results for song " + songFileUri)
    
                                # read the file .n3 and put everything into the named graph
                                g = Graph()
                                inputFilename = localFile + ".n3"                        
                                with open(inputFilename, "r") as f:
    
                                    # parse the result in a local, volatile graph
                                    result = g.parse(f, format="n3")
    
                                    # perform a SPARQL update on the graph g to add the link between:
                                    # the audioFile (the one passed by Jamendo, not the one downloaded by Sonic) and
                                    # the mean value
                                    g.update(self.ysap.getUpdate("LOCAL_FIX", {"newAudioFile":" <%s> " % songFileUri}))
    
                                    # copy the local graph to the SEPA store
                                    upd = getUpdateFromGraph(result, outputGraph)
                                    self.kp.update(self.ysap.updateURI, upd)
    
                                # remove the audio file and the .n3 file
                                os.remove(localFile)
                                os.remove(inputFilename)
                                
                            except:
                                logging.error("Error during analysis")
    
                            finally:
                                
                                # release the lock
                                lock.release()
    
                        # start threads                    
                        t = threading.Thread(target=worker, args=(r, lock))
                        threads.append(t)
                        t.setDaemon(True)
                        t.start()
    
                    for t in threads:
                        t.join()
                            
                    # sparql update to write completion time and decrement the workload 
                    updText = self.ysap.getUpdate("INSERT_SONIC_RESPONSE",
                                                  { "graphURI": " <%s> " % outputGraph,
                                                    "instanceURI": " <%s> " % instanceURI })
                    self.kp.update(self.ysap.updateURI, updText)                                               
    
                    # debug message
                    logging.debug("Results of request #%s in named graph <%s>" % (self.counter, outputGraph))
