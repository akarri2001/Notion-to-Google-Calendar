import os
from notion_client import Client
from pprint import pprint
from datetime import datetime, timedelta, date
import time
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

NOTION_TOKEN =  #the secret_something 
database_id =  #get the mess of numbers before the "?" on your dashboard URL and then split it into 8-4-4-4-12 characters between each dash
notion_time =  #has to be adjusted for when daylight savings is different
#^^ This is for America/New York when it's daylight savings

urlRoot =  #open up a task and then copy the URL root up to the "p="
GCalTokenLocation =  #This is the command you will be feeding into the command prompt to run the GCalToken program

#GCal Set Up Part
calendarID =  #The GCal calendar id. The format is something like "sldkjfliksedjgodsfhgshglsj@groups.calendar.google.com"
credentialsLocation = #This is where you keep the pickle file that has the Google Calendar Credentials



os.environ['NOTION_TOKEN'] = NOTION_TOKEN
notion = Client(auth=os.environ["NOTION_TOKEN"])




# Query the database for tasks that are for today or in the next week and not in ToDoIst
todayDate = datetime.today().strftime("%Y-%m-%d")

my_page = notion.databases.query(
    **{
        "database_id": database_id, 
        "filter": {
            "and": [
                {
                    "property": "On GCal?", 
                    "checkbox":  {
                        "equals": False
                    }
                }, 
                {
                    "or": [
                    {
                        "property": "Date", 
                        "date": {
                            "equals": todayDate
                        }
                    }, 
                    {
                        "property": "Date", 
                        "date": {
                            "next_week": {}
                        }
                    }
                ]   
                }
            ]
        },
    }
)


#Make list that contains each of the results
resultList = []

# print(my_page.json().keys())
results = my_page.json()['results']
UTCTime = datetime.now() + timedelta(hours = 5)

for result in results:
    resultList.append(result)
    
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO TODOIST
        **{
            "page_id": pageId, 
            "properties": {
                'On GCal?': {
                    "checkbox": True 
                },
                'Last Updated Time': {
                    "date":{
                        'start': notion_time, #has to be adjsuted for when daylight savings is different
                        'end': None,
                    }
                }
            },
        },
    )

TaskNames = []
Dates = []
Initiatives = []
ExtraInfo = []
URL_list = []

# print(resultList[0]['properties']['Task'].keys())

def makeTaskURL(ending, urlRoot):
    urlId = ending[0:8] + ending[9:13] + ending[14:18] + ending[19:23] + ending[24:]
    return urlRoot + urlId

if len(resultList) > 0:

    for el in resultList:
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties']['Task']['title'][0]['text']['content'])
        Dates.append(el['properties']['Date']['date']['start'])
        try:
            Initiatives.append(el['properties']['Initiative']['select']['name'])
        except:
            Initiatives.append("")
        
        try: 
            ExtraInfo.append(el['properties']['Extra Info']['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(result['id'], urlRoot))

    print(TaskNames)
    print(Dates)
    print(Initiatives)
    print(ExtraInfo)
    print(URL_list)

else:
    print("Nothing new added to GCal")


#note down the last time that the code was run
lastEditTime = datetime.now() + timedelta(hours = 5)
timeStr = lastEditTime.strftime("%Y-%m-%dT%H:%M:00.000Z")
text_file = open("Last_GCal_Update_Time.txt", "w")
n = text_file.write(timeStr)
text_file.close()




#SET UP THE GOOGLE CALENDAR API INTERFACE

credentials = pickle.load(open(credentialsLocation, "rb"))
service = build("calendar", "v3", credentials=credentials)

try:
    calendar = service.calendars().get(calendarId=calendarID).execute()
except:
    #refresh the token
    import os
    os.system(GCalTokenLocation)    
    
    #SET UP THE GOOGLE CALENDAR API INTERFACE

    credentials = pickle.load(open(credentialsLocation, "rb"))
    service = build("calendar", "v3", credentials=credentials)

    # result = service.calendarList().list().execute()
    # print(result['items'][:])

    calendar = service.calendars().get(calendarId=calendarID).execute()

print(calendar)

######################################################################
#METHOD TO MAKE A CALENDAR EVENT

def makeCalEvent(eventName, eventDescription, eventStartTime, sourceURL):
    eventStartTime = datetime.combine(eventStartTime, datetime.min.time()) + timedelta(hours=8) ##make the events pop up at 8 am instead of 12 am
    eventEndTime = eventStartTime + timedelta(hours =1)
    timezone = 'America/New_York'
    event = {
        'summary': eventName,
        'description': eventDescription,
        'start': {
            'dateTime': eventStartTime.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        },
        'end': {
            'dateTime': eventEndTime.strftime("%Y-%m-%dT%H:%M:%S"),
            'timeZone': timezone,
        }, 
        'source': {
            'title': 'Notion Link',
            'url': sourceURL,
        }
    }
    print('Adding this event to calendar: ', eventName)
    x = service.events().insert(calendarId=calendarID, body=event).execute()
    return x['id']


def makeEventDescription(initiative, info):
    return f'Initiative: {initiative} \n{info}'

###################


### Create events for tasks that have not been in GCal already
calEventIdList = []
for i in range(len(TaskNames)):
    calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i], '%Y-%m-%d'), URL_list[i])
    calEventIdList.append(calEventId)

print(calEventIdList)
i = 0
for result in resultList:
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO GCAL
        **{
            "page_id": pageId, 
            "properties": {
                'GCal Event Id': {
                    "rich_text": [{
                        'text': {
                            'content': calEventIdList[i]
                        }
                    }]
                }
            },
        },
    )
    i += 1

for result in results:
    resultList.append(result)
    
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO TODOIST
        **{
            "page_id": pageId, 
            "properties": {
                'On GCal?': {
                    "checkbox": True 
                },
                'Last Updated Time': {
                    "date":{
                        'start': notion_time,
                        'end': None,
                    }
                }
            },
        },
    )

###############################
#####################################
##################################
###### Filter events that have been updated since the GCal event has been made

my_page = notion.databases.query(
    **{
        "database_id": database_id,
        "filter": {
            "and": [
                {
                    "property": "NeedGCalUpdate", 
                    "formula":{
                        "checkbox":  {
                            "equals": True
                        }
                    }
                }, 
                {
                    "or": [
                    {
                        "property": "Date", 
                        "date": {
                            "equals": todayDate
                        }
                    }, 
                    {
                        "property": "Date", 
                        "date": {
                            "next_week": {}
                        }
                    }
                ]   
                }
            ]
        },
    }
)


#Make list that contains each of the results
resultList = []

# print(my_page.json().keys())
results = my_page.json()['results']
# UTCTime = datetime.now() + timedelta(hours = 5)

updatingPageIds = []
updatingCalEventIds = []
for result in results:
    resultList.append(result)
    
    pageId = result['id']
    updatingPageIds.append(pageId)
    print('\n')
    print(result)
    print('\n')
    calId = result['properties']['GCal Event Id']['rich_text'][0]['text']['content']
    print(calId)
    updatingCalEventIds.append(calId)


#Delete the event using the calendarEvent Id through for loop

for CalId in updatingCalEventIds: 
    service.events().delete(calendarId=calendarID, eventId= CalId).execute()


#Make new event 

TaskNames = []
Dates = []
Initiatives = []
ExtraInfo = []
URL_list = []

if len(resultList) > 0:

    for el in resultList:
        print('\n')
        print(el)
        print('\n')

        TaskNames.append(el['properties']['Task']['title'][0]['text']['content'])
        Dates.append(el['properties']['Date']['date']['start'])
        try:
            Initiatives.append(el['properties']['Initiative']['select']['name'])
        except:
            Initiatives.append("")
        
        try: 
            ExtraInfo.append(el['properties']['Extra Info']['rich_text'][0]['text']['content'])
        except:
            ExtraInfo.append("")
        URL_list.append(makeTaskURL(result['id'], urlRoot))

    print(TaskNames)
    print(Dates)
    print(Initiatives)
    print(ExtraInfo)
    print(URL_list)

else:
    print("Nothing new added to GCal")
calEventIdList = []

for i in range(len(TaskNames)):
    calEventId = makeCalEvent(TaskNames[i], makeEventDescription(Initiatives[i], ExtraInfo[i]), datetime.strptime(Dates[i], '%Y-%m-%d'), URL_list[i])
    calEventIdList.append(calEventId)



# Update the notion dashboard based off of the new calendar event id

i=0
for result in results:
    resultList.append(result)
    
    pageId = result['id']
    
    my_page = notion.pages.update( ##### THIS CHECKS OFF THAT THE TASK IS PUSHED OVER TO GCAL
        **{
            "page_id": pageId, 
            "properties": {
                'GCal Event Id': {
                    "rich_text": [{
                        'text': {
                            'content': calEventIdList[i]
                        }
                    }]
                },
                'Last Updated Time': {
                    "date":{
                        'start': notion_time, #has to be adjsuted for when daylight savings is different
                        'end': None,
                    }
                }
            },
        },
    )
    i += 1
