#!/usr/bin/env python
import sys
import os
import string
from optparse import OptionParser

class MathMate(object):
    def __init__(self):
        self.doc = sys.stdin.read()
        
        self.indent_size = int(os.environ['TM_TAB_SIZE'])
        if os.environ.get('TM_SOFT_TABS') == "YES":
            self.indent = " " * self.indent_size
        elif os.environ.get('TM_SOFT_TABS') == "NO":
            self.indent = "\t"
        
        self.tmln = int(os.environ.get('TM_LINE_NUMBER'))
        self.tmli = int(os.environ.get('TM_LINE_INDEX'))
        self.selected_text = os.environ.get('TM_SELECTED_TEXT')
    
    def count_indents(self, line):
        count = 0
        space_count = 0

        for char in line.rstrip():
            if char == "\t":
                count += 1
            elif char == " ":
                space_count = ((space_count + 1) % self.indent_size)
                if space_count == 0:
                    count += 1
            else:
                break
        return count
    
    def reformat_block(self, block, initial_indent_level = None):
        scope = []
        statements = self.get_statements(block)
        if statements is None:
            return
            
        indented_statements = []
        if initial_indent_level is None:
            initial_indent_level = self.count_indents(block)
        
        for ssln, ssli, ssp, esln, esli, esp, statement in statements:
            result = []
            indent_level = initial_indent_level
            scope.append("source")
        
            for line in statement.splitlines(True):
                pos = 0
                while pos < len(line):
                    c1 = line[pos]
                    c2 = line[pos:pos+2]
                    c3 = line[pos:pos+3]
                    scope_index = len(scope) - 1

                    pc = line[pos-1] if pos > 0 else None

                    nnsc = None
                    for i in range(pos, len(line)):
                        if line[i] not in (" ", "\t"):
                            nnsc = line[i]
                            break
                    
                    if "string" in scope:
                        if c2 == '\\"':
                            result += c2
                            pos += 2
                            continue

                        if c1 == '"':
                            scope.pop()
                            result += c1
                            pos += 1
                            continue

                        result += c1
                        pos += 1
                        continue

                    if "comment" in scope:
                        if c3 == "\\*)":
                            result += c3
                            pos += 3
                            continue

                        if c2 == "*)":
                            scope.pop()
                            result += c2
                            pos += 2
                            continue

                        result += c1
                        pos += 1
                        continue

                    if "source" in scope:
                        if pos == 0:
                            if len(line.strip()) > 0 and line.strip()[0] in ("]", "}", ")"):
                                result += (self.indent * (indent_level - 1))
                            else:
                                result += (self.indent * indent_level)

                        if c1 in (" ", "\t"):
                            vsc = string.ascii_letters + string.digits
                            if pc is not None and pc in vsc and nnsc in vsc:
                                result += " "
                            pos += 1
                            continue
                    
                        if c3 == "^:=":
                            scope.append("define")
                            indent_level += 1
                            result += " ", c3, " "
                            pos += 3
                            continue
                    
                        if c3 in ("===", ">>>"):
                            result += " ", c3, " "
                            pos += 3
                            continue

                        if c2 in (":=", "^="):
                            scope.append("define")
                            indent_level += 1
                            result += " ", c2, " "
                            pos += 2
                            continue

                        if c2 in ("*^", "&&", "||", "==", ">=", "<=", ";;", "/.", "->", ":>", "@@", "<>", ">>", "/@", "/;", "//", "~~"):
                            result += " ", c2, " "
                            pos += 2
                            continue

                        if c2 == "..":
                            result += c2, " "
                            pos += 2
                            continue

                        if c2 == "(*":
                            scope.append("comment")
                            result += c2
                            pos += 2
                            continue

                        if c1 in ("[", "{", "("):
                            scope.append("nest")
                            indent_level += 1
                            result += c1
                            pos += 1
                            continue

                        if c1 in ("]", "}", ")"):
                            scope.pop()
                            indent_level -= 1
                            if scope[-1] == "define":
                                indent_level -= 1
                                scope.pop()
                            result += c1
                            pos += 1
                            continue

                        if c1 == ",":
                            result += c1, " "
                            pos += 1
                            continue
                    
                        if c1 == "=":
                            scope.append("define")
                            indent_level += 1
                            result += " ", c1, " "
                            pos += 1
                            continue

                        if c1 in ("+", "-", "*", "/", "^", "!", ">", "<", "|", "?"):
                            result += " ", c1, " "
                            pos += 1
                            continue

                        if c1 == "&":
                            result += " ", c1
                            pos += 1
                            continue

                        if c1 in ("@", ";", "#"):
                            if scope[-1] == "define":
                                indent_level -= 1
                                scope.pop()
                            result += c1
                            pos += 1
                            continue

                        if c1 == '"':
                            scope.append("string")
                            result += c1
                            pos += 1
                            continue

                        result += c1
                        pos += 1
                        continue
                    
                    scope_index -= 1

            indented_statements.append("".join(result))
        return indented_statements
    
    def reformat_current_statement(self):
        current_statement = self.get_current_statement()
        if current_statement is None:
            return
            
        ssln, ssli, ssp, esln, esli, esp, statement = current_statement
        
        sys.stdout.write(self.doc[0:ssp])
        sys.stdout.write("".join(self.reformat_block(statement)))
        sys.stdout.write(self.doc[esp:])
        
    def reformat_selection(self):
        sys.stdout.write("".join(self.reformat_block(self.doc)))
        
    def reformat(self):
        if self.selected_text is not None:
            self.reformat_selection()
        else:
            self.reformat_current_statement()
    
    def get_statements(self, block):
        statements = []
        level = 0
        scope = "next"
        
        pos = 0
        ss_pos = 0
        current = []
        ss_line_number = 1
        ss_line_index = 0
        line_number = 1
        line_index_start = 0
    
        while pos < len(block):
            c1 = block[pos]
            c2 = block[pos:pos+2]
            c3 = block[pos:pos+3]
        
            if c1 == "\n":
                line_number += 1
                line_index_start = pos + 1
        
            line_index = pos - line_index_start
        
            if scope == "next":
                if c1 not in (" ", "\t", "\n"):
                    if current != []:
                        statements.append((ss_line_number, ss_line_index, ss_pos, line_number, pos - line_index_start, pos, "".join(current)))
                        
                    ss_pos = pos
                    ss_line_number = line_number
                    ss_line_index = line_index
                    current = []
                    scope = "source"
                    continue
                
                current += c1
                pos += 1
                continue
        
            if scope == "source":
                if c2 == "(*":
                    scope = "comment"
                    current += c2
                    pos += 2
                    continue
                
                if level == 0 and c1 == ";":
                    scope = "next"
                    current += c1
                    pos += 1
                    continue
            
                if c1 in ("[", "(", "{"):
                    level += 1
                    current += c1
                    pos += 1
                    continue
            
                if c1 in ("]", ")", "}"):
                    level -= 1
                    current += c1
                    pos += 1
                    continue
            
                if c1 == '"':
                    scope = "string"
                    current += c1
                    pos += 1
                    continue
            
                current += c1
                pos += 1
                continue
        
            if scope == "string":
                if c2 == '\\"':
                    current += c2
                    pos += 2
                    continue
            
                if c1 == '"':
                    scope = "source"
                    current += c1
                    pos += 1
                    continue
            
                current += c1
                pos += 1
                continue
        
            if scope == "comment":
                if c3 == '\\*)':
                    current += c3
                    pos += 3
                    continue
            
                if c2 == '*)':
                    scope = "source"
                    current += c2
                    pos += 2
                    continue
            
                current += c1
                pos += 1
                continue
    
        if current != []:
            statements.append((ss_line_number, ss_line_index, ss_pos, line_number, line_index, pos, "".join(current)))
        
        return statements
        
    def get_current_statement(self):
        statements = self.get_statements(self.doc)
        if statements is None:
            return None
        
        previous_statement = None
        
        for current_statement in statements:
            ssln, ssli, ssp, esln, esli, esp, statement = current_statement
            
            if self.tmln < ssln:
                continue
            
            if self.tmln > esln:
                if previous_statement is None or ssp > previous_statement[2]:
                    previous_statement = current_statement
                continue
            
            if self.tmln == ssln and self.tmli < ssli:
                continue
                
            if self.tmln == esln and self.tmli > esli:
                if previous_statement is None or ssp > previous_statement[2]:
                    previous_statement = current_statement
                continue
            
            return ssln, ssli, ssp, esln, esli, esp, statement
        
        if previous_statement is not None:
            return previous_statement
            
        return None
    
    def show_current_statement(self):
        print "Cursor Position: (Line: %d, Index: %d)" % (self.tmln, self.tmli)
        ssln, ssli, ssp, esln, esli, esp, statement = self.get_current_statement()
        print "Statement Boundaries: (Line: %d, Index: %d) -> (Line: %d, Index: %d)" % (ssln, ssli, esln, esli)
        print statement

def main():
    parser = OptionParser()
    (options, args) = parser.parse_args()
    command = args[0]
    
    mm = MathMate()

    if command == "show_current_statement":
        mm.show_current_statement()
        return
    
    if command == "reformat":
        mm.reformat()
        return
    
    if command == "reformat_current_statement":
        mm.reformat_current_statement()
        return
    
    if command == "reformat_selection":
        mm.reformat_selection()
        return
        
    print "Command not recognized: %s" % command

if __name__ == '__main__':
    main()