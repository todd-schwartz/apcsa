# you may need to do a pip install XlsxWriter
#https://xlsxwriter.readthedocs.io/getting_started.html
import xlsxwriter
import collections


class ExcelWriter:
    letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q']    
    def __init__(self, name):
            self.workbook = xlsxwriter.Workbook(name)
            self.worksheet = self.workbook.add_worksheet()
            self.currentRow = 0
            self.endRow = 0
            self.currentCol = 0            
            self.default_format = self.workbook.add_format()
            self.default_format.set_font_size(11)
            self.default_format.set_text_wrap()
            #self.default_format.set_shrink()
            self.default_format.set_align('top')
            self.maxCol = []
            self.indentFormat = {}
            self.name=name
            self.writtenCells = collections.defaultdict(list)
            self.mergeable = set()
            
    def Add_Header(self, headerLines, mergeable):
        self.mergeable.update(mergeable)
        maxRow = 0;
        col = 0
        headerFormat = self.workbook.add_format({'bold':True,'locked':True})
        for header in headerLines:
            row = 0
            for headerLine in header:
                self.Write_String(row, col, headerLine, headerFormat, 4)
                row = row + 1
                maxRow = max(row, maxRow)
            col = col + 1
        self.currentRow = maxRow
        
    
    def Write_String(self, row, col, stringVal, formatValue, tabSize):
        # by putting chr(2) at the front of the string, google docs will not remove
        # the leading spaces
        tabString = " " * tabSize
        stringVal = stringVal.replace("\t", tabString)
        self.Inc_Max_Col(stringVal)
        

        stringVal = chr(2) + stringVal;
        stringVal = stringVal.strip()
        #print(stringVal)
        # storing it in col/row because we are going to walk down the columns & merge the cells
        if (col in self.mergeable):   
            self.writtenCells[col].append((row, stringVal, formatValue))
        self.worksheet.write_string(row, col, stringVal, formatValue)
            
    def Get_Indent_Format(self, indentSize):
        if (indentSize not in self.indentFormat):
            temp_format = self.workbook.add_format({'font_name':'Courier New'})
            temp_format.set_font_size(11)
            #temp_format.set_text_wrap()
            #temp_format.set_shrink()
            temp_format.set_align('top')
            temp_format.set_indent(indentSize)
            self.indentFormat[indentSize] = temp_format
        return self.indentFormat[indentSize]
    
    def Inc_Row(self):
        self.currentRow = self.endRow + 1
        self.endRow = self.currentRow
        self.currentCol = 0
        
    def Inc_Max_Col(self, stringVal):
        while (len(self.maxCol) <= self.currentCol):
            self.maxCol.append(1)
        self.maxCol[self.currentCol] = max(self.maxCol[self.currentCol], len(stringVal))

    
    def Add_String(self, stringVal):        
        self.Write_String(self.currentRow, self.currentCol, stringVal, self.default_format, 8)
        self.currentCol = self.currentCol + 1
    
    def Add_String_Array(self, lines, tabSize):
        currentRow = self.currentRow
        
        for line in lines:
           
            finalLine = line.rstrip();
            insertFormat = self.Get_Indent_Format(0)
            self.Write_String(currentRow, self.currentCol, finalLine, insertFormat, tabSize)
            currentRow += 1
        self.endRow = max(self.endRow, currentRow)
        self.currentCol = self.currentCol + 1
        
    def Possible_Merge(self, colNumber, priorVal, row, stringVal, formatVal):
        if (priorVal < (row - 1)):
            mergeStart = self.letters[colNumber] + str(priorVal + 1)
            mergeEnd = self.letters[colNumber] + str(row)
            #print("Merging " + mergeStart + ":" + mergeEnd + " = " + stringVal)                    
            self.worksheet.merge_range(mergeStart + ":" +  mergeEnd, stringVal, formatVal)
        
    def Merge_Cells(self):
        for colNumber in self.writtenCells:
            priorVal = 0
            lastString = ""
            lastFormat = None
            for (row, stringVal, formatVal) in self.writtenCells[colNumber]:
                self.Possible_Merge(colNumber, priorVal, row, lastString, lastFormat)            
                priorVal = row
                lastString = stringVal
                lastFormat = formatVal
            self.Possible_Merge(colNumber, priorVal, self.endRow, lastString, lastFormat)
        
        
    def Close(self):
        self.Merge_Cells()
        
        colNum = 0
        for colWidth in self.maxCol:
            colString = self.letters[colNum] + ":" + self.letters[colNum]
            #print ("setting width " + colString + " " + str(colWidth))
            self.worksheet.set_column(colString, colWidth)
            colNum = colNum + 1        
        self.workbook.close()
        print("Created:" + self.name) 
        
def Test_Code():
    excelWriter = ExcelWriter("test1.xlsx")
    header=[["Name"],["Ran"],["Words"],["Other","Words"]]
    excelWriter.Add_Header(header, [0,1])    
    words = ["This", " is", "     a", "   test"]
    otherWords = ["Long lines but not many", "\tof them"]
    excelWriter.Add_String("name1")
    excelWriter.Add_String("true")
    excelWriter.Add_String_Array(words, 8)
    excelWriter.Add_String_Array(otherWords, 4)
    excelWriter.Inc_Row()
    excelWriter.Add_String("name2")
    excelWriter.Add_String("false")
    words[3] = "second\ttest"
    otherWords[0]="\t\t\tTesting tabs, many"
    excelWriter.Add_String_Array(words,8)
    excelWriter.Add_String_Array(otherWords, 4)
    excelWriter.Close()
    
#Test_Code()
