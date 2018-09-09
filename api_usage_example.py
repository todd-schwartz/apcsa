from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.rosters.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.students.readonly']


def pretty_print(data):
    print(json.dumps(data, indent=4, sort_keys=True))


courseId = '14911700941'


def main():
    """Shows how we can list the details of all the assignments (courseWork), and
    list the submissions for a particular assignment, correlated with student names.
    """
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('classroom', 'v1', http=creds.authorize(Http()))

    print()
    print('Assignments:')
    print('===================================================================')
    print()
    courseWork = service.courses().courseWork().list(courseId=courseId).execute()
    pretty_print(courseWork['courseWork'])

    print()
    print('Student submissions for 1.5 Homework:')
    print('===================================================================')
    print()
    courseWorkId = {item['title']: item['id'] for item in courseWork['courseWork']}
    studentSubmissions = service.courses().courseWork().studentSubmissions()
    submissionsFor1_5Homework = studentSubmissions.list(courseId=courseId,
                                                        courseWorkId=courseWorkId['1.5 Homework']).execute()
    for submission in submissionsFor1_5Homework['studentSubmissions']:
        studentId = submission['userId']
        studentProfile = service.userProfiles().get(userId=studentId).execute()
        print('Student Profile:')
        pretty_print(studentProfile)
        print('Submission:')
        pretty_print(submission)
        print("---------------------------------------------")


if __name__ == '__main__':
    main()
