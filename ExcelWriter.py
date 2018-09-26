# you may need to do a pip install XlsxWriter
#https://xlsxwriter.readthedocs.io/getting_started.html
import xlsxwriter


#The main component of this is entries.  It doesn't just store the cell strings in a 2D list.
#Instead, we have a 3d list, that allows us to group everything associated with a student.
#We do it that way to make it easy to compute where one student's info ends, allowing us
#to easily merge cells & add separator lines.
#Simple example (with the lines of the lists
#put onto new lines to show how they would look in excel

#entries[0]=
#[[student1],  [passFail],   [diffLine1,    [sourceLine1,
#                             diffLine2,     sourceLine2,
#                             diffLine3],    sourceLine3,
#                                            sourceLine4]]
#_________________________________________________________
#entries[1]=
#[[student2],  [passFail],   [diffLine1,    [sourceLine1,
#                             diffLine2,     sourceLine2,
#                             diffLine3],    sourceLine3,
#                                            sourceLine4]]
#_________________________________________________________
#

class ExcelWriter:
    letters=['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q']    
    def __init__(self, name):
            self.workbook = xlsxwriter.Workbook(name)
            self.worksheet = self.workbook.add_worksheet()
            self.entries=[]          
            self.name=name
            self.fontNames=[]
            self.borderFormat = {}            
            self.mergeable = set()
    
    # fontNames lets us apply different fonts per column
    # mergeable says whether we should merge all the rows to the 
    # bottom of this group (we use it for names, all the rows
    # associated with a name are merged)        
    def Add_Header(self, headerLines, fontNames, mergeable):
        self.entries.append(headerLines)
        self.fontNames=fontNames
        self.mergeable.update(mergeable)
        
    # Not the most generic name, but this needs to be called when we add the column zero block (student name for us).
    # This lets us start the next list of lists
    def Next_Student(self, studentName):
        self.entries.append([])
        self.Add_String(studentName, 0)
    
    #rip out the tabs & the newlines    
    def String_Manip(self, stringVal, tabSize):
        tabString = " " * tabSize 
        stringVal = stringVal.replace("\t", tabString)
        stringVal = stringVal.rstrip()
        return stringVal
        
    #add a single string to the list of lists, this string will occupy one column
    def Add_String(self, stringVal, tabSize):
        self.entries[-1].append([self.String_Manip(stringVal, tabSize)])

    #add a list into a column, this list will end up occupying N rows
    def Add_String_Array(self, lines, tabSize):
        for i in range(len(lines)):
            lines[i] = self.String_Manip(lines[i], tabSize)
        self.entries[-1].append(lines)
        

    #When we are finally creating our output, we want to put solid borders
    #separating the groups, but we don't want to create a ton of the same
    #format, so map them by the solid border type, font name & whether the
    #font will be bold.
    def Get_Border_Format(self, topBorder, bottomBorder, fontName, isHeader):
        if ((topBorder, bottomBorder, fontName, isHeader) not in self.borderFormat):
            temp_format = self.workbook.add_format({'font_name':fontName})
            temp_format.set_font_size(10)
            temp_format.set_align('top')
            temp_format.set_bottom(bottomBorder)
            temp_format.set_top(topBorder)
            temp_format.set_bold(isHeader)            
            if (isHeader):
                temp_format.set_align('center')
            self.borderFormat[(topBorder, bottomBorder, fontName, isHeader)] = temp_format
        return self.borderFormat[(topBorder, bottomBorder, fontName, isHeader)]

    # Determine how big we want the columns to be
    # Figure out the width of all the columns, sort
    # them, then chop off the last 3 to kill off the giant
    # outliers (3 was an arbitrary number that seemed to work)
    # average didn't work well, and neither did median (when we
    # have a lot of missing assignments, the median goes to zero).
    def Compute_Col_Width(self):
        maxCol = []
        colWidths=[[] for i in range(0, len(self.fontNames))]
        for studentValues in self.entries:
            currentCol = 0            
            for entryList in studentValues:
                for entry in entryList:              
                    colWidths[currentCol].append(len(entry) + 1)
                currentCol = currentCol + 1
        
        for colWidthList in colWidths:
            colWidthList.sort();
            #print(colWidthList)
            # not quite the max, trim off the last 3 entries, because some of those
            # are very large when there is an error 
            pos = len(colWidthList) - 3
            if (pos < 0):
                pos = len(colWidthList) - 1
            maxCol.append(colWidthList[pos]);        
        return maxCol
    
    # Set the widths of the columns in the spreadsheet based on the
    # size of the strings
    def Set_Col_Widths(self):
        maxCol = self.Compute_Col_Width()
        #print(maxCol)
        colNum = 0
        for colWidth in maxCol:
            colString = self.letters[colNum] + ":" + self.letters[colNum]
            #print ("setting width " + colString + " " + str(colWidth))
            self.worksheet.set_column(colString, colWidth)
            colNum = colNum + 1
            
    #Takes in all the lists associated with a single student
    #figures out how many rows the entries for this student will
    #occupy.  Sets the bottom row to have a default visible border
    #at the bottom - this extends the ____ all the way across the 
    #sheet.
    def Add_Default_Border(self, studentValues, startRow, isHeader):
        #figure out which list in this is the longest, that is how
        #many rows this entry will occupy
        numRows = 0
        for entryList in studentValues:
            numRows = max(numRows, len(entryList))            
        endRow = numRows + startRow - 1            
        defaultBottom = self.Get_Border_Format(0, 1, self.fontNames[0], isHeader)
        if (endRow == startRow):
            defaultBottom = self.Get_Border_Format(1, 1, self.fontNames[0], isHeader)
        self.worksheet.set_row(endRow, None, defaultBottom)
        return (numRows, endRow)
    
    # get the font name for printing this column.  We should use Courier New for things
    # like the source so that indenting is not weird
    def Get_Font_Name(self, currentCol, isHeader):
        if (isHeader == False):
            fontName = self.fontNames[currentCol]
        else:
            fontName = 'Arial'
        return fontName
    #For a given student's block, write out a single column, which will
    #be some list of values.
    def Write_Single_Column(self, startRow, endRow, currentCol, entryList, fontName, isHeader):
        currentRow = startRow
        topBorder = 1
        bottomBorder = 0
        for entry in entryList:
            #print ("Row = " + str(currentRow) + " Col = " + str(currentCol) + " Entries = " + str(entry))
            #print (str(currentRow) + ", " + str(endRow) + "top " + str(topBorder))
            if (currentRow == endRow):
                bottomBorder = 1
            else:
                bottomBorder = 0
            borderedFormat = self.Get_Border_Format(topBorder, bottomBorder, fontName, isHeader)
            #Here is how we preserve the spacing.  We use rich string to essentially create
            #a string with two formatting specifications - even though the first string is empty
            #Google sheets will then preserve the spacing instead of stripping it because it has
            #to parse two different formats.
            self.worksheet.write_rich_string(currentRow, currentCol, "", borderedFormat, entry, borderedFormat)
            currentRow = currentRow + 1
            topBorder = 0

    #For things like the student name, we want to merge all the rows associated with this student
    #to make it clearer which lines are owned by them.            
    def Possibly_Merge_Rows(self, startRow, endRow, currentCol, entryList, numRows, fontName, isHeader):
        if (len(entryList) < numRows):
            if (currentCol in self.mergeable and len(entryList) == 1):
                mergeStart = self.letters[currentCol] + str(startRow + 1)
                mergeEnd = self.letters[currentCol] + str(endRow + 1)                                        
                self.worksheet.merge_range(mergeStart + ":" +  mergeEnd, entryList[0], self.Get_Border_Format(1, 1, fontName, isHeader))

        
    # OK, we're all done, now it is time to write the file out
    def Write_Cells(self):
        self.Set_Col_Widths()        
        startRow = 0
        isHeader = True
        # now we go through one student at a time & create the output
        for studentValues in self.entries:           
            (numRows, endRow) = self.Add_Default_Border(studentValues, startRow, isHeader)
            #now walk each column
            currentCol = 0
            for entryList in studentValues:
                fontName = self.Get_Font_Name(currentCol, isHeader)
                self.Write_Single_Column(startRow, endRow, currentCol, entryList, fontName, isHeader)
                self.Possibly_Merge_Rows(startRow, endRow, currentCol, entryList, numRows, fontName, isHeader)
                currentCol = currentCol + 1
            startRow = endRow + 1
            isHeader = False 
    
    #After all the strings have been added, call this to create the actual file
    def Create_Excel_File(self):
        self.Write_Cells()
        self.workbook.close()
        print("Created:" + self.name) 
        
def Test_Code():
    excelWriter = ExcelWriter("test1.xlsx")
    header=[["Name"],["Ran"],["Words"],["Other","Words"]]
    excelWriter.Add_Header(header, ['Arial', 'Arial', 'Courier New', 'Courier New'],[0,1])    
    words = ["This\n", " is\n", "     a\n", "   test\n"]
    otherWords = ["Long lines but not many\n", "\tof them\n"]
    excelWriter.Next_Student("name1")
    excelWriter.Add_String("true", 8)
    excelWriter.Add_String_Array(words, 8)
    excelWriter.Add_String_Array(otherWords, 4)
    excelWriter.Next_Student("name2")
    excelWriter.Add_String("false", 8)
    words1 = ["Now\n", "    we\n", "   add\n", "even\n", "\t\t\tmore","\twords"]
    otherWords1 = ["And", "Now\n", "    we\n", "   add\n", "even\n", "\t\t\tmore","\twords"]
    excelWriter.Add_String_Array(words1,8)
    excelWriter.Add_String_Array(otherWords1, 4)
    excelWriter.Create_Excel_File()

    
#Test_Code()
