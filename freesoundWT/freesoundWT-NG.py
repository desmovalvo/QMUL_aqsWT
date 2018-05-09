#!/usr/bin/python3

# reqs
from sepy.SEPAClient import *
from sepy.YSAPObject import *
from lib.FSHandler import *
import configparser
import logging
            
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
    
    # create URIs for
    # - thing
    # - thingDescription
    # - search action
    # - search action input and output dataschema
    thingURI = ysap.getNamespace("qmul") + "FreesoundWT"
    thingDescURI = ysap.getNamespace("qmul") + "FreesoundWT_TD"
    actionURI = ysap.getNamespace("qmul") + "searchAction"
    indataSchemaURI = ysap.getNamespace("qmul") + "searchAction_IDS"
    outdataSchemaURI = ysap.getNamespace("qmul") + "searchAction_ODS"

    ##############################################################
    #
    # Put the Thing Description into SEPA
    #
    ##############################################################
    
    # get the first update (TD_INIT)
    updText = ysap.getUpdate("TD_INIT",
                             {"thingURI": " <%s> " % thingURI,
                              "thingDescURI": " <%s> " % thingDescURI,
                              "thingName":" 'FreesoundWT' "})
    kp.update(ysap.updateURI, updText)
    
    # get the second update (TD_ADD_ACTION_STRING_INPUT_GRAPH_OUTPUT)
    updText = ysap.getUpdate("TD_ADD_ACTION_STRING_INPUT_GRAPH_OUTPUT",
                             {"thingDescURI": " <%s> " % thingDescURI,
                              "actionURI": " <%s> " % actionURI,
                              "actionName": " 'searchByTags' ",                              
                              "inDataSchema": " <%s> " % indataSchemaURI,
                              "outDataSchema": " <%s> " % outdataSchemaURI,
                              "actionComment": " 'Search song by tags' " })
    kp.update(ysap.updateURI, updText)
        
    # # remove existing action instances
    # kp.update(updateURI, remove_actions.format(
    #     actionURI = actionURI
    # ))

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
    # Wait for the end...
    #
    ##############################################################    

    logging.info("WebThing ready! Waiting for actions!")
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
