from intbase import InterpreterBase


# Enumerated type for our different language data types
class Type:
    def __init__(self, type_name, supertype_name=None):
        self.type_name = type_name
        self.supertype_name = supertype_name

    def __eq__(self, other):
        return (
            self.type_name == other.type_name
            and self.supertype_name == other.supertype_name
        )


# Represents a value, which has a type and its value
class Value:
    def __init__(self, type_obj, value=None):
        self.t = type_obj
        self.v = value

    def value(self):
        return self.v

    def set(self, other):
        self.t = other.t
        self.v = other.v

    def type(self):
        return self.t

    def is_null(self):
        return self.v == None and self.t != Type(InterpreterBase.NOTHING_DEF)
  
    def is_typeless_null(self):
        return self.v == None and self.t == Type(InterpreterBase.NULL_DEF)
    
    def __eq__(self, other):
        return self.t == other.t and self.v == other.v


# val is a string with the value we want to use to construct a Value object.
# e.g., '1234' 'null' 'true' '"foobar"'
def create_value(val):
    if val == InterpreterBase.TRUE_DEF:
        return Value(Type(InterpreterBase.BOOL_DEF), True)
    elif val == InterpreterBase.FALSE_DEF:
        return Value(Type(InterpreterBase.BOOL_DEF), False)
    elif val.lstrip('-').isnumeric():
        return Value(Type(InterpreterBase.INT_DEF), int(val))
    elif val[0] == '"' :
        return Value(Type(InterpreterBase.STRING_DEF), val.strip('"'))
    elif val == InterpreterBase.NULL_DEF:
        return Value(Type(InterpreterBase.NULL_DEF), None)
    else:
        return None


# create a default value of the specified type; type_def is a Type object
def create_default_value(type_def):
    if type_def == Type(InterpreterBase.BOOL_DEF):
        return Value(Type(InterpreterBase.BOOL_DEF), False)
    elif type_def == Type(InterpreterBase.STRING_DEF):
        return Value(Type(InterpreterBase.STRING_DEF), "")
    elif type_def == Type(InterpreterBase.INT_DEF):
        return Value(Type(InterpreterBase.INT_DEF), 0)
    elif type_def == Type(
        InterpreterBase.NOTHING_DEF
    ):  # used for void return type on methods
        return Value(Type(InterpreterBase.NOTHING_DEF), None)
    else:
        return Value(
            type_def, None
        )  # the type is a class type, so we return null for default val, with proper class type


# Used to track user-defined types (for classes) as well as check for type compatibility between
# values of same/different types for assignment/comparison
class TypeManager:
    def __init__(self):
        self.map_typename_to_type = {}
        self.map_tclass_to_parameters = {}
        self.__setup_primitive_types()

    # used to register a new class name (and its supertype name, if present as a valid type so it can be used
    # for type checking.
    # needs to be called the moment we parse the class name and superclass name to enable things like linked lists
    # and other self-referential structures
    def add_class_type(self, class_name, superclass_name):
        class_type = Type(class_name, superclass_name)
        self.map_typename_to_type[class_name] = class_type

    def is_valid_type(self, typename, return_type_check=False):
        if '@' in typename:
            # its a templetized type
            tclass = typename.split('@')[0]
            tparams = typename.split('@')[1:]
            count_params_found = 0
            tparam_found = False
            for tparam in tparams:
                if tparam in self.map_typename_to_type:
                    tparam_found = True
                    count_params_found += 1
                elif tparam in self.map_tclass_to_parameters[tclass]:
                    tparam_found = True
                    count_params_found += 1

            return (tclass in self.map_tclass_to_parameters) and (tparam_found) and len(self.map_tclass_to_parameters[tclass]) == count_params_found
        elif typename in self.map_typename_to_type:
            return True
        else:
            for param in self.map_tclass_to_parameters:
                if not return_type_check:
                    if typename in self.map_tclass_to_parameters[param] or typename == param:
                        return True
            return False
        

    # return Type object for specified typename string 
    def get_type_info(self, typename):
        if not self.is_valid_type(typename):
            return None
        return self.map_typename_to_type[typename]

    # args are strings
    def is_a_subtype(self, suspected_supertype, suspected_subtype):
        if not self.is_valid_type(suspected_supertype) or not self.is_valid_type(
            suspected_subtype
        ):
            return False
        cur_type = suspected_subtype
        while True:
            if (
                suspected_supertype == cur_type
            ):  # passing a Student object to a Student parameter
                return True
            type_info = self.get_type_info(cur_type)
            if type_info.supertype_name is None:
                return False
            cur_type = (
                type_info.supertype_name #check suspected supertype is in the inheritance chain
            )  # check the base class of the subtype next

    # typea and typeb are Type objects
    def check_type_compatibility(self, typea, typeb, for_assignment):
        # if either type is invalid (E.g., the user referenced a class name that doesn't exist) then
        # return false
        if not self.is_valid_type(typea.type_name) or not self.is_valid_type(
            typeb.type_name
        ):
            return False
        # if a is a supertype of b, then the types are compatible
        if  ('@' in typea.type_name) and ('@' in typeb.type_name):   
            if typea.type_name == typeb.type_name:
                return True
            elif(for_assignment):
                typea_class= typea.type_name.split('@')[0]
                typeb_class= typeb.type_name.split('@')[0]
                typea_params = typea.type_name.split('@')[1:]
                typeb_params = typeb.type_name.split('@')[1:]
                tyepa_index = 0
                for param in typea_params:
                    if param in self.map_tclass_to_parameters[typea_class]:
                        if typeb_params[tyepa_index] in self.map_typename_to_type:
                            return True
                        else:
                            return False
                    elif param in self.map_typename_to_type:
                        if param == typeb_params[tyepa_index]:
                            return True
                        else:
                            if typeb_params[tyepa_index] in self.map_tclass_to_parameters[typea_class]:
                                return True
                            else:
                                return False
                    else:
                            return False                
        if  ('@' not in typea.type_name) and ('@' not in typeb.type_name):   
            if self.is_a_subtype(
                typea.type_name, typeb.type_name
            ):  # animal = person or animal == person
                return True
            # if b is a supertype of a, and we're not doing assignment then the types are compatible
            if not for_assignment and self.is_a_subtype(
                typeb.type_name, typea.type_name
            ):  # person == animal
                return True
       
        # if the types are identical then they're compatible
        if typea == typeb:
            return True
        # if either is a primitive type, but the types aren't the same, they can't match
        if ('@' in typea.type_name) or ('@' in typeb.type_name): 
            if '@' in typea.type_name:
                tclassaname = typea.type_name.split('@')[0]
            else:
                tclassaname = typea.type_name
            if '@' in typeb.type_name:
                tclassbname = typeb.type_name.split('@')[0]
            else:
                tclassbname = typeb.type_name
            if tclassbname == tclassaname:
                return True
        if (
            typea.type_name in self.primitive_types
            or typeb.type_name in self.primitive_types
        ):
            for p in self.map_tclass_to_parameters:
                if (typea.type_name in self.map_tclass_to_parameters[p]) or (typeb.type_name in self.map_tclass_to_parameters[p]):
                    return True
            else:
                return False
        # by the time we get here, the types must be class types and not primitives
        # check for one or both of the types to be the null type, in which the types are compatible
        # e.g., setting an object reference to null, or comparing two obj references
        if (
            typea.type_name == InterpreterBase.NULL_DEF
            or typeb.type_name == InterpreterBase.NULL_DEF
        ):
            return True
        
        # all other cases
        return False

    # add our primitive types to our map of valid types
    def __setup_primitive_types(self):
        self.primitive_types = {
            InterpreterBase.INT_DEF,
            InterpreterBase.STRING_DEF,
            InterpreterBase.BOOL_DEF,
        }
        self.map_typename_to_type[InterpreterBase.INT_DEF] = Type(
            InterpreterBase.INT_DEF
        )
        self.map_typename_to_type[InterpreterBase.STRING_DEF] = Type(
            InterpreterBase.STRING_DEF
        )
        self.map_typename_to_type[InterpreterBase.BOOL_DEF] = Type(
            InterpreterBase.BOOL_DEF
        )
        self.map_typename_to_type[InterpreterBase.NULL_DEF] = Type(
            InterpreterBase.NULL_DEF
        )

    def add_template_class_type(self,tclass_name, tclass_parameters):
        #get all parameterized Types
        param_types = self.get_parameterized_types(tclass_parameters)
        self.map_tclass_to_parameters[tclass_name] = param_types
        
    def get_parameterized_types(self,tclass_parameters):
        param_list = []
        for param in tclass_parameters:
            param_list.append(param)
        return param_list

