#!/usr/bin/python3

# global reqs
import os
import uuid
import vamp
import numpy
import logging
import librosa
import subprocess
from rdflib import *

# local reqs
from lib.utils import *

class ActionHandler:

    """This class is used to handle the action requests"""

    # constructor
    def __init__(self, kp, jsap):

        """Constructor of the handler"""

        # debug message
        logging.debug("ActionHandler::__init__() invoked")

        # working files and directories
        self.workDir = os.getcwd()
        self.outFile = self.workDir + "/.n3"
        self.n3File = self.workDir + "/lib/transform.n3"

        # store the kp and the jsap object
        self.jsap = jsap
        self.kp = kp
        

    def handle(self, added, removed):

        """This method is triggered every time a notification or a ping arrives"""

        # parse the message
        logging.debug(added)
        logging.debug(removed)
        
        # debug message
        logging.debug("ActionHandler::handle() invoked")

        # we need to get all data related to the action , the song name and the transform
        actionInstance = None
        transformUri = None
        songName = None
        
        # iterate over added building
        # TODO -- consider that we may receive multiple action requests with a notification
        #         but for the demo purposes it is not mandatory
        if len(added) > 0:
            for result in added:
                actionInstance = result["instance"]["value"]
                if result["fieldName"]["value"] == "transformUri":
                    transformUri = result["fieldValue"]["value"]
                if result["fieldName"]["value"] == "audio":
                    songName = result["fieldValue"]["value"]
                    print(songName)
    
            # get the transform!
            print(self.jsap.getQuery("GET_TRANSFORM_CONSTRUCT", {"transform": transformUri}))
            status, results =  self.kp.query(self.jsap.queryUri, self.jsap.getQuery("GET_TRANSFORM_CONSTRUCT", {"transform": transformUri}))
            getN3FromBindings(results["results"]["bindings"], self.n3File)
    
            # start the analysis
            logging.debug("ActionHandker::handle() -- performing analysis (workDir: %s)" % self.workDir)
            subprocess.run(["sonic-annotator", "-t", self.n3File, songName, "-w", "rdf", "--rdf-basedir", self.workDir, "--rdf-force"])        
            logging.debug("ActionHandker::handle() -- writing results")        
    
            # load the results into sepa by creating a new named graph
            namedGraphUri = self.jsap.namespaces["qmul"] + str(uuid.uuid4())
            outFile = ''.join(os.path.basename(songName).split('.')[:-1]) + ".n3"
            with open(outFile, "r") as f:
                g = Graph()
                result = g.parse(f, format="n3")
                upd = getUpdateFromGraph(result, namedGraphUri)
                self.kp.update(self.jsap.updateUri, upd)
                            
            # write data into SEPA
            self.kp.update(self.jsap.updateUri, self.jsap.getUpdate("ADD_COMPLETION_TIMESTAMP_WITH_OUTPUT", {
                "instance": actionInstance,
                "outputFieldValue": namedGraphUri,
                "outputFieldName": "output"
            }))
    
            # remove file
            logging.debug("ActionHandker::handle() -- removing output file")
            os.remove(outFile)
    
