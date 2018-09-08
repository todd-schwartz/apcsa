import os
from shutil import copyfile
import RunJavaUtils
from collections import defaultdict
import argparse

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
def Copy_And_Run_Files(sourceDir, tempDir, f):    
    cwd = os.getcwd()
    os.chdir(tempDir)
    dirs = os.listdir(sourceDir)

    f.write("FileName, Author, Class Name, Package, Ran\n")
    for file in dirs:
        if (".java" == file[(len(file) - len(".java")):]):
            source = sourceDir + "\\" + file           
            (author, package, className) = RunJavaUtils.Get_Java_Info(source)
            print (source + " " + author + " " + package + " " + className)
            destName = className + ".java"
            dest = tempDir + "\\" + destName
            print("copying " + source + " to " + dest)
            copyfile(source, dest)                                               
            (success, output) = RunJavaUtils.Run_Java_File(destName, package, className)
            f.write(file + "," + author + "," + className + "," + package + "," + str(success) + "\n") 
            os.remove(destName)   
    os.chdir(cwd)
    



def Parse_Args():
    parser = argparse.ArgumentParser()    
    parser.add_argument('-student_dir', type=str, help="path to where the student copies of the java source resides")
    parser.add_argument('-output', type=str, help="name of the .csv file where the results should be stored")
    args = parser.parse_args()
    parsed = True
    if (args.student_dir == None or args.output == None):
        print("Missing required argument (they're all required)")
        parser.print_help()
        parsed = False
    
    return (parsed, args.student_dir, args.output)

    
    

def main():    
    (parsed, studentDir, output) = Parse_Args()
    if (parsed):
        tempPath = RunJavaUtils.Create_Temp_Dir()

        f=open(output, "w")    
        Copy_And_Run_Files(studentDir, tempPath, f)
        f.close()
        print ("Created:" + output)
        RunJavaUtils.Clean_And_Remove_Temp_Dir(tempPath)

if __name__ == '__main__':
    main() 