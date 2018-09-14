import os
from shutil import move
from shutil import copyfile
import subprocess
import re
import ExcelWriter 
from unittest.test import test_result



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
def Convert_Source_To_Excel_Compat_List(sourceName):
    try:
        sourceFile = open(sourceName, "r")
        result = sourceFile.readlines();
        sourceFile.close()
    except UnicodeDecodeError:
        result = ["File cannot be read as text"]    
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
                        result.append(tempStr)
                        tempStr = ""
                    else:
                        tempStr = tempStr + str(c)
            else:
                tempStr = tempStr + "utf(" + str(a) + ")"
    if (len(tempStr) != 0):
        tempStr = tempStr.rstrip()
        result.append(tempStr)
        
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

def Copy_And_Run_Java_File(tempDir, source, classNameArg):
    (author, package, className) = Get_Java_Info(source)
    if (classNameArg != None):
        className = classNameArg            
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

def Add_Header(values, excelWriter):

    for value in values:
        excelWriter.Add_String(value)
    excelWriter.Inc_Row()
    
def Create_Header(excelWriter, addOutput, addFile, goldLines):
    header = ["Author", "Ran"]
    if (len(goldLines) != 0):
        addOutput = True
        header.append("diffLines")
        header.append("golden output")
    if (addOutput):
        header.append("output")
    if (addFile):
        header.append("sourceFile")
    Add_Header(header, excelWriter)
    
def Append_Run_Data(fileName, success, author, package, className, output, source, excelWriter, addOutput, addFile, goldLines):
        excelWriter.Add_String(author)       
        excelWriter.Add_String(str(success))
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
        for stringList in stringLists:
            excelWriter.Add_String_Array(stringList, 8)
        if (addFile and source != ""):
            excelWriter.Add_String_Array(Convert_Source_To_Excel_Compat_List(source), 4)
        excelWriter.Inc_Row()  
# one by one, copy the files from the source dir to the temp dir, run them,
# and store off the results in a .csv
def Copy_And_Run_Files(sourceDir, files, tempDir, excelWriter, addOutput, addFile, goldLines):
    Create_Header( excelWriter, addOutput, addFile, goldLines)

    for file in files: 
        source = sourceDir + "\\" + file       
        (success, author, package, className, output) = Copy_And_Run_Java_File(tempDir, source, None)
        Append_Run_Data(file, success, author, package, className, output, source, excelWriter, addOutput, addFile, goldLines)
             
 
                
    
  
    