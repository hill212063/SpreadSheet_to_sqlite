from __future__ import print_function
import os.path
import math
from peewee import *
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


db = SqliteDatabase('w5.db')
#table model
class Gpa(Model):
    GpaID = AutoField()
    GPA = FloatField() 

    class Meta:
        database=db


class Gpax(Model):
    GpaxID = AutoField()
    GPAX = FloatField()

    class Meta:
        database=db



class Subjects(Model):
    ID = AutoField()
    real_subject_id = CharField(max_length=9)
    subject_name = CharField(max_length=50)
    credit = IntegerField()
    grade_char = CharField(max_length=2)
    grade_int = FloatField()
    year = CharField(max_length=4)
    semester = SmallIntegerField()
    UserID = IntegerField()
    GpaID = ForeignKeyField(Gpa,backref='subjects')
    GpaxID = ForeignKeyField(Gpax,backref='subjects')

    class Meta:
        database=db





# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']

# The ID and range of a sample spreadsheet.
SheetsID = []
SheetsRange = []


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    #Create tables
    db.connect()
    db.create_tables([Subjects,Gpa,Gpax])



    for i in range(len(SheetsID)):
        semester_block=[]
        semester_credit = 0
        raw_semester_credit = 0
        credit_sum = 0
        raw_credit_sum =0

        gpax_recent = Gpax(GpaxID = i,GPAX=0.00)
        gpax_recent.save(force_insert=True)
        try:
            service = build('sheets', 'v4', credentials=creds)

            # Call the Sheets API
            sheet = service.spreadsheets()
            result = sheet.values().get(spreadsheetId=SheetsID[i],
                                    range=SheetsRange[i]).execute()
            values = result.get('values', [])
            values.append([';']*7)
            if not values:
                print('No data found.')
                return

            for row_idx in range(len(values)-1):
                row = values[row_idx]
                if(row[6] != values[row_idx+1][6]):
                    gpa_val = (semester_credit+((float(row[2])*float(row[4]))))/(raw_semester_credit+float(row[2]))
                    gpa_val = math.floor(gpa_val*100)/100
                    gpa_recent = Gpa(GPA=gpa_val)
                    gpa_recent.save()
                    for subj in semester_block:
                        subject_recent = Subjects(real_subject_id=subj[0],
                                subject_name=subj[1],
                                credit=int(subj[2]),
                                grade_char=subj[3],
                                grade_int=float(subj[4]),
                                year=subj[5],
                                semester=int(subj[6]),
                                UserID=i,
                                GpaID=gpa_recent,
                                GpaxID=i)
                        subject_recent.save()
        
                    semester_credit = 0
                    raw_semester_credit = 0
                    semester_block = []
                    if(values[row_idx+1][6]==(';')):
                        subject_recent = Subjects(real_subject_id=row[0],
                                subject_name=row[1],
                                credit=int(row[2]),
                                grade_char=row[3],
                                grade_int=float(row[4]),
                                year=row[5],
                                semester=int(row[6]),
                                UserID=i,
                                GpaID=gpa_recent,
                                GpaxID=i)
                        subject_recent.save()
                        break
                else:
                    semester_credit += float(row[2])*float(row[4])
                    raw_semester_credit += float(row[2])
                semester_block.append(row)
                credit_sum += float(row[2])*float(row[4])
                raw_credit_sum += float(row[2])

            gpax_val = credit_sum/raw_credit_sum        
            gpax_val = math.floor(gpax_val*100)/100
            Gpax.update(GPAX = gpax_val).where(Gpax.GpaxID == i).execute()

        except HttpError as err:
            print(err)

    db.close()

if __name__ == '__main__':
    main()
