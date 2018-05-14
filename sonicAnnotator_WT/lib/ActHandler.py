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
from rdflib import Graph
from lib.utils import *


class ActHandler:

    def __init__(self, kp, ysap):

        # logger
        logger = logging.getLogger('sonicWT')
        logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
        logging.debug("Logging subsystem initialized for ActHandler")

        # attributes
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
            logging.debug("Invoked sonic annotator (request #%s)" % self.counter)

            # cycle over added bindings
            threads = []                
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
                    # # invoke sonic
                    # # TODO - we use a temporary n3 file.. change it
                    # songName = r["audioFile"]["value"]
                    # songUri = r["audioClip"]["value"]
                    # subprocess.run(["sonic-annotator", "-t", "/home/val/QMUL/examples/ex01_sonicAnnotator/ampFoll", songName, "--summary", "mean", "-w", "rdf", "--rdf-force", "-q", "--rdf-track-uri", songUri, "--segments", "0,5"])        
                    # logging.debug("ActionHandker::handle() -- writing results")
                    #
                    # # read the file ".n3" and put everything into the named graph
                    # with open(".n3", "r") as f:
                    #     g = Graph()
                    #     result = g.parse(f, format="n3")
                    #     upd = getUpdateFromGraph(result, outputGraph)
                    #     self.kp.update(self.ysap.updateURI, upd)

                    # NOTE:
                    # this is a *tricky* way that consists of downloading file, invoking vampy and writing audio features the way we need them

                    # 0. read notification data
                    songName = r["title"]["value"]
                    songFileUri = r["audioFile"]["value"]
                    songClipUri = r["audioClip"]["value"]                    
                    print(r)

                    # start a thread
                    def worker(songName, songFileUri):
                        
                        # 1. download file
                        songFile = "/tmp/" + songName
                        r = requests.get(songFileUri, verify=False)
                        with open(songFile, "wb") as f:
                            f.write(r.content)
                    
                        # 2. invoke vampy
                        data, rate = librosa.load(songFile)
                        res = vamp.collect(data, rate, "vamp-example-plugins:spectralcentroid")

                        # 3. calculate mean of linear centroid
                        mean = numpy.mean(res["vector"][1])
                    
                        # 4. write features

                        # 5. remove file
                        os.remove(songFile)
                    
                    t = threading.Thread(name='daemon', target=worker, args=(songName, songFileUri))
                    t.setDaemon(True)
                    logging.info("Starting thread")
                    threads.append(t)
                    t.start()

                # join threads
                for t in threads:
                    t.join()
                    
                # write completion time
                updText = self.ysap.getUpdate("INSERT_SONIC_RESPONSE",
                                              { "graphURI": " <%s> " % outputGraph,
                                                "instanceURI": " <%s> " % instanceURI })
                self.kp.update(self.ysap.updateURI, updText)                                               

                # debug message
                logging.debug("Results of request #%s in named graph <%s>" % (self.counter, outputGraph))


        # increment indication count
        self.counter += 1
