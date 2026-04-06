---
title: "Python's Data Model and Metaprogramming: Descriptors, Metaclasses, and the Object Protocol"
date: 2026-03-25
summary: A comprehensive survey of Python's data model covering the dunder method protocol, descriptor machinery, metaclass system, C3 linearization MRO, class creation internals, and modern abstractions (dataclasses, attrs, pydantic) -- analyzing how CPython's object protocol enables a unified metaprogramming architecture from attribute access to class construction.
keywords: [python, data-model, metaprogramming, descriptors, metaclasses]
---

# Python's Data Model and Metaprogramming: Descriptors, Metaclasses, and the Object Protocol

*2026-03-25*

## Abstract

Python's data model -- the collection of special methods (commonly called "dunder methods") that define how objects participate in language operations -- constitutes one of the most comprehensive metaobject protocols in any mainstream programming language. Unlike languages where object behavior is fixed by the compiler, Python delegates virtually every operation (attribute access, arithmetic, comparison, iteration, context management, instance creation, and class construction itself) to user-overridable special methods resolved through a descriptor-based lookup chain. This design traces its intellectual lineage to Smalltalk's message-passing paradigm and the Common Lisp Object System's metaobject protocol, but Python's implementation is distinctive in its commitment to a uniform, introspectable object model where classes are themselves objects created by metaclasses, which are themselves classes.

This survey provides a PhD-depth analysis of CPython's data model and the metaprogramming facilities it enables. We begin with the foundational dunder methods that define the object protocol, then examine the descriptor protocol that underlies attribute access, property, classmethod, and staticmethod. We analyze the metaclass system from `type.__new__` through `__prepare__` and `__init_subclass__`, and the C3 linearization algorithm that resolves method lookup order in multiple inheritance hierarchies. We examine the class creation machinery including three-argument `type()`, `__build_class__`, `__class_cell__`, and `__set_name__`. We cover decorators as syntactic metaprogramming, `__slots__` as a memory optimization that fundamentally alters instance layout, and conclude with modern abstractions -- dataclasses (PEP 557), attrs, and pydantic -- that leverage the data model to generate class infrastructure automatically. Throughout, we provide performance measurements, CPython implementation details, and comparative analysis of alternative approaches.

## 1. Introduction

The phrase "data model" in Python refers to the interface between user-defined objects and the language runtime: the set of conventions by which objects communicate their capabilities to the interpreter [1]. When Python evaluates `a + b`, it does not execute a hardcoded addition operation; instead, it invokes `a.__add__(b)`, falling back to `b.__radd__(a)` if the first call returns `NotImplemented`. When `len(x)` is called, the interpreter delegates to `x.__len__()`. When `for item in collection` executes, the interpreter calls `collection.__iter__()` to obtain an iterator, then repeatedly calls `__next__()` on that iterator. This pervasive delegation is the defining characteristic of Python's object model and the foundation of its metaprogramming capabilities.

The design has deep historical roots. Guido van Rossum has cited both Smalltalk and the C programming language as influences on Python's object system [2]. From Smalltalk, Python inherited the idea that everything is an object and that operations are messages dispatched through a lookup mechanism. From C, it inherited the pragmatic concern with implementation efficiency, reflected in CPython's representation of objects as C structs containing a reference count, a type pointer, and type-specific data. The unification of types and classes in Python 2.2 -- documented in van Rossum's "Unifying types and classes in Python 2.2" and later "The Inside Story on New-Style Classes" blog post -- was the pivotal architectural decision that made the current data model possible, introducing descriptors, the `__mro__` attribute, and the use of `type` as the default metaclass [3].

At the C level, every Python object is represented by a `PyObject` structure containing `ob_refcnt` (reference count) and `ob_type` (a pointer to the object's type). The type object (`PyTypeObject`) contains a table of function pointers -- `tp_hash`, `tp_repr`, `tp_call`, `tp_getattro`, `tp_richcompare`, and dozens more -- that implement the type's behavior. When the interpreter encounters a special method invocation, it looks up the corresponding slot in the type object's function pointer table, bypassing the normal attribute lookup mechanism for performance [4]. This "slot-based" dispatch is the reason that special methods must be defined on the class, not the instance: the interpreter consults the type's C-level slot table, not the instance's `__dict__`.

The scope of this survey is CPython-centric, covering the data model as specified in the Python Language Reference and as implemented in CPython 3.12-3.14. We address eight interconnected topics: the dunder method protocol (Section 3), descriptors (Section 4), metaclasses (Section 5), method resolution order (Section 6), decorators (Section 7), `__slots__` (Section 8), class creation machinery (Section 9), and modern alternatives that build on the data model (Section 10). Section 11 provides a comparative synthesis, Section 12 identifies open problems, and Section 13 concludes.

## 2. Foundations

### 2.1 The Metaobject Protocol Tradition

Python's data model belongs to a tradition of metaobject protocols (MOPs) that began with Smalltalk-80's reflective architecture and was formalized by Kiczales, des Rivieres, and Bobrow in "The Art of the Metaobject Protocol" (AMOP, 1991) [5]. A metaobject protocol exposes the implementation of the object system itself as objects that can be specialized by the programmer. In CLOS, the metaclass controls how instances are allocated, how slots are accessed, how methods are dispatched, and how generic functions combine methods from multiple applicable classes. Python's data model provides analogous capabilities: `__new__` controls allocation, `__init__` controls initialization, descriptors control attribute access, metaclasses control class creation, and the MRO controls method dispatch ordering.

The key distinction between Python's approach and CLOS is one of explicitness versus protocol. CLOS provides a formal, layered MOP with distinct metaobject types for classes, generic functions, methods, and slot definitions, with each layer explicitly documented as an extension point. Python's MOP is more implicit: the "protocol" is the collection of dunder methods that the interpreter recognizes, documented in the language reference but not formalized as an abstract interface. This makes Python's system easier to learn incrementally but harder to reason about formally, as the interactions between different dunder methods are specified through prose rather than algebraic laws.

### 2.2 CPython's Object Representation

At the C level, CPython's object model is built on two fundamental structures defined in `Include/object.h` [4]:

```c
typedef struct _object {
    Py_ssize_t ob_refcnt;
    PyTypeObject *ob_type;
} PyObject;

typedef struct {
    PyObject ob_base;
    Py_ssize_t ob_size;
} PyVarObject;
```

Every Python object begins with a `PyObject` header. Variable-length objects (lists, tuples, strings) use `PyVarObject`, which adds an `ob_size` field. The type object `PyTypeObject` (defined in `Include/cpython/object.h` and implemented primarily in `Objects/typeobject.c`) is itself a `PyVarObject` containing over 50 function pointer slots that implement the type's behavior. CPython uses a C-level technique of struct embedding to simulate inheritance: because `PyVarObject` begins with a `PyObject`, any `PyVarObject*` can be safely cast to `PyObject*`, and similarly for type-specific structures like `PyLongObject` or `PyListObject` [6].

The type's function pointer table is organized into several sub-tables: `tp_as_number` (numeric operations), `tp_as_sequence` (sequence operations), `tp_as_mapping` (mapping operations), and `tp_as_async` (async operations). When a type is defined in Python rather than C, the interpreter generates "slot wrapper" functions that bridge from C slots to Python special methods. For example, when a class defines `__add__`, CPython installs a C function in the `nb_add` slot that calls the Python-level `__add__` method. Conversely, when Python code accesses `int.__add__`, a "method wrapper" descriptor is created that delegates to the C-level `nb_add` slot [4].

### 2.3 The Duality of Slots and Dunder Methods

A subtle but crucial aspect of CPython's design is the bidirectional mapping between C-level type slots and Python-level special methods. The file `Objects/typeobject.c` contains a table (`slotdefs`) that defines this mapping: each entry associates a C slot name (e.g., `tp_hash`) with a Python method name (e.g., `__hash__`), a C wrapper function, and flags indicating the calling convention [4].

When a new Python class is created, `type.__new__` calls `fixup_slot_dispatchers()`, which iterates through the class's MRO looking for Python-level definitions of special methods and installs corresponding C-level slot functions. Conversely, when a C extension type defines a slot without a corresponding Python method, the `add_operators()` function creates Python-level descriptors that wrap the C slot. This bidirectional synchronization is what allows `len([1,2,3])` (which calls `list.__len__` via the `sq_length` C slot) and `[1,2,3].__len__()` (which calls the same C function via a method-wrapper descriptor) to produce identical results [7].

This duality has a performance implication: calling a special method through the operator syntax (`a + b`) is faster than calling it explicitly (`a.__add__(b)`), because the operator path goes directly through the C slot without descriptor lookup overhead.

## 3. The Data Model: Dunder Methods

### 3.1 Object Lifecycle Methods

#### 3.1.1 Theory

Python separates object creation into two phases: *construction* (`__new__`) and *initialization* (`__init__`). The `__new__` method is a static method (special-cased by the runtime to not require `@staticmethod`) that receives the class as its first argument and returns a new instance. The `__init__` method receives the newly created instance as `self` and initializes its state. This separation exists because some immutable types (e.g., `int`, `str`, `tuple`) must have their value set during construction, before `__init__` runs, as their content cannot be modified afterward [1].

The destruction protocol uses `__del__`, which is called when the object's reference count reaches zero (or during garbage collection of reference cycles). However, `__del__` is not a deterministic destructor like C++ destructors: the garbage collector makes no guarantees about when -- or even whether -- `__del__` will be called, and calling it can resurrect the object if a new reference is created during finalization [1].

#### 3.1.2 Evidence: The Construction Sequence

When `MyClass(args)` is evaluated, the following sequence occurs:

1. `MyClass.__call__(args)` is invoked -- since `MyClass` is an instance of `type`, this is `type.__call__(MyClass, args)`.
2. `type.__call__` invokes `MyClass.__new__(MyClass, args)` to create the instance.
3. If `__new__` returns an instance of `MyClass` (or a subclass), `type.__call__` then invokes `instance.__init__(args)`.
4. If `__new__` returns an object that is *not* an instance of `MyClass`, `__init__` is *not* called.

This protocol is implemented in `type_call()` in `Objects/typeobject.c`. The conditional invocation of `__init__` based on `isinstance` checking is a common source of bugs when `__new__` is overridden to return a different type [8].

#### 3.1.3 Implementations

```python
class Singleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, value):
        self.value = value  # Called every time Singleton() is invoked
```

The singleton pattern illustrates the `__new__`/`__init__` split: `__new__` controls whether a new object is allocated, while `__init__` runs on whatever `__new__` returns. A subtlety: because `__init__` runs every time the constructor is called (as long as `__new__` returns an instance of the class), the singleton's state is re-initialized on each call unless `__init__` includes a guard.

#### 3.1.4 Strengths and Limitations

**Strengths:** The two-phase protocol provides flexibility unavailable in languages with a single constructor. Factory patterns, caching (e.g., interning small integers), and immutable value types are straightforward to implement. The separation also supports the metaclass system, where `type.__new__` creates the class object and `type.__init__` initializes it.

**Limitations:** The `__new__`/`__init__` split is a frequent source of confusion. Most classes need only `__init__`, and the interaction between the two methods when both are overridden (especially regarding which arguments each receives) is error-prone. The non-deterministic `__del__` makes it unsuitable for resource management; context managers (`__enter__`/`__exit__`) are the preferred alternative.

### 3.2 Representation Methods

#### 3.2.1 Theory

Python defines two string representation methods: `__repr__` (intended for developers, ideally producing a string that could recreate the object) and `__str__` (intended for end users, producing a human-readable representation). The `repr()` builtin calls `__repr__`, while `str()` and `print()` call `__str__`, falling back to `__repr__` if `__str__` is not defined. The `__format__` method, called by `format()` and f-strings, allows format-spec-driven customization [1].

#### 3.2.2 The repr Contract

The informal contract for `__repr__` is stated in the documentation: "If at all possible, this should look like a valid Python expression that could be used to recreate an object with the same value." For built-in types, this contract is generally upheld (`repr([1,2,3])` returns `'[1, 2, 3]'`), but for complex objects, a `<ClassName at 0x...>` form is acceptable. The default `__repr__` provided by `object` produces `<module.ClassName object at 0x...>`.

Raymond Hettinger and other core developers have emphasized that `__repr__` is the single most important dunder method to implement on any class: it transforms opaque objects into debuggable entities [9]. The `__str__` method, by contrast, is needed only when the human-readable form differs materially from the developer-readable form.

### 3.3 Comparison and Hashing

#### 3.3.1 Theory

Python supports six comparison operations through six dunder methods: `__eq__` (==), `__ne__` (!=), `__lt__` (<), `__le__` (<=), `__gt__` (>), and `__ge__` (>=). Each should return `True`, `False`, or `NotImplemented`. When one operand returns `NotImplemented`, Python tries the reflected operation on the other operand. The `functools.total_ordering` decorator can generate the remaining four comparison methods from `__eq__` and one of `__lt__`, `__le__`, `__gt__`, or `__ge__` [10].

The `__hash__` method is tightly coupled to `__eq__` through the invariant: `a == b` implies `hash(a) == hash(b)`. If a class defines `__eq__` without `__hash__`, the class becomes unhashable (its `__hash__` is implicitly set to `None`). This was a deliberate change in Python 3 to prevent the dangerous situation in Python 2 where mutable objects with custom `__eq__` retained the default identity-based `__hash__`, violating the hash invariant when the object was mutated after insertion into a set or dict [1].

#### 3.3.2 Evidence: Hash Collision and Performance

The interaction between `__eq__` and `__hash__` has real performance consequences. If all objects in a dictionary hash to the same value (a degenerate case), dictionary lookup degrades from O(1) to O(n). CPython's dict implementation uses open addressing with a perturbation sequence based on the hash value, so well-distributed hashes are critical [11]. The default `object.__hash__` returns `id(self)` (the memory address in CPython), which provides good distribution for identity-based equality.

### 3.4 Attribute Access Methods

#### 3.4.1 Theory

Python provides three levels of attribute access customization:

1. **`__getattribute__`**: Called unconditionally for every attribute access on an instance. The default implementation (`object.__getattribute__`) implements the descriptor protocol lookup chain (see Section 4). Overriding this method intercepts *all* attribute access, including access to the method itself, creating a risk of infinite recursion [1].

2. **`__getattr__`**: Called only when normal attribute lookup fails (i.e., when `__getattribute__` raises `AttributeError`). This is the recommended hook for implementing fallback or dynamic attribute access [1].

3. **`__setattr__`** and **`__delattr__`**: Called for all attribute assignment and deletion, respectively. There is no `__setattr__`/`__delattr__` split analogous to `__getattribute__`/`__getattr__`; these methods are always called for the corresponding operations.

#### 3.4.2 The Lookup Chain

The default `object.__getattribute__` implements the following lookup order for `obj.name`:

1. Invoke `type(obj).__mro__` data descriptor `__get__` (if a data descriptor with that name exists on the class or its bases).
2. Return `obj.__dict__['name']` (if it exists in the instance dictionary).
3. Invoke `type(obj).__mro__` non-data descriptor `__get__` (if a non-data descriptor with that name exists).
4. Raise `AttributeError`, which triggers `__getattr__` if defined.

This lookup order -- data descriptors take priority over instance variables, which take priority over non-data descriptors -- is the linchpin of the entire descriptor system and explains why `property` (a data descriptor) can intercept attribute access while methods (non-data descriptors) can be overridden on instances [12].

### 3.5 The Callable Protocol

#### 3.5.1 Theory

The `__call__` method makes instances of a class callable. When `obj(args)` is evaluated, Python invokes `type(obj).__call__(obj, args)`. This is the mechanism underlying function objects (whose `__call__` is the function body), bound methods (whose `__call__` delegates to the underlying function with the bound instance), and class instantiation (where `type.__call__` orchestrates `__new__` and `__init__`) [1].

The callable protocol enables powerful patterns: callable objects with state (an alternative to closures), decorator classes, and strategy patterns where callable instances are interchangeable with functions.

### 3.6 Operator Overloading

#### 3.6.1 Theory

Python supports overloading of arithmetic operators (`__add__`, `__sub__`, `__mul__`, `__truediv__`, `__floordiv__`, `__mod__`, `__pow__`, `__matmul__`), bitwise operators (`__and__`, `__or__`, `__xor__`, `__lshift__`, `__rshift__`, `__invert__`), unary operators (`__neg__`, `__pos__`, `__abs__`), and augmented assignment operators (`__iadd__`, `__isub__`, etc.) [1].

Each binary operator has a reflected (right-hand) variant prefixed with `r` (`__radd__`, `__rsub__`, etc.). The dispatch protocol for `a + b` is:

1. If `type(b)` is a subclass of `type(a)` and `type(b)` overrides `__radd__`, call `b.__radd__(a)` first.
2. Otherwise, call `a.__add__(b)`.
3. If the result is `NotImplemented`, call `b.__radd__(a)`.
4. If that also returns `NotImplemented`, raise `TypeError`.

The subclass-first rule (step 1) ensures that subclasses can override the behavior of operations involving their parent class. This is critical for numeric tower implementations where, for example, `float.__radd__` should take precedence over `int.__add__` when adding an int and a float [1].

### 3.7 Container Protocol

#### 3.7.1 Theory

The container protocol consists of several methods that allow objects to behave as sequences, mappings, or sets:

- **`__len__`**: Returns the number of items. Called by `len()`. Must return a non-negative integer.
- **`__getitem__`**: Enables indexing (`obj[key]`). For sequences, `key` is an integer or slice; for mappings, `key` is any hashable object.
- **`__setitem__`** and **`__delitem__`**: Enable item assignment and deletion.
- **`__iter__`**: Returns an iterator. Called by `for` loops, unpacking, and `iter()`.
- **`__next__`**: Returns the next item from an iterator. Raises `StopIteration` when exhausted.
- **`__contains__`**: Implements the `in` operator. If not defined, Python falls back to iterating through the object [1].
- **`__reversed__`**: Supports `reversed()`. Falls back to `__len__` + `__getitem__` if not defined.
- **`__missing__`**: Called by `dict.__getitem__` when a key is not found (used by `collections.defaultdict`).

#### 3.7.2 Evidence: Protocol vs Inheritance

A distinctive aspect of Python's container protocol is that it is structural rather than nominal. A class need not inherit from `collections.abc.Sequence` to be used as a sequence; it merely needs to implement `__getitem__` (and optionally `__len__`). The `for` loop will happily iterate over any object with `__iter__` (or failing that, `__getitem__` with integer indices starting from 0). This duck-typing approach is formalized through the abstract base classes in `collections.abc`, which use `__subclasshook__` to recognize structural conformance: `isinstance(obj, Iterable)` returns `True` for any object with `__iter__`, regardless of its class hierarchy [13].

## 4. Descriptors

### 4.1 Theory: The Descriptor Protocol

The descriptor protocol is the mechanism by which attribute access is customized in Python. A descriptor is any object that defines at least one of the following methods [12]:

- **`__get__(self, obj, objtype=None)`**: Called to get an attribute of the owner class (when `obj` is `None`) or an instance of the owner class.
- **`__set__(self, obj, value)`**: Called to set an attribute on an instance of the owner class.
- **`__delete__(self, obj)`**: Called to delete an attribute from an instance of the owner class.
- **`__set_name__(self, owner, name)`**: Called at class creation time (since Python 3.6, PEP 487) to inform the descriptor of the attribute name it was assigned to and the class it was assigned on [14].

The descriptor protocol is not an interface that classes opt into; it is a runtime check. If `type(obj).__dict__['attr']` defines `__get__`, it is a descriptor, and the attribute access machinery invokes the descriptor protocol.

### 4.2 Data vs Non-Data Descriptors

The distinction between data descriptors and non-data descriptors is the most important concept in understanding Python's attribute lookup:

- A **data descriptor** defines `__set__` and/or `__delete__` (in addition to `__get__`). Data descriptors take priority over instance dictionaries.
- A **non-data descriptor** defines only `__get__`. Instance dictionaries take priority over non-data descriptors.

This distinction explains several fundamental behaviors:

1. **Properties are data descriptors** (they define `__get__`, `__set__`, and `__delete__`), so they intercept attribute access even when an instance has a `__dict__` entry with the same name.
2. **Functions are non-data descriptors** (they define only `__get__`), which is why assigning to `instance.method = something` overrides the method for that instance.
3. **`classmethod` and `staticmethod` are non-data descriptors** that wrap functions and customize how they are bound.

The priority ordering in `object.__getattribute__` is [12]:

```
Data descriptor on class/bases  >  Instance __dict__  >  Non-data descriptor on class/bases
```

### 4.3 Evidence: How property, classmethod, and staticmethod Work

The official Python documentation, authored primarily by Raymond Hettinger, provides pure-Python equivalents of the built-in descriptors that reveal their implementation [12]:

#### property as a Descriptor

```python
class Property:
    def __init__(self, fget=None, fset=None, fdel=None, doc=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel
        if doc is None and fget is not None:
            doc = fget.__doc__
        self.__doc__ = doc

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.fget is None:
            raise AttributeError("unreadable attribute")
        return self.fget(obj)

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError("can't set attribute")
        self.fset(obj, value)

    def __delete__(self, obj):
        if self.fdel is None:
            raise AttributeError("can't delete attribute")
        self.fdel(obj)
```

The `if obj is None: return self` pattern is characteristic: when accessed from the class (`Class.prop`), the descriptor returns itself for introspection; when accessed from an instance (`instance.prop`), it invokes the getter.

#### staticmethod as a Descriptor

```python
class StaticMethod:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, objtype=None):
        return self.f
```

A `staticmethod` is the simplest descriptor: it returns the wrapped function unchanged, stripping away the binding behavior that would normally turn it into a bound method.

#### classmethod as a Descriptor

```python
class ClassMethod:
    def __init__(self, f):
        self.f = f

    def __get__(self, obj, cls=None):
        if cls is None:
            cls = type(obj)
        return MethodType(self.f, cls)
```

A `classmethod` binds the function to the class (not the instance), producing a bound method where the first argument is the class object. Since Python 3.9, `classmethod` can be chained with `property` -- though this was deprecated in 3.11 and removed in 3.13 [15].

### 4.4 Evidence: Functions as Descriptors

The mechanism by which plain functions become bound methods is itself the descriptor protocol. The `function` type defines `__get__`:

```python
class Function:
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return MethodType(self, obj)
```

When `instance.method` is accessed, the function's `__get__` is invoked with the instance, producing a `MethodType` object that binds the function to the instance. This is why `instance.method` and `Class.method` behave differently: the former produces a bound method (with `self` already bound), while the latter returns the raw function [12].

### 4.5 The Descriptor Lookup Chain in Detail

The full attribute lookup performed by `object.__getattribute__` can be expressed as the following algorithm (simplified from the CPython implementation in `Objects/object.c`):

```python
def object_getattribute(obj, name):
    cls = type(obj)
    # Search the MRO for a descriptor
    for base in cls.__mro__:
        if name in base.__dict__:
            descriptor = base.__dict__[name]
            descriptor_get = getattr(type(descriptor), '__get__', None)
            if (descriptor_get is not None and
                (hasattr(type(descriptor), '__set__') or
                 hasattr(type(descriptor), '__delete__'))):
                # Data descriptor -- highest priority
                return descriptor_get(descriptor, obj, cls)
            break  # Found but not a data descriptor; check instance dict first

    # Check instance __dict__
    if hasattr(obj, '__dict__') and name in obj.__dict__:
        return obj.__dict__[name]

    # Non-data descriptor or plain class variable
    if descriptor_get is not None:
        return descriptor_get(descriptor, obj, cls)

    if descriptor is not _sentinel:
        return descriptor

    raise AttributeError(name)
```

This algorithm is the result of extensive design work documented in van Rossum's "Unifying types and classes" essay. The priority ordering ensures that data descriptors (property, slots) always intercept access, preventing instances from accidentally shadowing computed attributes, while non-data descriptors (functions) can be overridden per-instance for flexibility [3].

### 4.6 __set_name__ and Descriptor Self-Awareness

Prior to Python 3.6, descriptors had no built-in way to know the name of the attribute they were assigned to. Descriptor authors had to either require explicit name passing or use metaclass machinery to inspect the class namespace. PEP 487 introduced `__set_name__(self, owner, name)`, which is called by `type.__new__` on each descriptor found in the class namespace during class creation [14].

```python
class Validated:
    def __set_name__(self, owner, name):
        self.public_name = name
        self.private_name = '_' + name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.private_name, None)

    def __set__(self, obj, value):
        self.validate(value)
        setattr(obj, self.private_name, value)
```

The `__set_name__` protocol eliminated a large class of boilerplate in descriptor-based frameworks and is one of the mechanisms by which libraries like attrs and SQLAlchemy simplify class definitions.

### 4.7 Strengths and Limitations

**Strengths:** The descriptor protocol is arguably the most powerful single mechanism in Python's data model. It unifies attribute access, method binding, property access, class methods, static methods, and slot access under a single framework. It is open to extension: any class can participate by implementing the protocol methods. The data/non-data distinction provides a principled way to control the priority of computed vs stored attributes.

**Limitations:** The implicit nature of the protocol makes it difficult to debug. When `instance.attr` returns an unexpected value, determining which descriptor in the MRO was invoked requires understanding the full lookup chain. Performance overhead from descriptor invocation is measurable: a property access is approximately 2-3x slower than a direct `__dict__` lookup, though this is rarely significant in practice. The interaction between descriptors and `__slots__` introduces additional complexity (see Section 8).

## 5. Metaclasses

### 5.1 Theory: type as the Default Metaclass

In Python, classes are objects. The class of a class is called its *metaclass*. The default metaclass is `type`: `type(int)` returns `<class 'type'>`, and `type(type)` returns `<class 'type'>` -- `type` is its own metaclass, forming the circular base of the type hierarchy. Alongside this, `type` is a subclass of `object`, and `object` is an instance of `type`, creating the fundamental bootstrap cycle of Python's object system [16].

A metaclass controls how a class is created, initialized, and behaves as an object. Since classes are instances of their metaclass, the metaclass's `__call__` method is invoked when the class is called (i.e., when instances are created). The metaclass's `__new__` and `__init__` control the creation and initialization of the class object itself.

### 5.2 __new__ vs __init__ in Metaclasses

In a metaclass, `__new__` and `__init__` serve distinct roles:

- **`Meta.__new__(mcs, name, bases, namespace, **kwargs)`**: Called to create the class object. This is where the metaclass can modify the namespace (add, remove, or transform methods), alter the bases, or even return a completely different object. Most metaclass logic belongs in `__new__` because the class does not yet exist, so transformations are applied before the class is finalized [17].

- **`Meta.__init__(cls, name, bases, namespace, **kwargs)`**: Called after the class object is created. The class object is already a fully formed type; `__init__` can perform additional setup but cannot change the class's bases or the namespace in a way that affects the type's internal slots (those were fixed in `__new__`).

```python
class RegistryMeta(type):
    _registry = {}

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, namespace)
        if name != 'Base':
            mcs._registry[name] = cls
        return cls

class Base(metaclass=RegistryMeta):
    pass

class Plugin(Base):       # Automatically registered
    pass
```

### 5.3 __prepare__: Namespace Customization

PEP 3115 introduced `__prepare__`, a classmethod on the metaclass that returns the mapping object to be used as the class namespace during body execution [18]. The default is an empty `dict`, but a metaclass can return any mapping-like object:

```python
class OrderedMeta(type):
    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        return OrderedDict()

    def __new__(mcs, name, bases, namespace, **kwargs):
        cls = super().__new__(mcs, name, bases, dict(namespace))
        cls._field_order = list(namespace.keys())
        return cls
```

Before Python 3.7, when `dict` did not guarantee insertion order, `__prepare__` returning an `OrderedDict` was the standard technique for preserving the order of class body definitions. Since CPython 3.7 guaranteed `dict` ordering (and Python 3.7+ made this part of the language specification), this particular use case has become unnecessary. However, `__prepare__` remains valuable for validation namespaces (that reject duplicate definitions), auto-registering namespaces, or namespaces that transform values on assignment [18].

### 5.4 __init_subclass__: The Lightweight Alternative

PEP 487 (Python 3.6) introduced `__init_subclass__` as a simpler alternative to metaclasses for the common case of customizing subclass creation [14]. When a class is subclassed, `Base.__init_subclass__` is called with the new subclass as `cls`:

```python
class PluginBase:
    _plugins = {}

    def __init_subclass__(cls, plugin_name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if plugin_name is not None:
            PluginBase._plugins[plugin_name] = cls

class MyPlugin(PluginBase, plugin_name="my_plugin"):
    pass
```

The `**kwargs` forwarding pattern with `super().__init_subclass__(**kwargs)` is essential for cooperative multiple inheritance: each class in the MRO consumes the keyword arguments it recognizes and passes the rest up the chain. Failure to include `super().__init_subclass__(**kwargs)` breaks the cooperative chain and will raise `TypeError` if any unprocessed keyword arguments remain [14].

`__init_subclass__` was explicitly designed to replace the majority of metaclass use cases. The PEP motivation states: "Metaclasses are a powerful tool, but most uses of metaclasses can be replaced with much simpler mechanisms" [14]. The key advantages over metaclasses are: (1) no metaclass conflict resolution needed, (2) the customization is expressed in the base class, which is conceptually simpler, and (3) `super()` works correctly for cooperative use.

### 5.5 Metaclass Resolution Order

When a class definition specifies bases, Python must determine which metaclass to use. The algorithm (implemented in `_calculate_meta()` in `Objects/typeobject.c`) is [1]:

1. If `metaclass` is explicitly given via `class Foo(metaclass=M)`, use `M`.
2. Otherwise, if there are bases, the metaclass is the most derived metaclass among all bases' metaclasses.
3. If no bases are given, the metaclass is `type`.

Step 2 requires that the chosen metaclass is a subclass of every base's metaclass. If no such metaclass exists, Python raises `TypeError: metaclass conflict`. This conflict arises when bases use unrelated metaclasses:

```python
class MetaA(type): pass
class MetaB(type): pass
class A(metaclass=MetaA): pass
class B(metaclass=MetaB): pass
class C(A, B): pass  # TypeError: metaclass conflict
```

The solution requires creating a combined metaclass: `class MetaC(MetaA, MetaB): pass`. This limitation is a primary motivation for preferring `__init_subclass__` over metaclasses when possible.

### 5.6 abc.ABCMeta

The `abc` module provides `ABCMeta`, a metaclass that supports abstract base classes. `ABCMeta` maintains a `__abstractmethods__` frozenset on each class, populated by methods decorated with `@abstractmethod`. A class with non-empty `__abstractmethods__` cannot be instantiated. `ABCMeta` also implements `__instancecheck__` and `__subclasscheck__` to support virtual subclassing via the `register()` method, enabling structural typing through `__subclasshook__` [19].

Since PEP 3119 (Python 3.0), the ABCs in `collections.abc` use `__subclasshook__` to recognize objects that implement the right methods without requiring inheritance:

```python
from collections.abc import Sized

class Bag:
    def __len__(self):
        return 42

isinstance(Bag(), Sized)  # True -- Bag implements __len__
```

This mechanism bridges Python's duck-typing tradition with explicit interface checking, providing "virtual inheritance" without metaclass conflicts.

### 5.7 Strengths and Limitations

**Strengths:** Metaclasses provide complete control over class creation: they can validate class definitions, automatically register classes, transform methods, enforce coding conventions, and implement patterns impossible through other means (e.g., singleton enforcement at the class level, transparent ORM mapping). The `__prepare__` hook enables sophisticated namespace manipulation.

**Limitations:** Metaclasses are frequently cited as one of Python's most confusing features. Tim Peters's famous aphorism -- "Metaclasses are deeper magic than 99% of users should ever worry about" -- reflects the community consensus [20]. The metaclass conflict problem makes metaclasses composable only through explicit multiple inheritance of metaclasses themselves. Performance overhead at class creation time is measurable but occurs only once per class definition. The introduction of `__init_subclass__` in Python 3.6 has diminished the practical need for metaclasses in most applications.

## 6. Method Resolution Order

### 6.1 Theory: C3 Linearization

Python uses the C3 linearization algorithm to compute the Method Resolution Order (MRO), which determines the order in which base classes are searched when looking up a method. C3 was originally designed for the Dylan programming language by Barrett, Cassels, Haahr, Moon, Playford, and Withington (1996) and was adopted by Python 2.3 after Michele Simionato's influential analysis [21].

The C3 algorithm computes the linearization `L[C]` of a class `C` with bases `B1, B2, ..., BN` as:

```
L[C] = C + merge(L[B1], L[B2], ..., L[BN], [B1, B2, ..., BN])
```

The `merge` operation selects the first element from the leftmost list that does not appear in the tail of any other list (a "good head"), appends it to the result, removes it from all lists, and repeats until all lists are empty or no good head exists (in which case the hierarchy is rejected as inconsistent).

### 6.2 Properties of C3

C3 linearization satisfies three critical properties [21]:

1. **Local precedence order**: The order of direct bases specified in the class definition is preserved. If `class C(A, B)`, then `A` precedes `B` in `L[C]`.

2. **Monotonicity**: If class `C1` precedes `C2` in the linearization of `C`, then `C1` precedes `C2` in the linearization of any subclass of `C`. Monotonicity is violated by the depth-first, left-to-right algorithm used in old-style Python classes, which produced pathological behavior with diamond inheritance.

3. **Extended precedence graph consistency**: The linearization is consistent with the extended precedence graph, which encodes both inheritance and local ordering constraints.

### 6.3 Evidence: Diamond Inheritance

The classic diamond inheritance problem illustrates C3's behavior:

```python
class A:
    def method(self):
        return 'A'

class B(A):
    def method(self):
        return 'B'

class C(A):
    def method(self):
        return 'C'

class D(B, C):
    pass

D.__mro__  # (D, B, C, A, object)
D().method()  # 'B'
```

Without C3, a naive depth-first search would produce `(D, B, A, object, C, A, object)`, placing `A` before `C` and causing `D().method()` to potentially skip `C`'s override of `A.method`. C3 ensures that `C` appears before `A` in the MRO, respecting the fact that `C` is a direct specialization of `A`.

### 6.4 super() Semantics

The `super()` function returns a proxy object that delegates method calls to the next class in the MRO, not necessarily the parent class. This is the foundation of cooperative multiple inheritance [22].

```python
class A:
    def method(self):
        print('A')

class B(A):
    def method(self):
        print('B')
        super().method()

class C(A):
    def method(self):
        print('C')
        super().method()

class D(B, C):
    def method(self):
        print('D')
        super().method()

D().method()  # Prints: D, B, C, A
```

The zero-argument `super()` form (PEP 3135) is implemented through a compiler-level mechanism: when the compiler encounters `super()` in a method body, it creates an implicit `__class__` cell variable that references the class being defined. At runtime, `super()` retrieves this cell to determine the "current class" and the first argument of the enclosing method as the instance [23]. This mechanism has a subtle implication: `super()` does not work with functions that are not defined as methods within a class body (e.g., dynamically assigned functions), and aliasing `super` to another name before calling it can fail because the compiler's detection is based on the literal name `super`.

### 6.5 Cooperative Multiple Inheritance Patterns

For cooperative multiple inheritance to work correctly, all classes in the hierarchy must follow the cooperative protocol [22]:

1. Every method that participates in cooperative dispatch must call `super().method()`.
2. The root class (typically `object` or a dedicated base) must provide a terminal implementation that does *not* call `super()`.
3. Method signatures must be compatible across the hierarchy. The common pattern uses `*args, **kwargs` to forward unknown arguments.

Raymond Hettinger's influential "Python's super() considered super!" article demonstrated that cooperative multiple inheritance enables powerful mixin patterns and eliminates the need for the "call-next-method" functionality of CLOS, using Python's simpler `super()` mechanism [22].

### 6.6 Strengths and Limitations

**Strengths:** C3 linearization provides a deterministic, predictable, and mathematically well-founded resolution order. The monotonicity property prevents surprising behavior changes when subclassing. The algorithm rejects inconsistent hierarchies at class creation time rather than producing undefined behavior. `super()` enables true cooperative behavior without hardcoding parent class names.

**Limitations:** C3 can reject some class hierarchies that a programmer might consider valid but that violate the monotonicity or ordering constraints. Understanding the MRO for complex hierarchies requires running the algorithm mentally or inspecting `__mro__`. The cooperative `super()` pattern requires all classes to follow the protocol -- a single class that fails to call `super()` breaks the chain, and debugging this is difficult because the symptom (a missing method call) is separated from the cause (the non-cooperative class).

## 7. Decorators

### 7.1 Theory: Syntactic Metaprogramming

Decorators are syntactic sugar for a higher-order function pattern. The decorator syntax:

```python
@decorator
def func():
    pass
```

is equivalent to:

```python
def func():
    pass
func = decorator(func)
```

For class decorators, the same desugaring applies: `@decorator class C: pass` becomes `C = decorator(C)` [1]. Decorators were introduced in Python 2.4 (PEP 318) for functions and Python 3.0 (PEP 3129) for classes.

The key insight is that decorators are not a new mechanism -- they are a syntactic convenience for the existing pattern of wrapping functions and classes. Any callable that accepts a function/class and returns a function/class can be used as a decorator.

### 7.2 Function Decorators

#### 7.2.1 The Wrapper Pattern

The canonical function decorator creates a wrapper that executes code before and/or after the wrapped function:

```python
import functools

def timing(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper
```

#### 7.2.2 functools.wraps

The `functools.wraps` decorator (which is itself a decorator factory) copies metadata from the wrapped function to the wrapper: `__name__`, `__qualname__`, `__module__`, `__doc__`, `__dict__`, and `__wrapped__`. Without `wraps`, the wrapper's `__name__` would be `'wrapper'`, its docstring would be `None`, and introspection tools (debuggers, documentation generators, `help()`) would report incorrect information [10].

The `__wrapped__` attribute, set by `functools.wraps`, provides access to the original unwrapped function, which is critical for testing (to test the underlying function without decorator side effects) and for chaining introspection through multiple decorator layers.

#### 7.2.3 Performance Considerations

Each decorator layer adds one function call per invocation. For decorators implemented as closures, this overhead is typically 50-150 nanoseconds per call in CPython. For decorator classes (which use the descriptor protocol for method binding), the overhead can be higher due to the `__get__` call on each access [24]. Graham Dumpleton's analysis of decorator overhead demonstrated that naive decorator implementations can incur 2-3x overhead for method calls due to incorrect handling of the descriptor protocol, motivating the development of the `wrapt` library [24].

### 7.3 Decorator Factories (Parametrized Decorators)

A decorator factory is a function that accepts configuration arguments and returns a decorator. This introduces a three-layer nesting:

```python
def retry(max_attempts=3, exceptions=(Exception,)):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts - 1:
                        raise
        return wrapper
    return decorator

@retry(max_attempts=5, exceptions=(ConnectionError,))
def fetch_data():
    pass
```

The three-layer structure is required because the decorator syntax `@expr` evaluates `expr` and calls the result with the decorated function. `@retry(max_attempts=5)` first calls `retry(max_attempts=5)`, which returns the actual decorator, which is then called with `fetch_data`.

### 7.4 Class Decorators

Class decorators receive the class as their argument and return a (typically modified) class. They are strictly less powerful than metaclasses -- they cannot intercept class body execution or customize the namespace -- but they compose without metaclass conflicts and are simpler to understand [25].

```python
def add_repr(cls):
    def __repr__(self):
        attrs = ', '.join(f'{k}={v!r}' for k, v in self.__dict__.items())
        return f'{cls.__name__}({attrs})'
    cls.__repr__ = __repr__
    return cls
```

Class decorators are the mechanism used by `@dataclass`, `@attrs.define`, and many framework decorators. They operate *after* the class is fully created, which means they can inspect the class's `__dict__`, `__mro__`, annotations, and other attributes.

### 7.5 Decorator Stacking

When multiple decorators are applied, they are evaluated bottom-up (closest to the function first):

```python
@decorator_a
@decorator_b
def func():
    pass
# Equivalent to: func = decorator_a(decorator_b(func))
```

The evaluation order matters when decorators have side effects or when the order of wrapping affects behavior. For example, stacking `@staticmethod` above a custom decorator will fail because `@staticmethod` returns a descriptor object that is not callable in the same way as a function.

### 7.6 Strengths and Limitations

**Strengths:** Decorators provide a clean, readable syntax for cross-cutting concerns (logging, caching, authentication, retry logic, registration). They compose naturally through stacking. They work with both functions and classes. The pattern is simple enough to be understood by intermediate Python programmers.

**Limitations:** Decorators obscure the original function signature (though `functools.wraps` preserves metadata). Deep stacking can make debugging difficult, as stack traces show wrapper functions rather than the original. Decorator factories require the unintuitive three-layer nesting. Parametrized decorators that work both with and without parentheses (`@decorator` and `@decorator()`) require additional boilerplate.

## 8. __slots__

### 8.1 Theory: Memory Layout Optimization

By default, Python stores instance attributes in a per-instance `__dict__` dictionary. The `__slots__` class variable replaces this dictionary with a fixed-size array of slot descriptors, eliminating the per-instance dictionary overhead [1].

```python
class Point:
    __slots__ = ('x', 'y')

    def __init__(self, x, y):
        self.x = x
        self.y = y
```

When `__slots__` is defined, the class creates a *member descriptor* (a data descriptor) for each slot name. These descriptors store attribute values directly in the instance's C-level memory layout at fixed offsets, rather than through dictionary lookup.

### 8.2 Evidence: Memory and Performance

Memory savings from `__slots__` are substantial for classes with few attributes and many instances:

| Configuration | Memory per instance (64-bit) | Notes |
|---|---|---|
| Regular class (2 attrs) | ~152 bytes | PyObject header + `__dict__` (~104 bytes) + dict entries |
| `__slots__` class (2 attrs) | ~56 bytes | PyObject header + 2 slot pointers |
| dataclass with `slots=True` | ~56 bytes | Same as manual `__slots__` |

Benchmarks consistently show 40-70% memory reduction for small objects. At scale, the effect is dramatic: 10 million instances of a two-attribute dataclass consume approximately 612 MB without slots versus 77 MB with `slots=True` -- an 8x reduction [26].

Performance improvements are more modest. Instance creation with `__slots__` is approximately 10-23% faster (the allocator need not create a dictionary). Attribute access is approximately 10-20% faster (array offset vs dictionary lookup). In absolute terms, these differences amount to tens of nanoseconds per operation [26].

### 8.3 Interaction with Inheritance

`__slots__` and inheritance have several interaction rules:

1. **Without `__slots__` in subclass**: If a class with `__slots__` is subclassed and the subclass does not define `__slots__`, the subclass regains a `__dict__`, negating the memory benefit for attributes defined in the subclass (though slotted parent attributes remain slotted).

2. **Duplicate slots**: If both parent and child define the same slot name, the parent's slot descriptor is shadowed but the memory is still allocated (wasted). Python issues no warning for this.

3. **Multiple inheritance**: Multiple inheritance with `__slots__` is restricted. If two base classes define non-empty `__slots__` and both use a non-trivial C-level layout, a `TypeError` is raised. The practical rule is: at most one base in a multiple inheritance hierarchy may define non-empty `__slots__` [1].

### 8.4 __dict__ Suppression and Weakref Interaction

When `__slots__` is defined, the instance has no `__dict__` by default. To allow dynamic attributes alongside slots, include `'__dict__'` in `__slots__`. Similarly, slotted objects do not support weak references by default; to enable them, include `'__weakref__'` in `__slots__` [1].

```python
class Flexible:
    __slots__ = ('x', 'y', '__dict__', '__weakref__')
```

### 8.5 Slots as Descriptors

Each slot is implemented as a *member descriptor* -- a data descriptor defined in C (type `PyMemberDescrObject`) that reads and writes to a fixed offset in the instance's memory. Because member descriptors are data descriptors, they take priority over instance `__dict__` entries (if `__dict__` is also present), following the standard descriptor priority rules [12].

### 8.6 Strengths and Limitations

**Strengths:** `__slots__` provides substantial memory savings for classes with many instances and few attributes. Attribute access is slightly faster. Slots enforce a fixed set of attribute names, preventing typos from silently creating new attributes. Slots are compatible with `dataclasses(slots=True)` since Python 3.10.

**Limitations:** Loss of dynamic attribute assignment (unless `__dict__` is included). Complicated interaction with inheritance, particularly multiple inheritance. Cannot be used with variable-length built-in types (e.g., `str`, `tuple`). Pickling requires extra care (must define `__getstate__`/`__setstate__`). Adding or removing slots after class creation requires recreating the class.

## 9. Class Creation Machinery

### 9.1 Three-Argument type()

The `type()` builtin serves double duty: with one argument, it returns the type of an object; with three arguments, it creates a new class [1]:

```python
# These two forms are equivalent:
class MyClass(Base):
    x = 10
    def method(self):
        return self.x

MyClass = type('MyClass', (Base,), {'x': 10, 'method': lambda self: self.x})
```

The three-argument form `type(name, bases, namespace)` is the fundamental class creation operation. The `class` statement is syntactic sugar that:

1. Determines the metaclass (from the `metaclass` keyword or the bases' metaclasses).
2. Calls `metaclass.__prepare__(name, bases, **kwargs)` to obtain the namespace.
3. Executes the class body as a function with the namespace as its local scope.
4. Calls `metaclass(name, bases, namespace, **kwargs)` to create the class.

### 9.2 __build_class__ and Class Body Execution

The actual implementation uses the `__build_class__` builtin (since Python 3.0), which the compiler generates as the first operation for any `class` statement. `__build_class__` receives the class body as a zero-argument function, the class name, the bases, and any keyword arguments. It orchestrates the full class creation protocol [7]:

1. Determine the metaclass via metaclass resolution.
2. Call `meta.__prepare__(name, bases, **kwargs)` to get the namespace.
3. Call the class body function with the namespace as locals.
4. Call `meta(name, bases, namespace, **kwargs)` to create the class object.

The class body is literally compiled as a function and called. This is why class bodies have their own scope (assignments create class attributes, not local variables in the enclosing function), and why expressions in the class body execute at class definition time.

### 9.3 __class_cell__ and Zero-Argument super()

PEP 3135 introduced the zero-argument `super()` form, which requires the compiler to implicitly make the enclosing class available inside methods [23]. The implementation uses the `__class__` cell variable:

1. The compiler detects uses of `super` (or `__class__`) in method bodies.
2. It creates a cell variable named `__class__` in the method's closure.
3. During class creation, `type.__new__` fills this cell with the newly created class object.
4. At runtime, `super()` reads `__class__` from the cell and the first argument from the frame to construct the `super` proxy.

If a metaclass's `__new__` does not return the result of `type.__new__` (or does not properly propagate the `__class__` cell), zero-argument `super()` will fail with a `RuntimeError: __class__ cell not found`. This is a rare but confusing failure mode that arises with certain metaclass patterns [23].

### 9.4 __qualname__

PEP 3155 introduced `__qualname__` (qualified name) to provide a dotted path from the module scope to the object [27]. For top-level definitions, `__qualname__` equals `__name__`. For nested definitions:

```python
class Outer:
    class Inner:
        def method(self):
            pass

Outer.Inner.__qualname__           # 'Outer.Inner'
Outer.Inner.method.__qualname__    # 'Outer.Inner.method'
```

The `__qualname__` attribute is set during class and function creation and is critical for pickling, debugging, and documentation. It allows tools to reconstruct the nesting context of a definition without maintaining a full scope chain.

### 9.5 __set_name__ in the Class Creation Sequence

When `type.__new__` creates a class, it iterates over the namespace and calls `descriptor.__set_name__(cls, name)` for each value that defines `__set_name__`. This happens *after* the class object is created but *before* `__init_subclass__` is called on the base class, ensuring that descriptors are fully initialized when `__init_subclass__` runs [14].

The complete class creation sequence is:

1. `meta.__prepare__(name, bases, **kwargs)` -- create namespace.
2. Execute class body in namespace.
3. `meta.__new__(mcs, name, bases, namespace, **kwargs)` -- create class object.
4. For each descriptor in namespace: `descriptor.__set_name__(cls, name)`.
5. `base.__init_subclass__(cls, **kwargs)` -- notify base class.
6. `meta.__init__(cls, name, bases, namespace, **kwargs)` -- initialize metaclass.

### 9.6 Strengths and Limitations

**Strengths:** The class creation machinery is fully transparent and overridable at every step. Three-argument `type()` enables programmatic class creation without syntactic overhead. `__build_class__` is a builtin that can be monkey-patched (though this is almost never advisable). The `__set_name__` and `__init_subclass__` hooks provide clean extension points that reduce the need for metaclasses.

**Limitations:** The multi-step creation protocol has many subtle ordering dependencies. The `__class_cell__` mechanism for `super()` is an implicit compiler-metaclass contract that can break with non-standard metaclasses. Understanding the full creation sequence requires knowledge of both the compiler and the runtime.

## 10. Modern Alternatives: dataclasses, attrs, and pydantic

### 10.1 Theory: Code Generation on the Data Model

The modern Python ecosystem has converged on a pattern: class decorators or metaclasses inspect type annotations and generate dunder methods (`__init__`, `__repr__`, `__eq__`, `__hash__`, `__lt__`, etc.) automatically. This approach leverages the data model as an implementation target while providing a declarative API for the programmer.

### 10.2 dataclasses (PEP 557)

#### 10.2.1 Implementation

The `@dataclass` decorator (Python 3.7, PEP 557) inspects the class's type annotations and generates methods by constructing source code as strings and calling `exec()` to compile them [28]:

```python
@dataclass
class Point:
    x: float
    y: float
```

The decorator generates `__init__`, `__repr__`, and `__eq__` by default (controlled by parameters `init`, `repr`, `eq`, `order`, `unsafe_hash`, `frozen`). Since Python 3.10, `slots=True` generates a new class with `__slots__` matching the field names. Since Python 3.10, `match_args=True` generates `__match_args__` for structural pattern matching.

#### 10.2.2 How It Uses the Data Model

- **Field discovery**: Inspects `cls.__annotations__` (and MRO for inherited annotations).
- **Method generation**: Constructs Python source strings and `exec()`s them in a namespace containing the field defaults. This compilation approach ensures the generated methods have the same performance as hand-written equivalents.
- **`__post_init__`**: If defined, is called at the end of the generated `__init__`, providing a hook for validation or derived attribute computation.
- **`__init_subclass__` interaction**: `@dataclass` does not use metaclasses, so it composes freely with metaclass-using libraries.
- **Frozen classes**: Implement `__setattr__` and `__delattr__` that raise `FrozenInstanceError`, using the data model's attribute interception to enforce immutability.
- **slots=True**: Creates a new class (not a modification of the original) with `__slots__`, because `__slots__` must be present at class creation time. The original class is replaced by the new one.

#### 10.2.3 Strengths and Limitations

**Strengths:** Standard library, zero dependencies. Composes with inheritance, descriptors, and metaclasses. `slots=True` and `frozen=True` provide performance and safety. `field()` offers fine-grained control over defaults, repr, hash, and comparison participation.

**Limitations:** No runtime validation (type annotations are not enforced). No serialization support. The `exec()`-based code generation makes source-level debugging of generated methods challenging. `frozen=True` incurs a per-attribute-access overhead because every `__setattr__` call invokes the check.

### 10.3 attrs

#### 10.3.1 Implementation

The attrs library (since 2015, predating dataclasses and inspiring them) provides `@attrs.define` (modern API) and `@attr.s` (classic API). Like dataclasses, attrs generates dunder methods, but with a more comprehensive feature set [29]:

- **Validators**: `attrs.validators.instance_of(int)` runs at `__init__` time.
- **Converters**: Automatically transform input values during initialization.
- **Factory defaults**: `attrs.Factory(list)` creates a new list per instance.
- **Slot classes by default**: `@attrs.define` generates slotted classes by default.
- **`__attrs_attrs__`**: The only introspection attribute added to the class.

#### 10.3.2 How It Uses the Data Model

attrs uses the same `exec()` code generation approach as dataclasses but with additional sophistication:

- **Slot class creation**: Like `dataclasses(slots=True)`, attrs creates a new class with `__slots__`. It goes further by automatically copying class methods, adjusting `__qualname__`, and handling `__weakref__`.
- **Frozen classes**: Two mechanisms: `__setattr__`/`__delattr__` override (like dataclasses) or a slots-based approach that uses C-level immutability.
- **Hash caching**: The `cache_hash=True` option stores the hash value as a slot, computing it once on first access.
- **`__set_name__`**: attrs descriptors use `__set_name__` when the field is a descriptor.

### 10.4 pydantic

#### 10.4.1 Implementation

Pydantic (v2) takes a fundamentally different approach: it uses a metaclass (`ModelMetaclass`) for model construction and a Rust-based validation core (`pydantic-core`) for runtime type checking and coercion [30].

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str
```

#### 10.4.2 How It Uses the Data Model

- **ModelMetaclass**: Inherits from `type` and overrides `__new__` to intercept class creation. It collects annotations, builds a validation schema, and compiles it to a Rust-backed validator.
- **`__init__`**: Generated to accept keyword arguments, pass them through the Rust validator, and set validated values. Pydantic's `__init__` performs type coercion (e.g., `"42"` -> `42` for `int` fields).
- **`__repr__` and `__str__`**: Generated from model fields.
- **`__eq__`**: Compares model fields (not identity).
- **Descriptor-like behavior**: Pydantic model fields behave like descriptors in that assignment triggers validation, but the mechanism is via `__setattr__` override rather than separate descriptor objects.
- **`model_validator`** and **`field_validator`**: Use decorators that are collected by the metaclass during class creation.
- **`__init_subclass__`**: Used for schema inheritance and validator collection.

#### 10.4.3 Strengths and Limitations

**Strengths:** Runtime type validation and coercion. JSON serialization/deserialization. Rust-powered validation is fast (10-50x faster than pure Python validation). OpenAPI schema generation. Extensive ecosystem integration (FastAPI, SQLModel).

**Limitations:** Metaclass-based, so metaclass conflicts are possible. Runtime validation overhead for every instance creation (intentional, but unsuitable for hot paths with trusted data). Complex internal architecture. The Rust dependency complicates debugging of validation errors. Model instances are heavier than plain dataclass instances.

## 11. Comparative Synthesis

| Feature | dataclasses | attrs | pydantic v2 | Manual dunder | Metaclass |
|---|---|---|---|---|---|
| **Mechanism** | Class decorator + exec() | Class decorator + exec() | Metaclass + Rust core | Manual code | type subclass |
| **Validation** | None (post_init only) | Validators, converters | Full type coercion | Manual | Manual |
| **Slots support** | slots=True (3.10+) | Default in @define | slots in ConfigDict | Manual __slots__ | Manual |
| **Frozen/immutable** | frozen=True | frozen=True | frozen=True in model_config | __setattr__ override | __setattr__ override |
| **Inheritance** | Works, some edge cases | Works well | Works, schema inheritance | Full control | Full control |
| **Metaclass conflict** | None (decorator) | None (decorator) | Possible (uses metaclass) | N/A | Inherent risk |
| **Serialization** | None built-in | None built-in | JSON, dict, custom | Manual | Manual |
| **Performance (creation)** | Fast | Fast | Moderate (validation) | Fastest | Fast |
| **Memory (slotted)** | ~56 bytes/instance | ~56 bytes/instance | ~200+ bytes/instance | ~56 bytes/instance | Depends |
| **Descriptor support** | Partial | Good | Via model fields | Full | Full |
| **Learning curve** | Low | Low-moderate | Moderate | Low (per method) | High |
| **Dependencies** | stdlib | attrs package | pydantic + pydantic-core | None | None |

### 11.1 Decision Framework

The choice among these approaches depends on the use case:

- **Data transfer objects with no validation**: dataclasses (stdlib, simple, fast).
- **Domain objects with rich invariants**: attrs (validators, converters, good defaults).
- **API boundaries with untrusted input**: pydantic (type coercion, serialization, schema generation).
- **Framework internals requiring deep control**: metaclasses or manual dunder methods.
- **Memory-constrained applications**: `__slots__` (via any mechanism) + minimal object overhead.
- **Maximum composability**: Prefer `__init_subclass__` and class decorators over metaclasses to avoid metaclass conflicts.

## 12. Open Problems

### 12.1 Protocol Formalization

Python's data model is documented in prose, not in a formal specification. The interactions between descriptors, metaclasses, MRO, and `__slots__` are defined by CPython's implementation rather than by algebraic laws. A formal metaobject protocol specification -- analogous to AMOP for CLOS -- would enable static analysis tools to reason about custom data model implementations and detect protocol violations at type-check time.

### 12.2 Performance of the Descriptor Protocol

While descriptors are elegant, each attribute access through a descriptor involves multiple function calls (type lookup, `__get__` invocation, potential `MethodType` creation for methods). Projects like Cython and mypyc address this through compilation, but the standard CPython interpreter pays the full cost. The specializing adaptive interpreter introduced in Python 3.11 (PEP 659) optimizes common cases (e.g., `LOAD_ATTR_SLOT` for slotted attributes, `LOAD_ATTR_METHOD` for method calls), but custom descriptors still incur the generic path overhead [31].

### 12.3 Metaclass Composability

The metaclass conflict problem remains unsolved at the language level. While `__init_subclass__` eliminates many use cases for metaclasses, some (ORM mapping, abstract base classes, protocol enforcement) still require them. Automatic metaclass combination (as explored in some Smalltalk implementations) has been discussed but not adopted, partly because the correct combination semantics are use-case-dependent [17].

### 12.4 Type Checker Integration

Type checkers (mypy, pyright, pytype) must model the data model's runtime behavior statically. This is particularly challenging for:

- Descriptors whose `__get__` return type depends on whether `obj` is `None` (class access vs instance access).
- Metaclasses that inject attributes not visible in the class body.
- `__init_subclass__` hooks that modify the class after creation.
- Dynamic `__getattr__` implementations.

PEP 681 (`@dataclass_transform`) partially addressed this for dataclass-like libraries, but a general solution for descriptor and metaclass typing remains elusive [32].

### 12.5 __slots__ and Dynamic Features

The mutual exclusion between `__slots__` and dynamic attribute assignment is a fundamental tension. Modern Python trends toward slots (attrs defaults to `slots=True`, dataclasses gained `slots=True` in 3.10), but this conflicts with patterns that rely on `__dict__` (monkey-patching, runtime method injection, some testing patterns). A more granular mechanism -- perhaps allowing slots for declared attributes while permitting a fallback dictionary for extras -- has been discussed but not proposed as a PEP.

### 12.6 Descriptor Debugging Tooling

When an attribute access produces an unexpected result, determining which descriptor in the MRO was invoked requires manual inspection of `type(obj).__mro__` and each class's `__dict__`. No standard library tool provides a "descriptor resolution trace" analogous to SQL's `EXPLAIN` or make's `--debug`. Such a tool would significantly improve the debuggability of complex class hierarchies.

## 13. Conclusion

Python's data model constitutes a comprehensive metaobject protocol that exposes virtually every aspect of object behavior to programmer customization. The descriptor protocol provides a unified mechanism for attribute access that underlies properties, methods, class methods, static methods, and slots. The metaclass system enables complete control over class creation, while C3 linearization provides a principled method resolution order for multiple inheritance. Decorators offer syntactic convenience for the common pattern of wrapping functions and classes. Modern libraries -- dataclasses, attrs, and pydantic -- demonstrate the data model's power as an implementation substrate, generating sophisticated class infrastructure from declarative annotations.

The data model's design philosophy reflects Python's broader commitment to transparency and introspection: rather than hiding the object system's implementation behind compiler magic, Python exposes it as a collection of protocols that any class can implement. This transparency has a cost in complexity -- the interactions between descriptors, metaclasses, MRO, slots, and class creation hooks form a web of dependencies that requires deep understanding to navigate -- but it provides a level of metaprogramming flexibility that few languages match.

The trajectory of the ecosystem suggests a gradual shift from explicit dunder method implementation toward declarative class construction (annotations + decorators/metaclasses that generate dunder methods), with the data model serving as the stable, well-understood compilation target. The key open challenges are formalizing the protocol specification, improving type checker integration, resolving the metaclass composability problem, and providing better debugging tools for the descriptor lookup chain.

## References

[1] Python Software Foundation. "Data Model." *Python Language Reference*, Python 3.14. https://docs.python.org/3/reference/datamodel.html

[2] G. van Rossum. "The Inside Story on New-Style Classes." *The History of Python*, 2010. http://python-history.blogspot.com/2010/06/inside-story-on-new-style-classes.html

[3] G. van Rossum. "Unifying types and classes in Python 2.2." 2002. https://docs.python.org/3/howto/descriptor.html (Descriptor HowTo Guide contains the historical context)

[4] CPython source. `Objects/typeobject.c`. https://github.com/python/cpython/blob/main/Objects/typeobject.c

[5] G. Kiczales, J. des Rivieres, and D. G. Bobrow. *The Art of the Metaobject Protocol*. MIT Press, 1991.

[6] CPython source. `Include/object.h` and `Include/cpython/object.h`. https://github.com/python/cpython/blob/main/Include/object.h

[7] CPython source. `Python/bltinmodule.c` (`__build_class__` implementation). https://github.com/python/cpython/blob/main/Python/bltinmodule.c

[8] Python Software Foundation. "Python Class Constructors." *Real Python*. https://realpython.com/python-class-constructor/

[9] R. Hettinger. "Python's super() considered super!" 2011. https://rhettinger.wordpress.com/2011/05/26/super-considered-super/

[10] Python Software Foundation. "functools -- Higher-order functions and operations on callable objects." https://docs.python.org/3/library/functools.html

[11] Python Software Foundation. `Objects/dictobject.c`. CPython dict implementation. https://github.com/python/cpython/blob/main/Objects/dictobject.c

[12] R. Hettinger. "Descriptor HowTo Guide." *Python Documentation*. https://docs.python.org/3/howto/descriptor.html

[13] Python Software Foundation. "collections.abc -- Abstract Base Classes for Containers." https://docs.python.org/3/library/collections.abc.html

[14] M. Teichmann. "PEP 487 -- Simpler customisation of class creation." 2015. https://peps.python.org/pep-0487/

[15] Python Software Foundation. "Built-in Functions: classmethod." https://docs.python.org/3/library/functions.html#classmethod

[16] I. M. C. Ro. "Understanding Python metaclasses." 2015. https://blog.ionelmc.ro/2015/02/09/understanding-python-metaclasses/

[17] Python Software Foundation. "Python Metaclasses." *Real Python*. https://realpython.com/python-metaclasses/

[18] N. Coghlan. "PEP 3115 -- Metaclasses in Python 3000." 2007. https://peps.python.org/pep-3115/

[19] Python Software Foundation. "abc -- Abstract Base Classes." https://docs.python.org/3/library/abc.html

[20] T. Peters. Quoted in Python documentation and community discussions regarding metaclass complexity.

[21] M. Simionato. "The Python 2.3 Method Resolution Order." 2003. https://www.python.org/download/releases/2.3/mro/

[22] R. Hettinger. "Python's super() considered super!" *Deep Thoughts by Raymond Hettinger*, 2011. https://rhettinger.wordpress.com/2011/05/26/super-considered-super/

[23] T. Delaney. "PEP 3135 -- New Super." 2007. https://peps.python.org/pep-3135/

[24] G. Dumpleton. "Performance overhead when applying decorators to methods." 2014. https://grahamdumpleton.me/posts/2014/02/performance-overhead-when-applying/

[25] J. Aycock. "PEP 3129 -- Class Decorators." 2007. https://peps.python.org/pep-3129/

[26] "Python slots=True: 8x Memory Cut in 10M Dataclass Instances." *TildAlice*, 2025. https://tildalice.io/python-dataclass-slots-memory-reduction-guide/

[27] A. Pitrou. "PEP 3155 -- Qualified name for classes and functions." 2011. https://peps.python.org/pep-3155/

[28] E. V. Smith. "PEP 557 -- Data Classes." 2017. https://peps.python.org/pep-0557/

[29] H. Schlawack. "attrs: Classes Without Boilerplate." *attrs documentation*. https://www.attrs.org/en/stable/why.html

[30] S. Colvin. "Architecture." *Pydantic Documentation*. https://docs.pydantic.dev/latest/internals/architecture/

[31] M. Shannon. "PEP 659 -- Specializing Adaptive Interpreter." 2021. https://peps.python.org/pep-0659/

[32] E. Traut. "PEP 681 -- Data Class Transforms." 2022. https://peps.python.org/pep-0681/

## Practitioner Resources

### Essential Reading

- **Python Data Model Reference**: The canonical specification. Read Section 3 of the Language Reference before any secondary source. https://docs.python.org/3/reference/datamodel.html
- **Descriptor HowTo Guide** (Raymond Hettinger): The definitive explanation of descriptors, with pure-Python equivalents of property, staticmethod, classmethod. https://docs.python.org/3/howto/descriptor.html
- **"Fluent Python" by Luciano Ramalho** (O'Reilly, 2nd edition, 2022): Chapters on the data model, descriptors, and metaclasses provide the most thorough book-length treatment.

### Talks and Videos

- **Raymond Hettinger, "Super considered super!"** (PyCon 2015): The definitive talk on cooperative multiple inheritance and `super()`.
- **Raymond Hettinger, "Descriptors -- The Magic Behind Python"**: Conference talk explaining the descriptor protocol with live demonstrations.
- **David Beazley, "Python 3 Metaprogramming"** (PyCon 2013): A thorough walkthrough of metaclasses, decorators, and descriptors.
- **James Powell, "So you want to be a Python expert?"** (PyData 2017): Covers the data model, metaclasses, and descriptors from first principles.

### PEPs for Deep Understanding

| PEP | Title | Key Concept |
|---|---|---|
| PEP 252 | Making Types Look More Like Classes | Descriptors for built-in types |
| PEP 253 | Subtyping Built-in Types | New-style classes |
| PEP 3115 | Metaclasses in Python 3000 | `__prepare__` |
| PEP 3135 | New Super | Zero-argument `super()` |
| PEP 487 | Simpler customisation of class creation | `__init_subclass__`, `__set_name__` |
| PEP 557 | Data Classes | `@dataclass` |
| PEP 659 | Specializing Adaptive Interpreter | Performance optimizations |
| PEP 681 | Data Class Transforms | Type checker support |

### Tools for Exploration

- **`inspect` module**: `inspect.getmro()`, `inspect.getmembers()`, `inspect.isdatadescriptor()` for runtime introspection.
- **`dis` module**: Disassemble bytecode to see how the interpreter dispatches dunder methods.
- **`sys.getsizeof()`**: Measure memory usage of objects with and without `__slots__`.
- **`object.__getattribute__`**: Override temporarily with a tracing implementation to debug descriptor resolution.
