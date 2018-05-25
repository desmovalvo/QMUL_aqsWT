#!/usr/bin/python3

# reqs
from sepy.SEPAClient import *
from sepy.YSAPObject import *
from lib.FSHandler import *
import configparser
import logging
import threading

# local reqs
from lib.utilities import *

# main
if __name__ == "__main__":

    ##############################################################
    #
    # Initialization
    #
    ##############################################################

    # initialize the logging system
    logger = logging.getLogger('freesoundWT')
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.debug("Logging subsystem initialized")
    
    # read freesound key
    config = configparser.ConfigParser()
    config.read("freesoundWT.conf")
    clientID = config["Freesound"]["clientId"]
    
    # create a new KP
    kp = SEPAClient(None, 40)

    # create an YSAPObject
    ysap = YSAPObject("freesoundTD.yaml", 40)

    # read the qmul namespace
    qmul = ysap.getNamespace("qmul")
    
    # create URIs and Literals for the thing and its TD
    thingName = "FreesoundWT"
    thingURI = getRandomURI(qmul)
    thingDescURI = getRandomURI(qmul)

    # ...for the action
    actionURI = getRandomURI(qmul)
    actionComment = "Search on Freesound"
    actionName = "searchByTags"
    inDataSchemaURI = getRandomURI(qmul)
    outDataSchemaURI = getRandomURI(qmul)

    # ...for the properties
    pingPropName = "Ping"
    pingPropURI = getRandomURI(qmul)
    pingPropData = getRandomURI(qmul)
    pingPropDataSchema = getRandomURI(qmul)
    
    ##############################################################
    #
    # Put the Thing Description into SEPA
    #
    ##############################################################

    fb = {
        "thingURI": " <%s> " % thingURI,
        "thingDescURI": " <%s> " % thingDescURI,
        "thingName":" '%s' " % thingName,
        "actionURI": " <%s> " % actionURI,
        "actionName": " '%s' " % actionName,
        "actionComment": " '%s' " % actionComment,         
        "inDataSchema": " <%s> " % inDataSchemaURI,
        "outDataSchema": " <%s> " % outDataSchemaURI,
        "pingPropURI": " <%s> " % pingPropURI,
        "pingPropName": " '%s' " % pingPropName,
        "pingPropData": " <%s> " % pingPropData,
        "pingPropDataSchema": " <%s> " % pingPropDataSchema
    }
    updText = ysap.getUpdate("THING_DESCRIPTION_UP", fb)
    kp.update(ysap.updateURI, updText)

    
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
    kp.subscribe(ysap.subscribeURI, subText, "actions", FSHandler(kp, ysap, clientID))

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
    # Wait for the end...
    #
    ##############################################################    

    logging.info("WebThing ready! Waiting for actions!")
    try:
       input("Press <ENTER> to close the WebThing")
       logging.debug("Closing WebThing")
       
    except KeyboardInterrupt:
       logging.debug("Closing WebThing")

    finally:
        
       # delete the thing description
       fb = {
           "thingURI": " <%s> " % thingURI,
           "thingDescURI": " <%s> " % thingDescURI,
           "thingName":" '%s' " % thingName,
           "actionURI": " <%s> " % actionURI,
           "actionName": " '%s' " % actionName,
           "actionComment": " '%s' " % actionComment,         
           "inDataSchema": " <%s> " % inDataSchemaURI,
           "outDataSchema": " <%s> " % outDataSchemaURI,
           "pingPropURI": " <%s> " % pingPropURI,
           "pingPropName": " '%s' " % pingPropName,
           "pingPropData": " <%s> " % pingPropData,
           "pingPropDataSchema": " <%s> " % pingPropDataSchema
       }
       updText = ysap.getUpdate("THING_DESCRIPTION_DOWN", fb)
       kp.update(ysap.updateURI, updText)
       
