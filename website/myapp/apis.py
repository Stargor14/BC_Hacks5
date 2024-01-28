import json
import googlemaps
import pathlib
from openai import OpenAI
import re

jsonFile=open("../keys.json","r")
dataJson = json.load(jsonFile)
gptClient = OpenAI()

mapsClient = googlemaps.Client(dataJson["google"])
photoDir="myapp/static/photos/"

prompt1="You are a website designed to help users find incredibly fun adventures. When data is given to you, you recommend locations someone could visit, taking into account all the restrictions given, while trying to make sure the adventure is as fun as possible. Output only the names of the locations, in json format. in the json format you will also include the 'area' that the location is in. Here is your data: "

def getGoogleLocation(location):
    result= mapsClient.find_place(input=location, input_type="textquery", fields=["name","place_id","photos"] )["candidates"][0]
    files = [f for f in pathlib.Path().glob("myapp/static/photos/"+result["place_id"]+".jpg") if f.is_file()]
    if(len(files)==0):
        print("create new image file")
        f = open(photoDir+result["place_id"]+".jpg", 'wb')
        photo_reference=result['photos'][0]['photo_reference']
        for chunk in mapsClient.places_photo(photo_reference, max_width=800):
            if chunk:
                f.write(chunk)
        f.close()
    return result

def requestGPT4(request):
    print("sending request")
    temp=prompt1+str(request)
    completion = gptClient.chat.completions.create(
        model="gpt-4-0125-preview",
               messages=[
            {
                "role": "user",
                "content": temp,
            },
        ],
    )
    return completion.choices[0].message.content

def createLocationList(request):
    locations={}
    gptResponse=requestGPT4(request)
    json_match = re.search(r'\[.*\]', gptResponse, re.DOTALL)
    if json_match:
        json_data = json_match.group(0)
        
        for location in json_data:
            googleResponse=getGoogleLocation(location["name"])
            locations[googleResponse["place_id"]]={
                                                    "name":googleResponse["name"],
                                                    "location":location["area"]
                                                    }
    else:
        print("No JSON data found.")
    return locations