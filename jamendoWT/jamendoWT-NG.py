#!/usr/bin/python3

# global reqs
from sepy.SEPAClient import *
from sepy.YSAPObject import *
from lib.JamHandler import *
import configparser
import logging

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
    logger = logging.getLogger('jamendoWT')
    logging.basicConfig(format='[%(levelname)s] %(message)s', level=logging.DEBUG)
    logging.debug("Logging subsystem initialized")
    
    # read jamendo key
    config = configparser.ConfigParser()
    config.read("jamendoWT.conf")
    clientID = config["Jamendo"]["clientId"]
    searchLimit = config["Jamendo"]["limit"]

    # create a new KP
    kp = SEPAClient(None, 40)

    # create an YSAPObject
    if len(sys.argv) < 2:
        sys.exit("You need to specify a yaml configuration file!")
    yamlFile = sys.argv[1]
    ysap = YSAPObject(yamlFile, 40)
    
    # create URIs and Literals for
    # 1 - thing and thingDescription
    thingName = "Jamendo WT"
    thingURI = getRandomURI(qmul) 
    thingDescURI = getRandomURI(qmul)

    # 2 - search action
    actionName = "searchByTags"
    actionURI = getRandomURI(qmul)
    actionComment = "Search on Jamendo"
    indataSchemaURI = getRandomURI(qmul)
    outdataSchemaURI = getRandomURI(qmul)

    # 2 - ping property
    pingPropName = "Ping"
    pingPropURI = getRandomURI(qmul)
    pingPropData = getRandomURI(qmul)
    pingPropDataSchema = getRandomURI(qmul)


    ##############################################################
    #
    # Put the Thing Description into SEPA
    #
    ##############################################################
    
    # get the first update (TD_INIT)
    updText = ysap.getUpdate("TD_INIT",
                             {"thingURI": " <%s> " % thingURI,
                              "thingDescURI": " <%s> " % thingDescURI,
                              "thingName":" ' <%s> ' " % thingName})
    kp.update(ysap.updateURI, updText)
    
    # get the second update (TD_ADD_ACTION_STRING_INPUT_GRAPH_OUTPUT)
    updText = ysap.getUpdate("TD_ADD_ACTION_STRING_INPUT_GRAPH_OUTPUT",
                             {"thingDescURI": " <%s> " % thingDescURI,
                              "actionURI": " <%s> " % actionURI,
                              "actionName": " '<%s>' "  % actionName,                              
                              "inDataSchema": " <%s> " % indataSchemaURI,
                              "outDataSchema": " <%s> " % outdataSchemaURI,
                              "actionComment": " '<%s>' " % actionComment })
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
    kp.subscribe(ysap.subscribeURI, subText, "actions", JamHandler(kp, ysap, clientID, searchLimit))

    ##############################################################
    #
    # Wait for the end...
    #
    ##############################################################    

    logging.debug("WebThing ready! Waiting for actions!")
    try:
       input("Press <ENTER> to close the WebThing")
       logging.debug("Closing WebThing")

       # delete action and instances
       updText = ysap.getUpdate("TD_DELETE_ACTION_STRING_INPUT_GRAPH_OUTPUT",
                                {"thingDescURI": " <%s> " % thingDescURI,
                                 "actionURI": " <%s> " % actionURI,
                                })
       kp.update(ysap.updateURI, updText)
       
       # delete thing description
       updText = ysap.getUpdate("TD_DELETE",
                                {"thingURI": " <%s> " % thingURI})
       kp.update(ysap.updateURI, updText)
       
    except KeyboardInterrupt:
       logging.debug("Closing WebThing")
