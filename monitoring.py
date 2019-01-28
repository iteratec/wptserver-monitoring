import urllib.request
import urllib.parse
import xml.etree.ElementTree as element_tree
import socket
import time
import json


class AgentMonitor:

    def print_all_children(self, url):
        xml_tree = self.get_xml_tree(url)
        root = xml_tree.getroot()
        self.recursive_print(root)

    def recursive_print(self, xml_element):
        print(xml_element.tag, xml_element.text)
        for child in xml_element:
            self.recursive_print(child)

    def parse_wpt_server(self, url):
        xml_tree = self.get_xml_tree(url)
        root = xml_tree.getroot()
        result_dict = {"url": url}
        result_dict["locations"] = []
        for location in root.iter("location"):
            result_dict["locations"].append(self.parse_location(location))
        return result_dict

    def get_xml_tree(self, url):
        urllib.request.urlretrieve('http://' + url + '/getTesters.php', 'testers.xml')
        tree = element_tree.parse('testers.xml')
        return tree

    def parse_location(self, xml_element):
        result_dict = {}
        id = xml_element.find("id")
        result_dict["id"] = id.text
        status = xml_element.find("status")
        if status is not None:
            result_dict["status"] = status.text
        else:
            result_dict["status"] = "-1"

        result_dict["testers"] = []
        for tester in xml_element.iter("tester"):
            result_dict["testers"].append(self.parse_testers(tester))
        return result_dict

    def parse_testers(self, xml_element):
        result_dict = {}
        freedisk = xml_element.find("freedisk")
        if freedisk is not None and freedisk.text is not None:
            result_dict["freeDisk"] = freedisk.text
        else:
            result_dict["freeDisk"] = "-1"
        pc = xml_element.find("pc")
        if pc is not None and pc.text is not None:
            result_dict["pc"] = pc.text
        else:
            result_dict["pc"] = "-1"
        last_work = xml_element.find("last")
        if last_work is not None and last_work.text is not None:
            result_dict["lastWork"] = last_work.text
        else:
            result_dict["lastWork"] = "-1"
        last_check = xml_element.find("elapsed")
        if last_check is not None and last_check.text is not None:
            result_dict["lastCheck"] = last_check.text
        else:
            result_dict["lastCheck"] = "-1"
        cpu = xml_element.find("cpu")
        if cpu is not None and cpu.text is not None:
            result_dict["cpu"] = cpu.text
        else:
            result_dict["cpu"] = "-1"
        errors = xml_element.find("errors")
        if errors is not None and errors.text is not None:
            result_dict["errors"] = errors.text
        else:
            result_dict["errors"] = "-1"
        return result_dict

    def report_to_graphite(self, wpt_agent_data, path_prefix, carbon_server, carbon_port, locations):
        sock = socket.create_connection((carbon_server, carbon_port))
        for location in filter(lambda loc: (loc["id"] in locations) if locations else True, wpt_agent_data["locations"]):
            url = path_prefix + wpt_agent_data["url"] + '.' + location["id"]
            message = url + '.' + "status" + ' ' + ("1" if (location["status"] == "OK") else "0") + ' %d\n' % int(
                time.time())
            sock.send(message.encode())
            for tester in location["testers"]:
                if tester["pc"] is not None:
                    for key, value in tester.items():
                        if key is not "pc":
                            message = (url + '.' + tester["pc"] + '.' + key + ' ' + value + ' %d\n' % int(time.time()))
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
            wptAgentData = agentMonitor.parse_wpt_server(server)
            agentMonitor.report_to_graphite(wptAgentData, path_prefix, carbon_server, carbon_port,
                                            locations.get(server, None))
        except Exception as ex:
            print("error while processing server " + server)
            print(ex)

except IOError as err:
    print(errorOutput)
    print(err)
