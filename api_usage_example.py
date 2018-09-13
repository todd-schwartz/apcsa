from __future__ import print_function
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
import json
import datetime


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.rosters.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.students.readonly']


def pretty_print(data):
    print(json.dumps(data, indent=4, sort_keys=True))


courseId = '14911700941'


def due_datetime(assignment):
    result = None
    if 'dueDate' in assignment:
        due_time = assignment['dueTime']
        due_date = assignment['dueDate']
        result = datetime.datetime(year=due_date['year'], month=due_date['month'], day=due_date['day'],
                                   hour=due_time['hours'], minute=due_time.get('minutes', 0))
    return result


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
    assignments = filter(lambda x: x['workType'] == 'ASSIGNMENT', courseWork['courseWork'])
    assignments_sorted_by_due_date = sorted(assignments, key=lambda x: due_datetime(x))
    for index, assignment in enumerate(assignments_sorted_by_due_date):
        line_item = '{}. {} (due {})'.format(index, assignment['title'], due_datetime(assignment))
        print(line_item)

    print()
    selection = raw_input('Select one of the above assignments: ')
    selected_assignment = assignments_sorted_by_due_date[int(selection)]

    print()
    print('Student submissions for {}:'.format(selected_assignment['title']))
    print('===================================================================')
    print()
    studentSubmissions = service.courses().courseWork().studentSubmissions()
    submissions_for_sslected_assignment = studentSubmissions.list(courseId=courseId,
                                                                  courseWorkId=selected_assignment['id']).execute()
    for submission in submissions_for_sslected_assignment['studentSubmissions']:
        studentId = submission['userId']
        studentProfile = service.userProfiles().get(userId=studentId).execute()
        print('Student:', studentProfile['name']['fullName'])
        print('Submission:', submission)
        print("---------------------------------------------")


if __name__ == '__main__':
    main()
