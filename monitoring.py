import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import socket
import time
import json

class AgentMonitor:

    def printAllChildren(self, url):
        xmlTree =self.getXMLTree(url)
        root=xmlTree.getroot()
        self.recursivePrint(root)

    def recursivePrint(self,xmlElement):
        print(xmlElement.tag, xmlElement.text)
        for child in xmlElement:
            self.recursivePrint(child)

    def parseWptServer(self,url):
        xmlTree =self.getXMLTree(url)
        root=xmlTree.getroot()
        resultDict = {"url":url}
        resultDict["locations"] = []
        for location in root.iter("location"):
             resultDict["locations"].append(self.parseLocation(location))
        return resultDict

    def getXMLTree(self,url):
        urllib.request.urlretrieve('http://'+url+'/getTesters.php','testers.xml')
        tree=ET.parse('testers.xml')
        return tree

    def parseLocation(self,xmlElement):
        resultDict = {}
        id = xmlElement.find("id")
        resultDict["id"]=id.text
        status = xmlElement.find("status")
        if (status is not None):
            resultDict["status"]=status.text
        else:
            resultDict["status"]="-1"

        resultDict["testers"]=[]
        for  tester in xmlElement.iter("tester"):
            resultDict["testers"].append(self.parseTesters(tester))
        return  resultDict

    def parseTesters(self,xmlElement):
        resultDict = {}
        freedisk = xmlElement.find("freedisk")
        if (freedisk is not None and freedisk.text is not None):
            resultDict["freeDisk"] = freedisk.text
        else:
            resultDict["freeDisk"] = "-1"
        pc = xmlElement.find("pc")
        if (pc is not None and pc.text is not None):
            resultDict["pc"]=pc.text
        else:
            resultDict["pc"]="-1"
        lastWork = xmlElement.find("last")
        if(lastWork is not None and lastWork.text is not None):
            resultDict["lastWork"]=lastWork.text
        else:
            resultDict["lastWork"]="-1"
        lastCheck = xmlElement.find("elapsed")
        if (lastCheck is not None and lastCheck.text is not None):
            resultDict["lastCheck"]=lastCheck.text
        else:
            resultDict["lastCheck"]="-1"
        cpu = xmlElement.find("cpu")
        if(cpu is not None and cpu.text is not None):
            resultDict["cpu"]=cpu.text
        else:
            resultDict["cpu"]="-1"
        errors = xmlElement.find("errors")
        if(errors is not None and errors.text is not None):
            resultDict["errors"]=errors.text
        else:
            resultDict["errors"]="-1"
        return resultDict

    def reportToGraphite(self,wptAgentData,path_prefix,carbon_server,carbon_port,locations):
        sock = socket.create_connection((carbon_server, carbon_port))
        for location in filter(lambda loc: (loc["id"] in locations) if locations else True, wptAgentData["locations"]):
            url = path_prefix+wptAgentData["url"]+'.'+location["id"]
            message=url+'.'+"status" + ' '+ ("1" if (location["status"] == "OK") else "0") + ' %d\n' % int(time.time())
            sock.send(message.encode())
            for tester in location["testers"]:
                if( tester["pc"] is not None):
                    for key, value in tester.items():
                        if key is not "pc":
                            message=(url+'.'+tester["pc"]+'.'+key + ' '+ value+ ' %d\n' % int(time.time()))
                            sock.send(message.encode())
        sock.close()


agentMonitor = AgentMonitor()

errorOutput = 'There needs to be a json file "conf.json" in the '
'directory /opt/wptserver-monitoring/conf/ that defines a list of strings named "servers", a string '
'named "path_prefix", a string '
'named "carbon_server" and a port number "carbon_port". The urls defined by '
'servers are wpt instances that will be monitored. The results will be sent '
'to the graphite application on carbon_server listening on port carbon_port. '
'The result message contains the metric path consisting of path_prefix and '
'the carbon servers. '

try:
    with open("/opt/wptserver-monitoring/conf/conf.json") as json_params:
        params = json.load(json_params)
        servers = params["servers"]
        carbon_server = params["carbon_server"]
        carbon_port = params["carbon_port"]
        path_prefix = params["path_prefix"]
        locations = params["locations"]

    for server in servers:
        try:
            wptAgentData = agentMonitor.parseWptServer(server)
            agentMonitor.reportToGraphite(wptAgentData,path_prefix,carbon_server,carbon_port,locations.get(server, None))
        except Exception as ex:
             print("error while processing server "+ server)
             print(ex)

except IOError as err:
    print(errorOutput)
    print(err)
