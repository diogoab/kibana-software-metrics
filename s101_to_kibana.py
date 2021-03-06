"""Structure101 to Kibana.

Usage:
  s101_to_kibana     --elasticSearchURL=<elasticSearchURL> --structureURL=<structureURL> [--dateFormat=<dateFormat>]

Options:
  -e --elasticSearchURL=<elasticSearchURL>      The URL to the elastic search, so we can post data to it
  -s --structureURL=<structureURL>              The URL to Structure101, so we can fetch data from it.
  -d --dateFormat=<dateFormat>                  The date format in teh XML [default: %d/%m/%y]
"""

import datetime
from docopt import docopt
import platform
import getpass
from elasticsearch import Elasticsearch
#import xml.etree.ElementTree
import xml.etree.cElementTree as ET
import urllib3

if __name__ == '__main__':
    arguments = docopt(__doc__, version='Structure101 to Kibana')
    elastic_search_url = arguments["--elasticSearchURL"]
    structure_url = arguments["--structureURL"]
    es = Elasticsearch([elastic_search_url])
    uname = platform.uname()
    es.index(index="s101-runner", doc_type="run",
             body={"author": "%s@%s" % (getpass.getuser(), platform.node()),
                    "date": datetime.datetime.now().isoformat(),
                    "arguments": arguments
             })
    http = urllib3.PoolManager()
    input_xml_stream = http.urlopen('GET',structure_url)
    s101_data_as_xml = ET.ElementTree(file=input_xml_stream)
    chart = s101_data_as_xml.getroot()
    chart_name = chart.attrib["name"].lower()  # e.g. "Size"
    #print(root)
    for series in chart.getchildren():
        series_name = series.attrib["name"]  # e.g. PG5_MAIN
        #print(series.attrib)
        for entry in series:
            #print(entry.attrib)
            body = {"series_name": series_name}
            attribs = entry.attrib
            if attribs["time"] == "":
                del attribs["time"] #no point in having empty data
            entry_date_as_string = attribs["date"]
            entry_date = datetime.datetime.strptime(entry_date_as_string, arguments["--dateFormat"])
            attribs["date"] = entry_date.isoformat()
            attribs[chart_name] = int(attribs["value"])  # it is an integer attribute
            del attribs["value"] #no point in having original data
            body.update(attribs)
            print(body)
            es.index(index="s101-%s" % chart_name, doc_type=chart_name, body=body)
