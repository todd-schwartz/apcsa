from __future__ import print_function
from googleapiclient.discovery import build
from googleapiclient import http
from httplib2 import Http
from oauth2client import file, client, tools
import json
import datetime
import argparse
import io
import os
import RunJavaUtils
import ExcelWriter
import Filter


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly',
          'https://www.googleapis.com/auth/classroom.rosters.readonly',
          'https://www.googleapis.com/auth/classroom.coursework.students.readonly',
          'https://www.googleapis.com/auth/drive https://www.googleapis.com/auth/drive.file',
          'https://www.googleapis.com/auth/drive.appdata',
          'https://www.googleapis.com/auth/drive.apps.readonly']

courseId = '14911700941'

def Parse_Args(filter1):
    parser = argparse.ArgumentParser(parents=[tools.argparser])
    parser.add_argument('-assignment', type=str, help="name of the assignment from google classroom (if not specified, all assignments will be listed for you to choose from)")
    parser.add_argument('-xlsx', type=str, required=True, help="name of the .xlsx file where the results should be stored")
    parser.add_argument('-output', dest='output', action='store_true', help='append the output from running the file into the .csv')
    parser.add_argument('-no_output', dest='output', action='store_false', help='do not append the output from running the file into the .csv')
    parser.add_argument('-file', dest='file', action='store_true', help='append the original student source into the .csv')
    parser.add_argument('-no_file', dest='file', action='store_false', help='do not append the original student source into the .csv')
    parser.add_argument("-golden_source", help='if you want to compare the output of a golden source to the student sources specify a file with this option')
    filter1.Add_Args(parser)
    parser.set_defaults(output=True)
    parser.set_defaults(file=True)
    args = parser.parse_args()
    filter1.Read_Args(args)
    return args

def Open_Classroom(args):
    store = file.Storage('token.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
        creds = tools.run_flow(flow, store, flags=args)
    service = build('classroom', 'v1', http=creds.authorize(Http()))
    drive = build('drive', 'v3', http=creds.authorize(Http()))
    return (service, drive)

def Print_And_Select_Assignment(assignments):
    assignments_sorted_by_due_date = sorted(assignments, key=lambda x: due_datetime(x))
    for index, assignment in enumerate(assignments_sorted_by_due_date):
        line_item = '{}. {} (due {})'.format(index, assignment['title'], due_datetime(assignment))
        print(line_item)

    print()
    selection = input('Select one of the above assignments: ')
    selected_assignment = assignments_sorted_by_due_date[int(selection)]
    return selected_assignment

def Verify_Assignment(service, assignmentName):
    courseWork = service.courses().courseWork().list(courseId=courseId).execute()
    assignments = filter(lambda x: x['workType'] == 'ASSIGNMENT', courseWork['courseWork'])
    if (assignmentName == None):
        assignmentSelected = Print_And_Select_Assignment(assignments)
    else:
        for testAssignment in assignments:
            if (assignmentName == testAssignment['title']):
                assignmentSelected = testAssignment  
                break
        if (assignmentSelected == None):
            print("Assignment: " + assignmentName + " Not found, do not specify the assignment on the command line to get a full list")
    return assignmentSelected

CHUNK_SIZE = 1024 * 1024
def Copy_Student_Java_Files(tempDir, service, drive, assignmentSelected, excelWriter, addOutput, addFile, goldLines, filter1):
    RunJavaUtils.Create_Header( excelWriter, addOutput, addFile, goldLines)
    studentSubmissions = service.courses().courseWork().studentSubmissions()
    submissions_for_sslected_assignment = studentSubmissions.list(courseId=courseId,
                                                                  courseWorkId=assignmentSelected['id']).execute()
    for submission in submissions_for_sslected_assignment['studentSubmissions']:
        studentId = submission['userId']
        studentProfile = service.userProfiles().get(userId=studentId).execute()
        studentName = studentProfile['name']['fullName']
        filtered=[]
        updated=False
        print(studentName)
        assignmentSub = submission['assignmentSubmission']
        if ('attachments') in assignmentSub:
            for singleAssignment in assignmentSub['attachments']:
                if 'driveFile' in singleAssignment:
                    driveFile = singleAssignment['driveFile']
                    if ('alternateLink') in driveFile:                        
                        fileName = driveFile['title']
                        if (".java" in fileName):
                            if (filter1.Filter_On_File_Name_Only() == False or filter1.Use_File(fileName, [], False)):
                                
                                className = fileName.replace(".java","")
                                txtName = fileName + ".txt"
                                tempName = os.path.join(tempDir, txtName)
                                print ("Downloding to " + tempName)
                                outFile = io.FileIO(tempName, mode='wb')
                                fileID = driveFile['id']
                                try:
                                    request = drive.files().get_media(fileId=fileID)
                                    downloader=http.MediaIoBaseDownload(outFile, request, chunksize=CHUNK_SIZE)
                                    download_finished = False
                                    while download_finished is False:
                                        _, download_finished = downloader.next_chunk()
                                    print ("Download complete")
                                    (success, ignore1, package, ignore2, output) = RunJavaUtils.Copy_And_Run_Java_File(tempDir, tempName, className)
                                except Exception as e:
                                    success = False
                                    package = ""
                                    output = ["could not download file: {}".format(e)]
                                if (filter1.Use_File(fileName, output, success)):
                                    if (success):                                                               
                                        RunJavaUtils.Append_Run_Data(fileName, success, studentName, package, className, output, tempName, excelWriter, addOutput, addFile, goldLines)
                                        updated = True
                                    else:
                                        RunJavaUtils.Append_Run_Data(fileName, success, studentName, package, className, output, tempName, excelWriter, addOutput, addFile, goldLines)
                                        updated = True
                            else:
                                print ("Filtered out: " + fileName + " base on name")
                                filtered.append(fileName)
        if (updated == False):
            ranLine = "missing"
            if (len(filtered)):
                ranLine = ranLine + " filtered out these files: " + str(filtered)            
            RunJavaUtils.Append_Run_Data("missing", ranLine, studentName, "missing", "", [""], "", excelWriter, addOutput, addFile, goldLines)


def main():
    filter1 = Filter.Filter()
    args = Parse_Args(filter1)
    (service, drive) = Open_Classroom(args)
    assignmentSelected = Verify_Assignment(service, args.assignment)
    if assignmentSelected:
        tempPath = RunJavaUtils.Create_Temp_Dir()
        goldenLines = []
        if args.golden_source is not None:
            (success, author, package, className, goldenLines) = RunJavaUtils.Copy_And_Run_Java_File(tempPath, args.goldenSource, None)
            if (success == False):
                print("Build failure for golden source")
                return
        writer = ExcelWriter.ExcelWriter(args.xlsx)
        Copy_Student_Java_Files(tempPath, service, drive, assignmentSelected, writer, args.output, args.file, goldenLines, filter1)
                
        
#        files = Create_File_List(studentDir)    
#    RunJavaUtils.Copy_And_Run_Files(studentDir, files, tempPath, writer, addOutput, addFile, goldenLines)
        writer.Close()
        RunJavaUtils.Clean_And_Remove_Temp_Dir(tempPath)

def pretty_print(data):
    print(json.dumps(data, indent=4, sort_keys=True))





def due_datetime(assignment):
    result = None
    if 'dueDate' in assignment:
        due_time = assignment['dueTime']
        due_date = assignment['dueDate']
        result = datetime.datetime(year=due_date['year'], month=due_date['month'], day=due_date['day'],
                                   hour=due_time['hours'], minute=due_time.get('minutes', 0))
    return result


def main1():
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
    selection = input('Select one of the above assignments: ')
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
