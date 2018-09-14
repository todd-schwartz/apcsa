import argparse

class Filter:
    def __init__(self):
        self.inFileName = None
        self.notInFileName = None
        self.inOutput = None
        self.notInOutput = None
    
    def Add_Args(self, parser):
        parser.add_argument('-filt_in_file_name', type=str, nargs="+", help="use this student submission if the string(s) passed in (case insensitive) is part of the file name (anded with all other filt options selected)")
        parser.add_argument('-filt_not_in_file_name', type=str, nargs="+", help="use student submission file if the string(s) passed in (case insensitive) is not part of the file name (anded with all other filt options selected)")
        parser.add_argument('-filt_in_output', type=str,nargs="+",  help="use this student submission if the output of running the program contains the string(s) passed in  (case insensitive) (anded with all other filt options selected) EX: -filt_in_output \"wet dog\" -filt_not_in_output \"cat\" The student submission will only be added to the .xlsx if the output contains the phrase wet dog, and also does not contain cat")
        parser.add_argument('-filt_not_in_output', type=str, nargs="+", help="use this student submission if the output of running the program does not contain the string(s) passed in  (case insensitive) (anded with all other filt options selected)")
    
    def Convert_Arg(self, arg):
        if (arg == None):
            return None
        else:
            for i in range(0, len(arg)):
                arg[i] = arg[i].lower()
            return arg

        
    def Read_Args(self, args):
        self.inFileName = self.Convert_Arg(args.filt_in_file_name)
        self.notInFileName = self.Convert_Arg(args.filt_not_in_file_name)
        self.inOutput = self.Convert_Arg(args.filt_in_output)
        self.notInOutput = self.Convert_Arg(args.filt_not_in_output)
    
    def Filter_On_File_Name_Only(self):
        if (self.inOutput == None and self.notInOutput == None):
            return True
        return False
    
    def Init_Check_Bool(self, check, initVal):
        if (check == None):
            return [True]
        else:
            return [initVal for i in range(len(check))]
        
    def Check_In(self, isIn, check, line):
        if (check != None):
            for i in range(len(check)):
                if (check[i] in line.lower()):
                    isIn[i] = True
    
    def Check_Not_In(self, isNotIn, check, line):
        if (check != None):
            for i in range(len(check)):
                if (check[i] in line.lower()):
                    isNotIn[i] = False
                    
    def Check_Loop(self, checkResults, check, lines, checkIn):
        if (check != None):            
            for line in lines:
                if (checkIn):
                    self.Check_In(checkResults, check, line)
                else:
                    self.Check_Not_In(checkResults, check, line)
                    
    def Final_Loop(self, checkResults):
        for check in checkResults:
            if (check == False):
                return False
        return True
        
        
    def Use_File(self, originalFileName, output, success):
        inFileNameRes = self.Init_Check_Bool(self.inFileName, False)
        notInFileNameRes = self.Init_Check_Bool(self.notInFileName, True)
        inOutputRes = self.Init_Check_Bool(self.inOutput, False)
        notInOutputRes = self.Init_Check_Bool(self.notInOutput, True)
        
        self.Check_In(inFileNameRes, self.inFileName, originalFileName)
        self.Check_Not_In(notInFileNameRes, self.notInFileName, originalFileName)
        if (success == True):
            self.Check_Loop(inOutputRes, self.inOutput, output, True)
            self.Check_Loop(notInOutputRes, self.notInOutput, output, False)
        return (self.Final_Loop(inFileNameRes) and self.Final_Loop(notInFileNameRes) and self.Final_Loop(inOutputRes) and self.Final_Loop(notInOutputRes))
    
