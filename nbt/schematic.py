import nbt

class Schematic(nbt.NBTFile):
    def __init__(self,*args,buffer="rb",**kwargs):
        super().__init__(*args,**kwargs)

        self.blocks = list(self.get_value("Blocks"))
        self.width = self.get_value("Width")
        self.height = self.get_value("Height")
        self.length = self.get_value("Length")

    def count(self,id_):
        """Returns how many blocks with the specified ID are in the schematic"""
        return self.blocks.count(id_)

    def get_noair(self):
        """Returns a list of the blocks without the air blocks"""
        return [b for b in self.blocks if b != 0]
    
    def get_value(self,key):
        """Returns the value of a given key"""
        return self[key].value

    def get_valuestr(self,key):
        """Returns the value of a given key in string form"""
        return self[key].valuestr()

    def print_tree(self):
        """Outputs a pretty tree to the console"""
        print(self.pretty_tree())
