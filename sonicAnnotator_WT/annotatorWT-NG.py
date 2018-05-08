#!/usr/bin/python3

# config
CONFIG_FILE = "annotatorTD.yaml"
SONIC_ANN = ["sonic-annotator", "-l"]

# global reqs
import time
import vamp
import logging
import subprocess
from sepy.YSAPObject import *
from sepy.SEPAClient import *

# local reqs
from lib.ActHandler import *

# main
if __name__ == "__main__":

    ##############################################################
    #
    # Basic initialization
    #
    ##############################################################
    
    # initialize the logging system
    logger = logging.getLogger('annotatorWT')
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.debug("Logging subsystem initialized")

    # 1 - create an instance of the YSAP and the KP
    kp = SEPAClient(None, 40)
    ysap = YSAPObject(CONFIG_FILE, 40)

    ##############################################################
    #
    # Put TD into SEPA
    #
    ##############################################################
    
    # 2 - generate URIs
    thingName = "Sonic Annotator WT"
    thingURI = ysap.namespaces["qmul"] + "SonicAnnotatorWT"
    thingDescURI = ysap.namespaces["qmul"] + "SonicAnnotatorWT_TD"
    actionURI = ysap.namespaces["qmul"] + "execVampPlugin"
    actionName = "Exec Vamp Plugin"
    actionComment = "Exploit Sonic Annotator to run VAMP plugin"
    inDataSchema = ysap.namespaces["qmul"] + "inDS"
    outDataSchema = ysap.namespaces["qmul"] + "outDS"
    
    # 3 - init the web thing
    u = ysap.getUpdate("TD_INIT", {
        "thingName": " '%s' " % thingName,
        "thingURI": " <%s> " % thingURI,
        "thingDescURI": " <%s> " % thingDescURI
    })
    kp.update(ysap.updateURI, u)

    # 4 - add an action to the web thing
    u = ysap.getUpdate("TD_ADD_ACTION_GRAPH_INPUT_GRAPH_OUTPUT", {
        "thingDescURI": " <%s> " % thingDescURI,
        "actionURI": " <%s> " % actionURI,
        "actionName": " '%s' " % actionName,
        "actionComment": " '%s' " % actionComment,
        "inDataSchema": " <%s> " % inDataSchema,
        "outDataSchema": " <%s> " % outDataSchema
    })
    kp.update(ysap.updateURI, u)

    ##############################################################
    #
    # Subscribe to actions
    #
    ##############################################################

    # subscribe
    subText = ysap.getQuery("ACTION_REQUESTS",
                            {"thingURI": " <%s> " % thingURI,
                             "thingDescURI": " <%s> " % thingDescURI,
                             "actionURI": " <%s> " % actionURI })
    kp.subscribe(ysap.subscribeURI, subText, "actions", ActHandler(kp, ysap))

    # # 7 - subscribe to action requests
    # wt.waitForActions(ActionHandler)
    
    # 8 - wait, then destroy data
    logging.info("WebThing ready! Waiting for actions!")
    try:
        input("Press <ENTER> to close the WebThing")
    except KeyboardInterrupt:
        pass
    finally:
        logging.debug("Closing WebThing")

        # delete actions
        u = ysap.getUpdate("TD_DELETE_ACTION_GRAPH_INPUT_GRAPH_OUTPUT", {
            "thingDescURI": " <%s> " % thingDescURI,
            "actionURI": " <%s> " % actionURI
        })
        kp.update(ysap.updateURI, u)

        # delete TD
        u = ysap.getUpdate("TD_DELETE", {
            "thingURI": " <%s> " % thingURI
        })
        kp.update(ysap.updateURI, u)

        
