import os
from collections import defaultdict
from shutil import copyfile
from test.test_decimal import file
import argparse
import RunJavaUtils

#
# find all the files in the path that have the same base names
def Find_Files(rootName, baseNames):
    filedict = defaultdict(list)

    for root, dirs, files in os.walk(rootName):
        for file in files:
            if (".java" in file):
                chopPoint = file.find(".java")
                checkFile = file[0:chopPoint]
                if (' ' in checkFile):
                    checkFile = checkFile[0:checkFile.find(' ')]
                if ('(' in checkFile):
                    checkFile = checkFile[0:checkFile.find('(')]                
                for baseName in baseNames:
                    if (checkFile == baseName):
                        filedict[baseName].append(file)
                        break
    return filedict



def Parse_Args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-base_names', type=str, nargs="+", help="all of the basenames for the files to copy - ex: Egg Pokeball Mantra")
    parser.add_argument('-golden_dir', type=str, help="path to where the golden copy of the java source resides")
    parser.add_argument('-student_dir', type=str, help="path to where the student copies of the java source resides")
    parser.add_argument('-csv', type=str, help="name of the .csv file where the results should be stored")
    args = parser.parse_args()
    parsed = True
    if (args.base_names == None or args.golden_dir == None or args.student_dir == None or args.csv == None):
        print("Missing required argument (they're all required)")
        parser.print_help()
        parsed = False
    
    return (parsed, args.base_names, args.golden_dir, args.student_dir, args.csv)

def Check_Each_Base(goldenDir, tempPath, baseNames, studentDir, csvName):
    goldenSources = Find_Files(goldenDir, baseNames)
    studentFiles = Find_Files(studentDir, baseNames)
    csv=open(csvName, "w")
    for baseName in baseNames:
        goldenSource = goldenDir + "\\" + goldenSources[baseName][0]
        (success, author, package, className, goldenLines) = RunJavaUtils.Copy_And_Run_Java_File(tempPath, goldenSource)
        if (success == False):
            print("!!!!!Build failure for golden source"  + goldenSources[baseName][0])
            csv.close()
            return
        RunJavaUtils.Copy_And_Run_Files(studentDir, studentFiles[baseName], tempPath, csv, True, True, goldenLines)
        goldenLines=[]    
    csv.close()
    

def main():    
    (parsed, baseNames, goldenDir, studentDir, csvName) = Parse_Args()
    if (parsed):
        tempPath = RunJavaUtils.Create_Temp_Dir()
        Check_Each_Base(goldenDir, tempPath, baseNames, studentDir, csvName)
        RunJavaUtils.Clean_And_Remove_Temp_Dir(tempPath)

if __name__ == '__main__':
    main()  
               
    