# SonicAnnotator WT

## Introduction

This project contains the WebThing of the Sonic Annotator tool. Starting this tool,
a new WebThing will be created, that put into SEPA its Thing Description.
The WebThing will then subscribe to Action Requests, in order to get notification
about new requests. The handler will then execute the action and put the results
into SEPA.

## Quick start

To start the web thing simply type:

```bash
$ python3 annotatorWT.py
```

Remember to edit its configuration from `annotator.jsap`.

## Basic Behaviour

The WebThing pushes its Thing Description into a running instance of SEPA. The Thing Description states all the properties, events and actions exposed by the Thing.
Then the WebThing subscribes to all the action requests addressed to it. The handler read all of the data contained in the request, performs the audio analysis and return the results.

## License

This software is released with GNU GPL v3.0. 
