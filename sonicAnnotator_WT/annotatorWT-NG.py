#!/usr/bin/python3

# config
CONFIG_FILE = "annotatorTD.yaml"
SONIC_ANN = ["sonic-annotator", "-l"]

# global reqs
import time
import vamp
import logging
import subprocess
import configparser
from sepy.YSAPObject import *
from sepy.SEPAClient import *

# local reqs
from lib.ActHandler import *
from lib.utilities import *

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
    
    # generate URIs and literals for:
    logging.debug("Pushing Thing Description to SEPA")

    # 1 - thing and thing description
    thingName = "Sonic Annotator WT"
    thingURI = getRandomURI(ysap.namespaces["qmul"])
    thingDescURI = getRandomURI(ysap.namespaces["qmul"])

    # 2 - vamp plugin action
    actionName = "Exec Vamp Plugin"
    actionURI = getRandomURI(ysap.namespaces["qmul"])
    inDataSchema = getRandomURI(ysap.namespaces["qmul"])
    outDataSchema = getRandomURI(ysap.namespaces["qmul"])
    actionComment = "Exploit Sonic Annotator to run VAMP plugin"

    # 3 - vamp plugin property
    plugPropName = "Vamp Plugin"
    plugPropURI = getRandomURI(ysap.namespaces["qmul"])
    plugPropData = getRandomURI(ysap.namespaces["qmul"])
    plugPropDataSchema = getRandomURI(ysap.namespaces["qmul"])

    # 4 - workload property
    wlPropName = "Workload"
    wlPropURI = getRandomURI(ysap.namespaces["qmul"]) 
    wlPropData = getRandomURI(ysap.namespaces["qmul"])
    wlPropDataSchema = getRandomURI(ysap.namespaces["qmul"])

    # 5 - ping property
    pingPropName = "Ping"
    pingPropURI = getRandomURI(ysap.namespaces["qmul"])
    pingPropData = getRandomURI(ysap.namespaces["qmul"])
    pingPropDataSchema = getRandomURI(ysap.namespaces["qmul"])

    # set the forced bindings
    fb = {
        "thingURI": " <%s> " % thingURI,
        "thingName": " '%s' " % thingName,
        "thingDescURI": " <%s> " % thingDescURI,
        "plugPropURI": " <%s> " % plugPropURI,
        "plugPropData": " <%s> " % plugPropData,
        "plugPropName": " '%s' " % plugPropName,
        "plugPropValue": " '%s' " % ",".join(vamp.list_plugins()),
        "plugPropDataSchema": " <%s> " % plugPropDataSchema,
        "wlPropURI": " <%s> " % wlPropURI,
        "wlPropData": " <%s> " % wlPropData,
        "wlPropName": " '%s' " % wlPropName,
        "wlPropValue": " '0' ",
        "wlPropDataSchema": " <%s> " % wlPropDataSchema,
        "pingPropURI": " <%s> " % pingPropURI,
        "pingPropData": " <%s> " % pingPropData,
        "pingPropName": " '%s' " % pingPropName,
        "pingPropDataSchema": " <%s> " % pingPropDataSchema,
        "pingPropValue": " '%s' " % str(time.time()),
        "actionURI": " <%s> " % actionURI,
        "actionName": " '%s' " % actionName,
        "actionComment": " '%s' " % actionComment,
        "inDataSchema": " <%s> " % inDataSchema,
        "outDataSchema": " <%s> " % outDataSchema,
    }

    # push the thing description
    u = ysap.getUpdate("THING_DESCRIPTION_UP", fb)
    kp.update(ysap.updateURI, u)
    logging.debug("Thing URI: %s" % thingURI)

    
    ##############################################################
    #
    # Start a Ping thread
    #
    ##############################################################    
        
    t = threading.Thread(target = pingWorker, args = (kp, ysap, pingPropData))
    t.setDaemon(True)
    t.start()

    
    ##############################################################
    #
    # Subscribe to actions
    #
    ##############################################################

    # 7 . subscribe
    logging.debug("Subscribing to action requests")
    subText = ysap.getQuery("ACTION_REQUESTS",
                            {"thingURI": " <%s> " % thingURI,
                             "thingDescURI": " <%s> " % thingDescURI,
                             "actionURI": " <%s> " % actionURI })
    kp.subscribe(ysap.subscribeURI, subText, "actions", ActHandler(kp, ysap))

    # 8 - wait, then destroy data
    logging.info("WebThing ready! Waiting for actions!")
    try:
        input("Press <ENTER> to close the WebThing")
    except KeyboardInterrupt:
        pass
    finally:
        logging.debug("Closing WebThing")

        # set the forced bindings
        fb = {
            "thingURI": " <%s> " % thingURI,
            "thingName": " '%s' " % thingName,
            "thingDescURI": " <%s> " % thingDescURI,
            "plugPropURI": " <%s> " % plugPropURI,
            "plugPropData": " <%s> " % plugPropData,
            "plugPropName": " '%s' " % plugPropName,
            "plugPropValue": " '%s' " % ",".join(vamp.list_plugins()),
            "plugPropDataSchema": " <%s> " % plugPropDataSchema,
            "wlPropURI": " <%s> " % wlPropURI,
            "wlPropData": " <%s> " % wlPropData,
            "wlPropName": " '%s' " % wlPropName,
            "wlPropValue": " '0' ",
            "wlPropDataSchema": " <%s> " % wlPropDataSchema,
            "pingPropURI": " <%s> " % pingPropURI,
            "pingPropData": " <%s> " % pingPropData,
            "pingPropName": " '%s' " % pingPropName,
            "pingPropDataSchema": " <%s> " % pingPropDataSchema,
            "actionURI": " <%s> " % actionURI,
            "actionName": " '%s' " % actionName,
            "actionComment": " '%s' " % actionComment,
            "inDataSchema": " <%s> " % inDataSchema,
            "outDataSchema": " <%s> " % outDataSchema,
        }
        
        # delete the thing description
        u = ysap.getUpdate("THING_DESCRIPTION_DOWN", fb)
        kp.update(ysap.updateURI, u)
