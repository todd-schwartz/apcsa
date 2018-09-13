# you may need to do a pip install XlsxWriter
#https://xlsxwriter.readthedocs.io/getting_started.html
import xlsxwriter


class ExcelWriter:    
    def __init__(self, name):
            self.workbook = xlsxwriter.Workbook(name)
            self.worksheet = self.workbook.add_worksheet()
            self.currentRow = 0
            self.currentCol = 0            
            self.courier_format = self.workbook.add_format({'font_name':'Courier New'})
            self.courier_format.set_font_size(11)
            self.courier_format.set_text_wrap()
            self.courier_format.set_shrink()
            self.courier_format.set_align('top')
            self.maxCol = []
            self.name=name
    
    def Inc_Row(self):
        self.currentRow = self.currentRow + 1
        self.currentCol = 0
        
    def Inc_Max_Col(self, stringVal):
        while (len(self.maxCol) <= self.currentCol):
            self.maxCol.append(10)
        if (self.maxCol[self.currentCol] < len(stringVal)):
            self.maxCol[self.currentCol] = len(stringVal) * 1.5
    
    def Add_String(self, stringVal):
        self.Inc_Max_Col(stringVal)
        self.worksheet.write_string(self.currentRow, self.currentCol, stringVal, self.courier_format)
        self.currentCol = self.currentCol + 1
    
    def Add_String_Array(self, lines):
        finalString = ""
        for line in lines:
            self.Inc_Max_Col(line)
            finalString = finalString + line + "\n"
        self.worksheet.write_string(self.currentRow, self.currentCol, finalString, self.courier_format)
        self.currentCol = self.currentCol + 1
        
    def Add_Rich_Test(self, lines):
        test=self.workbook.add_format({'font_name':'Courier New'})
        test.set_indent(4)
        test2=self.workbook.add_format({'font_name':'Courier New'})
        test2.set_indent(8)
        self.worksheet.write_string(1, 1, "Test", test)
        self.worksheet.write_string(2, 1, "Test2", test2)
        newLines=[]
        indents={}        
        for line in lines:
            indent = 0
            for letter in line:
                if (letter=="\t"):
                    indent = indent + 4
                elif (letter.isspace()):
                    indent = indent + 1
                else:
                    break;
            if (indent != 0):
                if (indent not in indents):
                    indents[indent]=self.workbook.add_format()
                    indents[indent].set_indent(indent)                    
                newLines.append(indents[indent])
            newLines.append(line)
        newLines.append(self.courier_format)
        self.worksheet.write_rich_string(0, 0, *newLines)
        
        
    def Close(self):
        letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q']
        colNum = 0
        for colWidth in self.maxCol:
            colString = letters[colNum] + ":" + letters[colNum]
            self.worksheet.set_column(colString, colWidth)
            colNum = colNum + 1        
        self.workbook.close()
        print("Created:" + self.name)
        


excelWriter = ExcelWriter("test.xlsx")
excelWriter.Add_Rich_Test(["this is\n","\ta test\n","\t\tanother test\n","final test\n"])
excelWriter.Close()

