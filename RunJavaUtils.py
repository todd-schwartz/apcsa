import os
from shutil import move
from shutil import copyfile
import subprocess
import re



def Create_Temp_Dir():    
    tempBase = os.environ['TEMP']
    tempBase += "\\javaTemp"
    temp = tempBase
    tempCount = 0
    while(os.path.exists(temp)):
        tempCount += 1
        temp = tempBase + str(tempCount)
    os.mkdir(temp)
    return temp

def Clean_And_Remove_Temp_Dir(tempDir):
    dirs = os.listdir(tempDir)
    for file in dirs:
        if (file != "." and file != ".."):            
            source = tempDir + "\\" + file
            os.remove(source)
    os.rmdir(tempDir)

#
# We need the source lines to be surrounded by "    " in order for the 
# display in the .csv to be correct
def Convert_Source_To_CSV_Compat_List(sourceName):
    sourceFile = open(sourceName, "r")
    result = []
    for line in sourceFile.readlines():
        modLine = line.rstrip()
        modLine = modLine.replace("\t", "    ")
        result.append("\"" + modLine + "\"")
    sourceFile.close()
    return result 
   
def Compare_Lines(goldenList, studentList):
    maxLen = len(goldenList)
    maxLen = max(len(studentList), maxLen)
    mismatch=[]
    anyMismatch=False
    for i in range(0, maxLen):
        if (i >= len(goldenList) or i >= len(studentList)):
            mismatch.append("->")
            anyMismatch=True
        elif (goldenList[i] != studentList[i]):
            mismatch.append("->")
            anyMismatch=True
        else:
            mismatch.append(" ")
    if (anyMismatch == False):
        mismatch=["Perfect Match"]  
    return mismatch
#
# This is really cheesy.  It just grabs the first line with the word package & assumes
# that is the package name.
# same with the className  
def Get_Java_Info(fileName):
    javaFile = open(fileName, "r", encoding="latin-1" )
    package = ""
    className = ""
    author = "Unknown"
    authKey = "@author"
    for line in javaFile:        
        if ("package" in line and (("import" in line) == False) and package == ""):
            package = line.replace("package","", 1)
            package = package.replace(" ","")
            package = package.replace(";","")
            package = package.strip()
        if ("class" in line and className == ""):
            classNamePos = line.find("class") + len("class") + 1
            classNameList = re.split("\W+", line[classNamePos:])
            if (len(classNameList)):
                className = classNameList[0]
            className = className.strip()
            break;
        if (authKey in line):
            authPos = line.find(authKey)
            authPos += len(authKey)
            author = line[authPos:]
            author = author.strip()
    javaFile.close()
    return (author, package, className)

#appends the strings onto the end of the csv.
#assumes the first line should only be separated by 1 comma
#and all others by n commas
#used for adding the golden/actual lines when a diff is detected
# 
def Append_String_Lists(numCommas, lists):
    result = ""
    commas = ""    
    for i in range(0, numCommas):
        commas = commas + ","
    maxLen = 0
    for listN in lists:
        maxLen = max(len(listN), maxLen)
    for i in range(0, maxLen):
        if (i == 0):
            result = result + ","
        else:
            result = result + "\n"
            result = result + commas
        for listN in lists:
            if (i < len(listN)):
                result = result + listN[i]            
            result = result + ","   
    return (result)   


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
    if (len(tempStr) != 0):
        tempStr = tempStr.rstrip()
        result.append("\"" + tempStr + "\"")
        
    return result
 
#
# Runs the java file from the command line.  The output is in binary format (that is what subprocess returns
# If it doesn't run, output will be equal to a string. 
# If we plan to keep using, probably worth fixing this so output is always a string
def Run_Java_File(destName, package, baseName):
    className = baseName + ".class"
    invokeName = baseName
    fullClassName = className
    success = True
    if (package != ""):
        os.mkdir(package)
        fullClassName = package + "\\" + className
        invokeName = package + "." + invokeName            
    try:
        subprocess.check_output(["javac", destName], stderr=True)
    except subprocess.CalledProcessError:
        output = ["build error"]
        success = False
    if (success == True):
        try:
            if (package != ""):
                move(className, fullClassName)
            binaryOutput = subprocess.check_output(["java", invokeName], stderr=True)
            output=Change_Binary_To_String_List(binaryOutput)                        
        except subprocess.CalledProcessError:
            output = ["run error"]
            success = False
        try:
            os.remove(fullClassName)
        except FileNotFoundError:
            print("build failed")
    if (package != ""):
        os.rmdir(package)
    return (success, output)

def Copy_And_Run_Java_File(tempDir, source):
    (author, package, className) = Get_Java_Info(source)            
    destName = className + ".java"
    dest = tempDir + "\\" + destName
    print("copying " + source + " to " + dest)
    copyfile(source, dest)
    cwd = os.getcwd()
    os.chdir(tempDir)
    (success, output) = Run_Java_File(destName, package, className)
    os.chdir(cwd)
    os.remove(dest) 
    return (success, author, package, className, output)

# one by one, copy the files from the source dir to the temp dir, run them,
# and store off the results in a .csv
def Copy_And_Run_Files(sourceDir, files, tempDir, csv, addOutput, addFile, goldLines):    
    csv.write("FileName, Author, Class Name, Package, Ran")
    if (len(goldLines) != 0):
        addOutput = True
        csv.write(", diffLines")
        csv.write(", golden output")
    if (addOutput):
        csv.write(", output")
    if (addFile):
        csv.write(", sourceFile")
    csv.write("\n")
    for file in files: 
        source = sourceDir + "\\" + file       
        (success, author, package, className, output) = Copy_And_Run_Java_File(tempDir, source)
        csv.write(file + "," + author + "," + className + "," + package + "," + str(success))
        stringLists=[]
        if (len(goldLines)):
            if (success):
                stringLists.append(Compare_Lines(goldLines, output))
                stringLists.append(goldLines)
            else:
                stringLists.append([""])
                stringLists.append([""])
        if (addOutput):                
            stringLists.append(output)
        if (addFile):
            stringLists.append(Convert_Source_To_CSV_Compat_List(source))               
        if (len(stringLists) != 0):            
            csv.write(Append_String_Lists(5, stringLists))          
        csv.write("\n") 
                
    
  
    