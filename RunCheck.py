import os
from shutil import copyfile
import RunJavaUtils
from collections import defaultdict
import argparse
import ExcelWriter




#
def Create_File_List(sourceDir):
    dirs = os.listdir(sourceDir)
    files = []
    for file in dirs:
        if (".java" == file[(len(file) - len(".java")):]):            
            files.append(file)
    return files 

 
    



def Parse_Args():
    parser = argparse.ArgumentParser()    
    parser.add_argument('-student_dir', type=str, required=True, help="path to where the student copies of the java source resides")
    parser.add_argument('-xlsx', type=str, required=True, help="name of the .xlsx file where the results should be stored")
    parser.add_argument('-output', dest='output', action='store_true', help='append the output from running the file into the .csv')
    parser.add_argument('-no_output', dest='output', action='store_false', help='do not append the output from running the file into the .csv')
    parser.add_argument('-file', dest='file', action='store_true', help='append the original student source into the .csv')
    parser.add_argument('-no_file', dest='file', action='store_false', help='do not append the original student source into the .csv')
    parser.add_argument("-golden_source", help='if you want to compare the output of a golden source to the student sources specify a file with this option')
    parser.set_defaults(output=True)
    parser.set_defaults(file=True)
    args = parser.parse_args()
    parsed = True
    if (args.student_dir == None or args.output == None):
        print("Missing required argument (they're all required)")
        parser.print_help()
        parsed = False
    
    return (parsed, args.student_dir, args.xlsx, args.output, args.file, args.golden_source)


def main():    
    (parsed, studentDir, csv, addOutput, addFile, golden_source) = Parse_Args()
    if (parsed):
        tempPath = RunJavaUtils.Create_Temp_Dir()
        goldenLines = []
        if (golden_source != None):
            (success, ignore1, ignore2, ignore3, goldenLines) = RunJavaUtils.Copy_And_Run_Java_File(tempPath, golden_source, None)
            if (success == False):
                print("Build failure for golden source")
                return
        writer = ExcelWriter.ExcelWriter(csv)                
        
        files = Create_File_List(studentDir)    
        RunJavaUtils.Copy_And_Run_Files(studentDir, files, tempPath, writer, addOutput, addFile, goldenLines)
        writer.Create_Excel_File()        
        RunJavaUtils.Clean_And_Remove_Temp_Dir(tempPath)

if __name__ == '__main__':
    main() 