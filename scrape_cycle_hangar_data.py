import os
import requests
import lxml.html
from dateutil import parser
from shapely.geometry import mapping
from shapely.geometry import Point
import json

login_form = {
    "USERNAME": os.environ["USER"],
    "PASSWORD": os.environ["PASSWORD"],
}

s = requests.Session()
s.post("https://cyclehangars.hackney.gov.uk/sf/control/loginSF", data=login_form)

response = s.get("https://cyclehangars.hackney.gov.uk/sf/control/cyclehangerapplication?type=Residential")
root = lxml.html.document_fromstring(response.content)
nodes = root.xpath('//*[@id="hangerData"]')
data =  json.loads(nodes[0].attrib["value"])

features = []
for key, item in data["hangers"].items():
    # Remap some fields to make them more convenient
    item["waiting_list"] = int(item["waitingList"])
    item["hanger_type"]["id"] = item["hanger_type"]["hanger_id"]
    item["hanger_type"]["cost_per_year"] = float(item["hanger_type"]["cost"]["Per Year"])

    # Fixup types
    item["auto_offer_spaces"] = bool(item["auto_offer_spaces"])
    item["created"] = parser.parse(item["created"]).isoformat()
    item["end_of_life"] = parser.parse(item["end_of_life"]).isoformat()
    if item["street_usrn"]:
        item["street_usrn"] = int(item["street_usrn"])
    item["spaces"] = int(item["spaces"])

    del item["waitingList"]
    del item["hanger_type_id"]
    del item["hanger_type"]["hanger_id"]
    del item["hanger_type"]["cost"]

    # GeoJSON version
    p = mapping(Point(float(item["long"]), float(item["lat"])))
    features.append({
        "type": "Feature",
        "properties": {
            "name": item["hanger_id"],
            "created": item["created"],
            "cost_per_year": item["hanger_type"]["cost_per_year"],
            "end_of_life": item["end_of_life"],
            "spaces": item["spaces"],
            "type": item["hanger_type"]["class"],
            "waiting_list": item["waiting_list"],
        }, 
        "geometry": p
    })

with open("hangers.json", "w") as f:
    f.write(json.dumps(data, indent=4, sort_keys=True))

schema = {
    "type": "FeatureCollection",
    "features": features,
}
with open("hangers.geojson", "w") as outfile:
    outfile.write(json.dumps(schema, indent=4, sort_keys=True))
