import os
from shutil import move
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
        output = subprocess.check_output(["javac", destName], stderr=True)
    except subprocess.CalledProcessError:
        output = "build error"
        success = False
    if (success == True):
        try:
            if (package != ""):
                move(className, fullClassName)
            output = subprocess.check_output(["java", invokeName], stderr=True)                
        except subprocess.CalledProcessError:
            output = "run error"
            success = False
        try:
            os.remove(fullClassName)
        except FileNotFoundError:
            print("build failed")
    if (package != ""):
        os.rmdir(package)
    return (success, output)


    
  
    