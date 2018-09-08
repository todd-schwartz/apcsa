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


 
 

#
# one by one, copy the files from the source dir to the temp dir, run them,
# and store off the results in a map
# map is [baseName][original file name]["author"]
#                                      ["output"]
def Copy_And_Run_Files(sourceDir, tempDir, baseNames, sources):
    cwd = os.getcwd()
    os.chdir(tempDir)
    results={}
    for baseName in baseNames:
        results[baseName]={}
        for file in sources[baseName]:
            source = sourceDir + "\\" + file
            destName = baseName + ".java"
            dest = tempDir + "\\" + destName
            print("copying " + source + " to " + dest)
            copyfile(source, dest)                        
            (author, package, className) = RunJavaUtils.Get_Java_Info(destName)            
            (success, output) = RunJavaUtils.Run_Java_File(destName, package, baseName)
            results[baseName][file]={}            
            results[baseName][file]["author"]=author
            results[baseName][file]["output"]=output
            results[baseName][file]["success"]=success            
            os.remove(destName)   
    os.chdir(cwd)
    return results

#
# Change the output returned from running the sub process into a string 
def Change_Binary_To_String_List(binary):
    result=[]
    tempStr = ""
    if (len(binary) > 0):        
        for a in binary:
            if (isinstance(a, str)):
                tempStr = tempStr + a
            if (a > 8 and a < 127):
                c = chr(a)
                if (c != '\r'):
                    if (c == '\n'):
                        #remove trailing spaces, they are impossible to mark wrong since they are ambiguous in text
                        tempStr = tempStr.rstrip()
                        result.append("\"" + tempStr + "\"")
                        tempStr = ""
                    else:
                        tempStr = tempStr + str(c)
            else:
                tempStr = tempStr + "utf(" + str(a) + ")"
    return result
    
#appends the strings onto the end of the csv.
#assumes the first line should only be separated by 1 comma
#and all others by n commas
#used for adding the golden/actual lines when a diff is detected
# 
def Append_String_Lists(list1, list2, numCommas):
    result = ""
    commas = "" 
    #we return mismatch because the binary form may have differed based on trailing
    #spaces.  The string form, with those spaces stripped may match perfectly
    mismatch = False   
    for i in range(0, numCommas):
        commas = commas + ","
    maxLen = max(len(list1), len(list2))
    for i in range(0, maxLen):
        check1 = ""
        check2 = ""
        if (i == 0):
            result = result + ","
        else:
            result = result + "\n"
            result = result + commas
        if (i < len(list1)):  
            check1 = list1[i]         
            result = result + list1[i]
        result = result + ","
        if (i < len(list2)):
            check2 = list2[i]            
            result = result + list2[i]
        if (check1 != check2):
            result = result + ", <-"
            mismatch = True                
    return (result, mismatch)

#
# Go through the results of the run & check for differences.  Return the results in 
# lines suitable for a .csv mapped by the original file name
def Check_Diffs(goldenResults, studentResults, baseNames):
    results = {}
    for baseName in baseNames:        
        for goldenKey in goldenResults[baseName].keys():
            goldenResult = goldenResults[baseName][goldenKey]["output"]
            goldenLines = Change_Binary_To_String_List(goldenResult)
                            
        for studentKey in studentResults[baseName].keys():            
            studentString = ", " + studentResults[baseName][studentKey]["author"] + ", "
            if (studentResults[baseName][studentKey]["success"] == False):
                results[studentKey]=studentString + "Build Error"
            else:
                studentResult = studentResults[baseName][studentKey]["output"]
                if (studentResult == goldenResult):
                    results[studentKey]=studentString + "Match"
                else:
                    studentLines = Change_Binary_To_String_List(studentResult)
                    if ((len(studentLines) == 1) and ("error" in studentLines[0])):
                        results[studentKey] = studentString + studentLines[0] + "\n"
                    else:
                        (diffLines, mismatch) = Append_String_Lists(goldenLines, studentLines, 3)
                        if (mismatch):
                            diffString = studentString + "Differ"                                
                            diffString = diffString + diffLines
                            results[studentKey]=diffString
                        else:
                            results[studentKey]=studentString + "Match"
    return results

# Just dump the results into a .csv
def Print_Report(results, fileName):
    f=open(fileName, "w")
    f.write("FileName, Author, Diff Results, Golden Results, Student Results\n")
    for key in results:
        f.write(key +  results[key] + "\n")
    f.close()
    print("Created:" + fileName)

def Parse_Args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-base_names', type=str, nargs="+", help="all of the basenames for the files to copy - ex: Egg Pokeball Mantra")
    parser.add_argument('-golden_dir', type=str, help="path to where the golden copy of the java source resides")
    parser.add_argument('-student_dir', type=str, help="path to where the student copies of the java source resides")
    parser.add_argument('-output', type=str, help="name of the .csv file where the results should be stored")
    args = parser.parse_args()
    parsed = True
    if (args.base_names == None or args.golden_dir == None or args.student_dir == None or args.output == None):
        print("Missing required argument (they're all required)")
        parser.print_help()
        parsed = False
    
    return (parsed, args.base_names, args.golden_dir, args.student_dir, args.output)



def main():    
    (parsed, baseNames, goldenDir, studentDir, output) = Parse_Args()
    if (parsed):
        tempPath = RunJavaUtils.Create_Temp_Dir()
    
        goldenSources = Find_Files(goldenDir, baseNames)
        goldenResults = Copy_And_Run_Files(goldenDir, tempPath, baseNames, goldenSources)
    
        studentFiles = Find_Files(studentDir, baseNames)
        studentResults = Copy_And_Run_Files(studentDir, tempPath, baseNames, studentFiles)
        
        results = Check_Diffs(goldenResults, studentResults, baseNames)    
        Print_Report(results, output)            
        RunJavaUtils.Clean_And_Remove_Temp_Dir(tempPath)

if __name__ == '__main__':
    main()  
               
    