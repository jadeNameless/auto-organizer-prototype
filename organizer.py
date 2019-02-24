from __future__ import print_function
import pickle
import os.path
import sys
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.labels']
creds=None

if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
myService = build('gmail', 'v1', credentials=creds)


def ListMessagesWithLabels(service, user_id, label_ids=[]):
    print('grabbing inbox...')
    try:
        response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
        
        if 'messages' in response:
            for i in response['messages']:
                yield i
        while 'nextPageToken' in response:
            page_token = response['nextPageToken']
            response = service.users().messages().list(userId=user_id, labelIds=label_ids, pageToken=page_token).execute()
            for j in response['messages']:
                yield j
            
        
        
  
    except errors.HttpError:
        print('An error occurred: %s' % error)
    except:
        print('wow this is a weird error')
    


def messageMaker():
    messages=ListMessagesWithLabels(myService, 'me', ['INBOX'])
    print("ok now we're here") 
    for i in messages:
        print(i)
        currentMess=myService.users().messages().get(userId='me', id=i['id'], format='metadata', metadataHeaders=['from']).execute()
        currentclean=currentMess['payload']['headers']
        idNamePair=[i['id'], currentclean[0]['value']]
        print(idNamePair)
        yield idNamePair

def folderManager():
    makeFolder(MakeLabel('notifications'))
    makeFolder(MakeLabel('bullshit'))
    mails=messageMaker()
    labels=ListLabels(myService, 'me')
    names=labelNames(labels)
    ids=labelId(labels)
    notifIndex=ids[names.index('notifications')]
    bsIndex=ids[names.index('bullshit')]
    for m in mails:
        if m[1] in names:
            
            ModifyMessage(m[0], CreateMsgLabels(ids[names.index(m[1])]), myService, 'me')
        elif 'facebook' in m[1] or 'linkedin' in m[1]:
            ModifyMessage(m[0], CreateMsgLabels(notifIndex), myService, 'me')
        else:
            value=makeFolder(MakeLabel(m[1]))
            #print(m[1])
            try:
                ModifyMessage(m[0], CreateMsgLabels(value['id']), myService, 'me')
            except:
                print("this email is bullshit, im filing it with the bullshit")
                ModifyMessage(m[0], CreateMsgLabels(bsIndex), myService, 'me')
                print(m[1])
               



def ModifyMessage(msg_id, msg_labels, service=myService, user_id='me' ):
    """Modify the Labels on the given Message.

    Args:
      service: Authorized Gmail API service instance.
      user_id: User's email address. The special value "me"
      can be used to indicate the authenticated user.
      msg_id: The id of the message required.
      msg_labels: The change in labels.

    Returns:
      Modified message, containing updated labelIds, id and threadId.
    """
    try:
      message = service.users().messages().modify(userId=user_id, id=msg_id,
                                                body=msg_labels).execute()

      label_ids = message['labelIds']

      print('Message ID: %s - With Label IDs %s' % (msg_id, label_ids))
      return message
    except errors.HttpError as error:
      print('An error occurred: %s' % error)
    return "aligatorNone"

def CreateMsgLabels(senderTag):
  """Create object to update labels.

  Returns:
    A label update object.
  """
  return {'removeLabelIds': ['INBOX'], 'addLabelIds': [senderTag]}


def makeFolder(label_object):  
    try:
        label = myService.users().labels().create(userId='me', body=label_object).execute()
        print ("created", label['id'])
        return label
    except:
        return None 
"""Creates a new label within user's mailbox, also prints Label ID.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.
    label_object: label to be added.

  Returns:
    Created Label.
  """

def MakeLabel(label_name, mlv='show', llv='labelShow'):
  """Create Label object.

  Args:
    label_name: The name of the Label.
    mlv: Message list visibility, show/hide.
    llv: Label list visibility, labelShow/labelHide.

  Returns:
    Created Label.
  """
      

  label = {'messageListVisibility': mlv,
           'name': label_name,
           'labelListVisibility': llv,
           "type": 'user',
           "color": {
                 "textColor": '#efa093',
                 "backgroundColor": '#000000'}
           }
  return label

def ListLabels(service, user_id):
  """Get a list all labels in the user's mailbox.

  Args:
    service: Authorized Gmail API service instance.
    user_id: User's email address. The special value "me"
    can be used to indicate the authenticated user.

  Returns:
    A list all Labels in the user's mailbox.
  """
  try:
    response = service.users().labels().list(userId=user_id).execute()
    labels = response['labels']
    for label in labels:
      print('Label id: %s - Label name: %s' % (label['id'], label['name']))
    return labels
  except errors.HttpError:
    print ('An error occurred: %s' % error)


def labelNames(labels):
    names=[l['name'] for l in labels]
    return names

def labelId(labels):
    ids=[l['id'] for l in labels]
    return ids
def main():
    folderManager()
main()

#def CreateMsgLabels():
 # return {'removeLabelIds': [], 'addLabelIds': ['UNREAD', 'INBOX', 'Labe