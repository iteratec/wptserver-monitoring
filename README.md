
# wptserver monitoring

Script to monitor WPT servers and post metrics to a graphite server.

Monitors the following wpt server metrics returned by `/getTesters.php`

* status
* Last Check
* Last Work
* Free Disk
* Error Rate
* CPU Utilization

## Usage

The script needs to be parameterized via a json file `/opt/wptserver-monitoring/conf/conf.json`.

The necessary parameters are

* servers

  The URL's of the wpt servers that are monitored.

* carbon_server

  URL of Graphite server's carbon component resulting metrics are sent to.

* carbon_port

  Port of Graphite server's carbon component resulting metrics are sent to.

* path_prefix

  Prefix of the graphite path metrics resulting metrics are sent for. Must end with a dot.
  The complete metric path consists of the wpt server url prefixed by this prefix.

* locations

  Locations that will be fetched for the given server. If the server is not listed,
  all available locations will be retrieved.

An example json file might look like this:

    {
      "servers": ["example1.wpt.server.com", "example2.wpt.server.com"],
      "carbon_server": "url.to.carbon.component",
      "carbon_port": 2003,
      "path_prefix": "example.prefix.",
      "locations": {
        "example1.wpt.server.com": ["examplecity", "exampleplace"]
      }
    }
