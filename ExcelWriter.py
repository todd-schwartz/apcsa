# you may need to do a pip install XlsxWriter
#https://xlsxwriter.readthedocs.io/getting_started.html
import xlsxwriter
from lib2to3.pgen2.tokenize import tabsize


class ExcelWriter:    
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
        
    def Inc_Max_Col(self, stringVal, addVal):
        while (len(self.maxCol) <= self.currentCol):
            self.maxCol.append(1)
        self.maxCol[self.currentCol] = max(self.maxCol[self.currentCol], len(stringVal))

    
    def Add_String(self, stringVal):
        self.Inc_Max_Col(stringVal, 0)
        self.worksheet.write_string(self.currentRow, self.currentCol, stringVal, self.default_format)
        self.currentCol = self.currentCol + 1
    
    def Add_String_Array(self, lines, tabSize):
        currentRow = self.currentRow
        for line in lines:
            spacePos = 0
            insertSize = 0
            while(spacePos < len(line) and line[spacePos].isspace()):
                if (line[spacePos] == "\t"):
                    insertSize += tabSize
                else:
                    insertSize += 1
                spacePos += 1            
            finalLine = line[spacePos:].strip()
            self.Inc_Max_Col(finalLine, insertSize)
            insertFormat = self.Get_Indent_Format(insertSize)
            self.worksheet.write_string(currentRow, self.currentCol, finalLine, insertFormat)
            currentRow += 1
        self.endRow = max(self.endRow, currentRow)
        self.currentCol = self.currentCol + 1
        
        
    def Close(self):
        letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q']
        colNum = 0
        for colWidth in self.maxCol:
            colString = letters[colNum] + ":" + letters[colNum]
            self.worksheet.set_column(colString, colWidth)
            colNum = colNum + 1        
        self.workbook.close()
        print("Created:" + self.name)        

