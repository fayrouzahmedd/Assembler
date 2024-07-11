class Assembler(object):
    def __init__(self, asmpath='', mripath='', rripath='', ioipath='') -> None:
        super().__init__()
        self.__address_symbol_table = {}
        self.__bin = {}
        if asmpath:
            self.read_code(asmpath)   
        self.__mri_table = self.__load_table(mripath) if mripath else {}
        self.__rri_table = self.__load_table(rripath) if rripath else {}
        self.__ioi_table = self.__load_table(ioipath) if ioipath else {}
    

    def read_code(self, path:str):
        assert path.endswith('.asm') or path.endswith('.S'), \
                        'file provided does not end with .asm or .S'
        self.__asmfile = path.split('/')[-1] 
        with open(path, 'r') as f:
            self.__asm = [s.rstrip().lower().split() for s in f.readlines()]


    def assemble(self, inp='') -> dict:
        assert self.__asm or inp, 'no assembly file provided'
        if inp:
            assert inp.endswith('.asm') or inp.endswith('.S'), \
                        'file provided does not end with .asm or .S'
        if not self.__asm:
            self.read_code(inp)
        self.__rm_comments()
        self.__first_pass()
        self.__second_pass()
        return self.__bin


    # PRIVATE METHODS
    def __load_table(self, path) -> dict:
        with open(path, 'r') as f:
            t = [s.rstrip().lower().split() for s in f.readlines()]
        return {opcode:binary for opcode,binary in t}


    def __islabel(self, string) -> bool:
        return string.endswith(',')


    def __rm_comments(self) -> None:
        for i in range(len(self.__asm)):
            for j in range(len(self.__asm[i])):
                if self.__asm[i][j].startswith('/'):
                    del self.__asm[i][j:]
                    break

    def __format2bin(self, num:str, numformat:str, format_bits:int) -> str:
        if numformat == 'dec':
            return '{:b}'.format(int(num)).zfill(format_bits)
        elif numformat == 'hex':
            return '{:b}'.format(int(num, 16)).zfill(format_bits)
        else:
            raise Exception('format2bin: not supported format provided.')
        


    
    def __first_pass(self) -> None:
        linecounter = 0
        inc = 0  
        org = self.__asm[0][1] 
        for i in range(1, len(self.__asm) - 1):
            if self.__asm[i][0] == 'end':
                break
            if self.__asm[i][0] == 'org':
                org = self.__asm[i][1]
                inc = -1
            linecounter += 1
            ctr = self.__format2bin(hex(int(org, 16) + inc)[2::], 'hex', 12)
            inc += 1
            if self.__islabel(self.__asm[i][0]):  
                assert len(self.__asm[i]) >= 2, "Invalid Assembly Code, in line {}".format(linecounter + 1)  
                self.__address_symbol_table[self.__asm[i][0]] = ctr  
            self.__bin[ctr] = None  



    def __second_pass(self) -> None:
        flag = False
        for i in range(1, len(self.__asm) - 1):
            if self.__asm[i][0] == 'end':
                break
            elif 'hlt' in self.__asm[i]:  
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__rri_table['hlt']
                flag = True
            elif self.__asm[i][0] in self.__rri_table.keys():  
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__rri_table[self.__asm[i][0]]
            elif self.__asm[i][1] in self.__rri_table.keys():  
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__rri_table[self.__asm[i][1]]
            elif self.__asm[i][0] in self.__mri_table.keys():  
                if 'i' in self.__asm[i][1::]: 
                    I = '1'
                else:
                    I = '0'
                self.__bin[list(self.__bin.keys())[i - 1]] = I + self.__mri_table[self.__asm[i][0]] + \
                                                             self.__address_symbol_table[self.__asm[i][1] + ',']
            elif self.__asm[i][1] in self.__mri_table.keys():  
                if 'i' in self.__asm[i][1::]:
                    I = '1'
                else:
                    I = '0'
                self.__bin[list(self.__bin.keys())[i - 1]] = I + self.__mri_table[self.__asm[i][1]] + \
                                                             self.__address_symbol_table[self.__asm[i][2] + ',']
            elif self.__asm[i][0] in self.__ioi_table.keys():  
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__ioi_table[self.__asm[i][0]]
            elif self.__asm[i][1] in self.__ioi_table.keys(): 
                self.__bin[list(self.__bin.keys())[i - 1]] = self.__ioi_table[self.__asm[i][1]]
            elif self.__islabel(self.__asm[i][0]) and flag:  
                if self.__asm[i][1] == 'hex':  
                    self.__bin[list(self.__bin.keys())[i - 1]] = self.__format2bin(self.__asm[i][2], 'hex', 16)
                elif self.__asm[i][1] == 'dec':  
                    self.__bin[list(self.__bin.keys())[i - 1]] = self.__format2bin(self.__asm[i][2], 'dec', 16)
                else:
                    print('error')
        print(self.__bin)    
        dv = list(self.__bin.values())
        dk = list(self.__bin.keys())
        for i in range(len(dv)):  
            if dv[i] == None:
                self.__bin.pop(dk[i])
        