#!/usr/bin/python3

# global reqs
import logging
from uuid import uuid4
from sepy.YSAPObject import *
from sepy.SEPAClient import *

# the class
class Device:

    """This class represents a generic WebThing"""
    
    # constructor
    def __init__(self, ysap, thingName):

        """This method is used to initialize the WebThing.
        Mandatory parameters are the name of the YSAP file
        with the configuration and the name of the WebThing 
        to create"""
        
        # debug message
        logging.debug("Device::__init__() invoked")

        # read the ysap provided
        logging.debug("Device::__init__() -- Reading configuration file")
        self.ysap = YSAPObject(ysap, 40)
        
        # store things data
        self.thingName = thingName
        self.thingURI = self.getRandomURI()
        self.thingID = self.thingURI.split("#")[1]
        self.thingDescURI = self.thingURI + "_TD"
        
        # initialize an empty dictionary for events, props and actions
        # keys are represented by names, values are the related URIs
        self.events = {}
        self.actions = {}
        self.properties = {}

        # initialize a list of the custom statements
        self.statements = []
        
        # create a KP
        logging.debug("Device::__init__() -- Creating a new KP")
        self.kp = SEPAClient(None, 40)

        # save the important URIs
        self.updateURI = self.ysap.updateURI
        self.subscribeURI = self.ysap.subscribeURI
        
        # call TD_INIT
        u = self.ysap.getUpdate("TD_INIT", {
            "thingName": " '%s' " % self.thingName,
            "thingURI": " <%s> " % self.thingURI,
            "thingDescURI": " <%s> " % self.thingDescURI
        })
        print(u)
        self.kp.update(self.updateURI, u)

        
    def addProperty(self, isUri, propertyName, propertyValue, propertyURI=None, dataschema="-", writable=True, stability=0):

        """This method adds a new property to the thing"""

        # debug message
        logging.debug("Debug::addProperty() invoked")

        # generate an URI and store data
        if not propertyURI:
            self.properties[propertyName] = self.getRandomURI()
        else:
            self.properties[propertyName] = propertyURI
    
        # add the property
        u = None
        if isUri:
            u = self.ysap.getUpdate("ADD_URI_PROPERTY", {
                "thing": self.thingURI,
                "property": propertyURI,
                "newName": propertyName,
                "newStability": stability,
                "newWritable": writable,
                "newDataSchema": dataschema,
                "newValue": propertyValue
            })
        else:
            u = self.ysap.getUpdate("ADD_PROPERTY", {
                "thing": self.thingURI,
                "property": propertyURI,
                "newName": propertyName,
                "newStability": stability,
                "newWritable": writable,
                "newDataSchema": dataschema,
                "newValue": propertyValue
            })
        self.kp.update(self.updateURI, u) 

        
    # add new action
    def addAction(self, actionName, actionURI=None, fields=[]):

        """This method is used to put the description of
        an action into the SEPA instance. Mandatory is the
        name of the action to publish. The eventURI is instead
        optional. If not provided, will be automatically generated"""

        # debug message
        logging.debug("Debug::addAction() invoked")

        u = self.ysap.getUpdate("TD_ADD_ACTION_GRAPH_INPUT_GRAPH_OUTPUT", {
            "thingDescURI": self.thingDescURI,
            "actionURI": self.actionURI,
                "inField": fieldURI,
                "fieldType": f["fieldType"],
                "fieldName": f["fieldName"]
            })
            self.kp.update(self.updateURI, u)
            print(u)


        
        # # generate an URI and store data
        # self.actions[actionName] = {}
        # if not actionURI:
        #     self.actions[actionName]["uri"] = self.getRandomURI()
        # else:
        #     self.actions[actionName]["uri"] = actionURI

        # # generate an URI for the data schema
        # dataSchema = self.getRandomURI()
            
        # # generate and perform the update
        # u = self.ysap.getUpdate("ADD_NEW_ACTION", {
        #     "thing": self.thingURI,
        #     "action": self.actions[actionName]["uri"],
        #     "newName": actionName,
        #     "newInDataSchema": dataSchema,
        #     "newOutDataSchema": "-"
        # })
        # self.kp.update(self.updateURI, u)
        # print(u)

        # # add fields to the action
        # self.actions[actionName]["fields"] = fields
        # for f in fields:

        #     # generate an URI for the field
        #     fieldURI = self.getRandomURI()
            
        #     # read field name and type
        #     u = self.ysap.getUpdate("ADD_INPUT_FIELD_TO_ACTION", {
        #         "thing": self.thingURI,
        #         "action": self.actions[actionName]["uri"],
        #         "inField": fieldURI,
        #         "fieldType": f["fieldType"],
        #         "fieldName": f["fieldName"]
        #     })
        #     self.kp.update(self.updateURI, u)
        #     print(u)

    # add event
    def addEvent(self, eventName, eventURI=None):

        """This method is used to put the description of
        an event into the SEPA instance. Mandatory is the
        name of the event to publish. The eventURI is instead
        optional. If not provided, will be automatically generated"""
        
        # debug message
        logging.debug("Device::addEvent() invoked")
        
        # generate an URI and store data
        if not eventURI:
            self.events[eventName] = self.getRandomURI()
        else:
            self.events[eventName] = eventURI

        # generate and perform the update
        u = self.ysap.getUpdate("ADD_EVENT", {
            "event": self.events[eventName],
            "thing": self.thingURI,
            "eName": eventName,
            "outDataSchema": "-"
        })
        print(u)
        self.kp.update(self.updateURI, u)


    def addCustomStatement(self, statement):

        """This method is used to add custom statements not present
        in the ysap file used by this class"""

        # debug message
        logging.debug("Device::addCustomStatement() invoked")

        # store and do the update
        self.statements.append(statement)
        self.kp.update(self.updateURI, "INSERT DATA { %s }" % statement)
        
        
    def subscribeToAction(self):
        logging.error("Device::subscribeToAction yet to implement!")


    # delete Web Thing
    def deleteWT(self):

        """This method is used to delete a Thing from the KB. It should be
        called before shutting down the Thing"""

        # debug message
        logging.debug("Device::deleteWT() invoked")
        
        # delete properties
        logging.debug("Device::deleteWT() -- removing all the properties")
        for p in self.properties:
            u = self.ysap.getUpdate("DELETE_PROPERTY", {
                "thing": self.thingURI,
                "property": self.properties[p]
            })
            self.kp.update(self.updateURI, u)        
        
        # delete actions
        logging.debug("Device::deleteWT() -- removing all the actions")
        for a in self.actions:

            # delete fields, then the action
            for f in self.actions[a]["fields"]:
                print(f)
                u = self.ysap.getUpdate("DELETE_INPUT_FIELD_FROM_ACTION", {
                    "thing": self.thingURI,
                    "action": self.actions[a]["uri"],
                    "fieldType": f["fieldType"],
                    "fieldName": f["fieldName"]
                })
                print(u)
                self.kp.update(self.updateURI, u)
                
                
            u = self.ysap.getUpdate("DELETE_ACTION", {
                "thing": self.thingURI,
                "action": self.actions[a]["uri"]
            })
            self.kp.update(self.updateURI, u)
            
        
        # delete events
        logging.debug("Device::deleteWT() -- removing all the events")
        for e in self.events:
            u = self.ysap.getUpdate("DELETE_EVENT", {
                "thing": self.thingURI,
                "event": self.events[e]
            })
            self.kp.update(self.updateURI, u)
            
        # delete thing
        logging.debug("Device::deleteWT() -- removing thing")
        u = self.ysap.getUpdate("DELETE_THING", {
            "thing": self.thingURI,
            "name": self.thingName })
        self.kp.update(self.updateURI, u)    

        # delete custom statements
        logging.debug("Device::deleteWT() -- removing custom statements")
        for statement in self.statements:
            self.kp.update(self.updateURI, "DELETE DATA { %s }" % statement)

        
    def waitForActions(self, handlerClass):

        """This method is used to subscribe to all the actions request
        for this Web Thing. The handler is the only parameter required"""
        
        # get subscription
        s = self.ysap.getQuery("GET_ACTION_REQUEST", {
            "thing": self.thingURI})
        
        # subscribe
        self.kp.subscribe(self.subscribeURI, s, "actions", handlerClass(self.kp, self.ysap))
        

    def getRandomURI(self):

        """This method is used to create a random URI"""

        # debug message
        logging.debug("Device::getRandomURI() invoked")
        
        # return
        return self.ysap.namespaces["qmul"] + str(uuid4())
