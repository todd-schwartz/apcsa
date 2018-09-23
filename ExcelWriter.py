# you may need to do a pip install XlsxWriter
#https://xlsxwriter.readthedocs.io/getting_started.html
import xlsxwriter
from lib2to3.pgen2.tokenize import tabsize


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
            self.writtenCells = {}
            
    def Add_Header(self, headerLines):
        row = 0;
        maxCol = 0;
        for header in headerLines:
            col = 0
            for headerLine in header:
                self.Write_String(row, col, headerLine)
                col = col + 1
                maxCol = max(col, maxCol)
        self.currentCol = maxCol
        
    
    def Write_String(self, row, col, stringVal, formatValue):
        # by putting chr(2) at the front of the string, google docs will not remove
        # the leading spaces
        tabString = " " * 4
        stringVal = stringVal.replace("\t", tabString)
        self.Inc_Max_Col(stringVal)
        

        stringVal = chr(2) + stringVal;
        stringVal = stringVal.strip()
        print(stringVal)
        # storing it in col/row because we are going to walk down the columns & merge the cells
        if (col not in self.writtenCells):
            self.writtenCells[col] = []       
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
        self.Write_String(self.currentRow, self.currentCol, stringVal, self.default_format)
        self.currentCol = self.currentCol + 1
    
    def Add_String_Array(self, lines, tabSize):
        currentRow = self.currentRow
        
        for line in lines:
           
            finalLine = line.rstrip();
#            spacePos = 0
#             while(spacePos < len(line) and line[spacePos].isspace()):
#                 if (line[spacePos] == "\t"):
#                     insertSize += tabSize
#                 else:
#                     insertSize += 1
#                 spacePos += 1            
#             finalLine = line[spacePos:].strip()
            insertFormat = self.Get_Indent_Format(0)
            self.Write_String(currentRow, self.currentCol, finalLine, insertFormat)
            currentRow += 1
        self.endRow = max(self.endRow, currentRow)
        self.currentCol = self.currentCol + 1
        
    def Possible_Merge(self, colNumber, priorVal, row, stringVal, formatVal):
        if ((priorVal + 1) < row):
            mergeStart = self.letters[colNumber] + str(priorVal + 1)
            mergeEnd = self.letters[colNumber] + str(row + 1)
            print("Merging " + mergeStart + ":" + mergeEnd + " = " + stringVal)                    
            self.worksheet.merge_range(mergeStart + ":" +  mergeEnd, stringVal, formatVal)
        
    def Merge_Cells(self):
        for colNumber in self.writtenCells:
            priorVal = 0
            lastString = ""
            lastFormat = None
            for (row, stringVal, formatVal) in self.writtenCells[colNumber]:
                self.Possible_Merge(colNumber, priorVal, row, stringVal, formatVal)            
                priorVal = row
                lastString = stringVal
                lastFormat = formatVal
            self.Possible_Merge(colNumber, priorVal, self.endRow, lastString, lastFormat)
        
        
    def Close(self):
        #self.Merge_Cells()
        
        colNum = 0
        for colWidth in self.maxCol:
            colString = self.letters[colNum] + ":" + self.letters[colNum]
            #print ("setting width " + colString + " " + str(colWidth))
            self.worksheet.set_column(colString, colWidth)
            colNum = colNum + 1        
        self.workbook.close()
        print("Created:" + self.name)        
