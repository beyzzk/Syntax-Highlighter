import tkinter as tk
import re

# CFG
# statement -> print_stmt|if_else_stmt|assign_stmt|typed_var_decl|while_stmt|for_stmt;
# print_stmt -> 'print' '(' string ')' ';'
# if_stmt -> 'if' '(' condition ')' '{' statement '}' ['else' '{' statement'}']
# condition -> identifier operator number ';'
# assign_stmt -> identifier '=' number ';'
#statement -> type identifier = number ;
#type -> 'int' | 'float' | 'double';
#function_decl -> type identifier '(' parameters ')' '{' statement '}';
#parameters -> [ type identifier { ',' type identifier } ];
#while_stmt -> 'while' '(' condition ')' '{' statement '}';
#for_stmt -> 'for' '(' init ';' condition ';' update ')' '{' statement '}';
#init -> typed_variable_decl;
#update -> identifier '=' expression;

#token tiplerine renk atama
TOKEN_COLORS={
    "keyword":"blue",
    "identifier":"black",
    "number":"darkorange",
    "string":"darkcyan",
    "operator":"red",
    "delimiter":"grey",
    "function":"purple",
    "single_comment":"green"
}

#anahtar kelimeler
KEYWORDS={"if","else","print","int","float","double","for","while"}

#token ayırıcı fonksiyon
def lexer(code):
    tokens=[]
    #regex ile kelime eşleşmeleri
    token_specification=[
        ("single_comment", r'//.*'),
        ("float_number", r'\d+\.\d+'),
        ("number", r'\d+'),
        ("string", r'"[^"]*"'),
        ("identifier", r'[a-zA-Z_]\w*'), 
        ("operator", r'==|!=|<=|>=|[+\-*/=<>]'),
        ("delimiter", r'[();{}]'),
        ("whitespace", r'\s+'),
    ]
    tok_regex="|".join(f"(?P<{name}>{pattern})" for name,pattern in token_specification)

    for match in re.finditer(tok_regex,code):
        kind=match.lastgroup
        value=match.group()
        if kind=="identifier" and value in KEYWORDS:
            kind="keyword"
        if kind=="identifier":
            end_pos=match.end()
            if end_pos<len(code) and code[end_pos]=='(':
                kind="function"
        if kind == "float_number":
            kind = "number"
        if kind !="whitespace":
            tokens.append((kind,value,match.start(),match.end()))
    return tokens

def parser(tokens,label,text_widget):
    i = 0
    length = len(tokens)

    def try_parse(*parsers):
        nonlocal i
        for parser_func in parsers:
            old_i = i
            if parser_func():
                return True
            i = old_i  #başarısız olduysa geri sarıcak
        return False


    text_widget.tag_remove("syntax_error", "1.0", "end")

    def match(expected_type, expected_value=None):
        nonlocal i
        if i >= length:
            return False
        tok_type, tok_val, start, end = tokens[i]
        if tok_type != expected_type:
            return False
        if expected_value and tok_val != expected_value:
            return False
        i += 1
        return True

    def parse_print_stmt():
        return (
            match("keyword", "print") and
            match("delimiter", "(") and
            match("string") and
            match("delimiter", ")") and
            match("delimiter", ";")
        )

    def parse_assign_stmt():
        return (
            match("identifier") and
            match("operator", "=") and
            match("number") and
            match("delimiter", ";")
        )

    def parse_if_stmt():
        #if bloğu
        if not (
            match("keyword", "if") and
            match("delimiter", "(") and
            match("identifier") and
            match("operator") and
            match("number") and
            match("delimiter", ")") and
            match("delimiter", "{") and
            (
                parse_print_stmt() or parse_assign_stmt()
            ) and
            match("delimiter", "}")
        ):
            return False

        #else bloğu varsa
        if i < length and tokens[i][0] == "keyword" and tokens[i][1] == "else":
            if not (
                match("keyword", "else") and
                match("delimiter", "{") and
                (
                    parse_print_stmt() or parse_assign_stmt()
                ) and
                match("delimiter", "}")
            ):
                return False

        #if tek başına da çalışabilir,else varsa da geçerli 
        return True

    
    def parse_typed_variable_decl():
        if not match("keyword"):  #int,float,double
            return False

        type_token = tokens[i - 1][1]

        if not match("identifier"):
            return False
        if not match("operator", "="):
            return False

        if not match("number"):
            return False  #hem int hem float burada eşleşebiliyor

        value = tokens[i-1][1]

        if type_token == "int":
            if not re.fullmatch(r'\d+', value):
                return False
        elif type_token in ("float", "double"):
            if not re.fullmatch(r'\d+(\.\d+)?', value):
                return False

        if not match("delimiter", ";"):
            return False

        return True


    def parse_function_decl():
        if not match("keyword"):
            return False
        type_token = tokens[i - 1][1]
        if type_token not in ("int", "float", "double"):
            return False

        if not match("identifier"):
            return False

        if not match("delimiter", "("):
            return False

        #parametreler(isteğe bağlı)
        if match("keyword"):  
            param_type = tokens[i - 1][1]
            if param_type not in ("int", "float", "double"):
                return False
            if not match("identifier"):
                return False

            while match("delimiter", ","):
                if not match("keyword"):
                    return False
                if tokens[i - 1][1] not in ("int", "float", "double"):
                    return False
                if not match("identifier"):
                    return False

        if not match("delimiter", ")"):
            return False

        #burada ya gövdeyle başlar ya da noktalı virgülle
        if match("delimiter", "{"):
            #gövde:tek statement destekliyor
            if not try_parse(
                parse_print_stmt,
                parse_assign_stmt,
                parse_typed_variable_decl,
                parse_if_stmt,
                parse_while_stmt,
                parse_for_stmt
            ):
                return False
            if not match("delimiter", "}"):
                return False
        elif match("delimiter", ";"):
            #gövdesiz fonksiyon bildirimi
            pass
        else:
            return False

        return True

    def parse_while_stmt():
        if not match("keyword", "while"):
            return False
        if not match("delimiter", "("):
            return False
        if not match("identifier"):
            return False
        if not match("operator"):  
            return False
        if not match("number"):
            return False
        if not match("delimiter", ")"):
            return False
        if not match("delimiter", "{"):
            return False
        if not ( 
            parse_print_stmt() or
            parse_assign_stmt() or
            parse_typed_variable_decl() or
            parse_if_stmt()
        ):
            return False
        if not match("delimiter", "}"):
            return False
        
        return True


    def parse_for_stmt():
        if not match("keyword", "for"):
            return False
        if not match("delimiter", "("):
            return False
        if not parse_typed_variable_decl():
            return False
        if not match("identifier"):
            return False
        if not match("operator"):
            return False
        if not match("number"):
            return False
        if not match("delimiter", ";"):
            return False
        if not match("identifier"):
            return False
        if not match("operator", "="):
            return False
        if not (
            (match("identifier") or match("number")) and
            match("operator") and
            (match("identifier") or match("number"))
        ):
            return False

        if not match("delimiter", ")"):
            return False
        if not match("delimiter", "{"):
            return False
        if not (
            parse_print_stmt() or
            parse_assign_stmt() or
            parse_typed_variable_decl() or
            parse_if_stmt()
        ):
            return False
        if not match("delimiter", "}"):
            return False

        return True

    while i<length:
        if tokens[i][0] == "single_comment":
            i += 1
            continue
        if not try_parse(parse_print_stmt, parse_assign_stmt, parse_if_stmt,
                        parse_typed_variable_decl, parse_function_decl,
                        parse_while_stmt, parse_for_stmt):
            label.config(text="Syntax Error", fg="red")
            return False

    label.config(text="Syntax OK", fg="green")
    return True

previous_code=""
#gui renklendirme
def highlight():
    global previous_code
    code=text.get("1.0","end-1c") #guideki yazı alınır
    if code==previous_code:
        root.after(300,highlight)
        return
    previous_code=code
    text.tag_remove("token","1.0","end") #önceki renklendrimeyi siler
    for tag in TOKEN_COLORS:
        text.tag_config(tag,foreground=TOKEN_COLORS[tag])
        text.tag_remove(tag,"1.0","end")

    tokens=lexer(code) #alınan yazı yani kullanıcının yazdıgı kod lexer fonksiyonuna gönderilir
    for kind, val, start, end in tokens:
        start_index=f"1.0+{start}c"
        end_index=f"1.0+{end}c"
        text.tag_add(kind, start_index, end_index)

    if tokens:
        parser(tokens,status_label,text)

    root.after(300, highlight) #300ms sonra tekrar kontrol eder

#tkinter ile gui oluşturma 
root=tk.Tk()
root.title("Syntax Highlighter")
text=tk.Text(root, font=("Consolas",12))
text.pack(expand=True, fill='both')
#guida syntax ok/error yazısı için
status_label = tk.Label(root, text="", font=("Consolas", 12))
status_label.pack()
#guida temizle butonu için 
def clear_all():
    text.delete("1.0", "end")
    status_label.config(text="")
    text.tag_remove("syntax_error", "1.0", "end")
clear_button = tk.Button(root, text="Temizle", command=clear_all)
clear_button.pack()

highlight()
root.mainloop()
