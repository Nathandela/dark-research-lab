---
title: "CPython Internals: From PEG Parser to Adaptive Interpreter"
date: 2026-03-25
summary: A comprehensive survey of CPython's internal architecture spanning the PEG parser, bytecode compilation pipeline, evaluation loop, C-level object model, extension API, specializing adaptive interpreter, JIT compiler, and interactive REPL -- tracing the reference implementation's evolution from a simple tree-walking interpreter to a multi-tier optimizing execution engine.
keywords: [python, cpython, interpreter, bytecode, peg-parser, jit, adaptive-interpreter, object-model, c-extension-api, repl]
---

# CPython Internals: From PEG Parser to Adaptive Interpreter

*2026-03-25*

## Abstract

CPython, the reference implementation of the Python programming language, has undergone a profound architectural transformation over the past five years. What began as a straightforward bytecode interpreter with an LL(1) parser has evolved into a multi-tier execution engine featuring a PEG parser with direct AST generation, a specializing adaptive interpreter with inline caches, and an experimental copy-and-patch JIT compiler. These changes, driven largely by the Faster CPython initiative funded by Microsoft and led by Mark Shannon and Guido van Rossum, have yielded cumulative speedups of 40-50% over Python 3.10 baselines while preserving backward compatibility.

This survey examines the full execution pipeline of CPython: from source text entering the PEG parser (PEP 617), through the bytecode compilation stages (AST, symbol table, CFG, code object), into the evaluation loop in `ceval.c`, and across the C-level object model that underpins every Python value. We further analyze the C extension API and its stability guarantees (PEP 384), the specializing adaptive interpreter (PEP 659) introduced in Python 3.11, the copy-and-patch JIT compiler arriving experimentally in Python 3.13 (PEP 744), and the modernized interactive REPL (PEP 762). Throughout, we compare CPython's approach with alternative implementations -- PyPy, GraalPy, and RustPython -- to contextualize design trade-offs between compatibility, maintainability, and raw performance.

The paper identifies several open problems: the tension between free-threading (PEP 703) and the existing reference-counting object model, the maturation path for the JIT compiler, the fragmentation of the C extension ecosystem across ABI boundaries, and the challenge of achieving the original 5x speedup target without sacrificing CPython's role as the accessible, contributor-friendly reference implementation.

## 1. Introduction

### 1.1 Problem Statement

Python's dominance in machine learning, data science, web development, and scripting has placed extraordinary performance demands on its reference implementation. CPython's historical design priorities -- simplicity, readability, and extensibility -- produced an interpreter that is often 10-100x slower than compiled languages for CPU-bound workloads. The Faster CPython project, initiated by Mark Shannon's 2020 proposal for a 5x speedup over four release cycles [Shannon 2020], catalyzed a fundamental rearchitecting of CPython's execution engine while preserving its defining characteristics: a C-based implementation accessible to contributors with undergraduate-level computer science knowledge, full backward compatibility with the existing C extension ecosystem, and predictable performance without "sharp edges" where minor data variations cause dramatic slowdowns.

### 1.2 Scope

This survey covers CPython versions 3.9 through 3.14, focusing on architectural changes to the parser, compiler, interpreter, object model, extension API, and REPL. We treat CPython as the primary subject, referencing PyPy (RPython-based tracing JIT), GraalPy (GraalVM Truffle framework), and RustPython (Rust-based interpreter) only for comparative analysis. We exclude the standard library, the import system beyond `.pyc` caching, and application-level optimization techniques.

### 1.3 Key Definitions

- **Bytecode**: The intermediate representation executed by CPython's virtual machine, encoded as sequences of 16-bit code units (8-bit opcode + 8-bit operand) since Python 3.6.
- **Quickening**: The process of replacing generic bytecode instructions with specialized or adaptive variants at runtime.
- **Tier 1**: The standard bytecode interpreter in `ceval.c`.
- **Tier 2**: The micro-op (uop) trace interpreter and optimizer that processes hot code paths.
- **Copy-and-patch JIT**: A compilation technique that copies pre-compiled machine code templates ("stencils") and patches runtime values into placeholder "holes."
- **Inline cache**: Per-instruction metadata stored in the bytecode stream immediately following an instruction, used by specialized instructions for fast-path lookups.

## 2. Foundations

### 2.1 Interpreter Design Space

Language interpreters occupy a spectrum from tree-walking evaluators (directly traversing AST nodes) through bytecode virtual machines (compiling to an intermediate representation executed by a loop) to JIT-compiled systems (generating native machine code at runtime). CPython historically occupied the bytecode VM position, and the Faster CPython project has extended it toward JIT territory while maintaining the bytecode VM as the foundational tier.

The key theoretical trade-offs are:

| Dimension | Tree-walker | Bytecode VM | Tracing JIT | Method JIT |
|---|---|---|---|---|
| Startup latency | Lowest | Low | Low | Medium |
| Peak throughput | Lowest | Low-Medium | High | High |
| Memory overhead | Low | Low | Medium-High | Medium-High |
| Implementation complexity | Lowest | Medium | High | High |
| Debugging support | Excellent | Good | Challenging | Challenging |

CPython's multi-tier approach attempts to capture benefits across this spectrum: Tier 1 provides the low-overhead bytecode VM baseline, the adaptive interpreter adds specialization without code generation, and the Tier 2 optimizer with optional JIT pursues higher throughput for hot paths.

### 2.2 Parsing Theory

Context-free grammars (CFGs) form the theoretical basis for most programming language parsers. LL(k) parsers -- top-down predictive parsers with k tokens of lookahead -- have been the traditional choice for hand-written and generated parsers due to their simplicity and linear-time guarantees. However, LL(1) parsers impose constraints that force grammar authors to distort rule structure: left recursion must be eliminated, and overlapping first sets require factoring or rewriting.

Parsing Expression Grammars (PEGs), introduced by Bryan Ford in 2004, offer an alternative formalism where the choice operator is ordered (prioritized alternation) rather than unordered. This eliminates ambiguity by construction and permits unlimited lookahead through backtracking, made efficient via memoization (packrat parsing). PEG parsers naturally support left recursion through memoization-based techniques adapted from academic research on left-recursive packrat parsing [Warth et al. 2008].

### 2.3 Virtual Machine Architecture

CPython implements a stack-based virtual machine, where operands are pushed onto and popped from an evaluation stack. This contrasts with register-based VMs (e.g., Lua 5.0+, Dalvik) that use numbered virtual registers. Stack machines produce simpler compilers (no register allocation needed) and more compact bytecode, at the cost of more memory traffic (values move through the stack rather than staying in registers). The Tier 2 micro-op representation preserves the stack-based model but uses a format better suited to optimization and machine code translation.

## 3. Taxonomy of CPython Subsystems

The following taxonomy classifies CPython's major subsystems by their role in the execution pipeline, the Python version introducing significant changes, and their primary design constraints:

| Subsystem | Pipeline Stage | Key Version | Primary Constraint | Files |
|---|---|---|---|---|
| PEG Parser | Source -> AST | 3.9 (PEP 617) | Backward grammar compat | `Parser/parser.c`, `Grammar/python.gram` |
| Bytecode Compiler | AST -> Code Object | 3.11+ | Correctness, debuggability | `Python/compile.c`, `Python/flowgraph.c`, `Python/assemble.c` |
| Symbol Table | AST -> Scope info | Stable | Python scoping semantics | `Python/symtable.c` |
| Evaluation Loop | Bytecode execution | 3.11+ | Performance, GIL compat | `Python/ceval.c`, `Python/ceval_macros.h` |
| Object Model | Runtime values | Stable | C ABI, refcounting | `Include/object.h`, `Objects/typeobject.c` |
| C Extension API | Native extensions | PEP 384 (3.2+) | Binary compatibility | `Include/`, stable ABI subset |
| Adaptive Interpreter | Bytecode specialization | 3.11 (PEP 659) | No code generation needed | `Python/specialize.c`, `Python/bytecodes.c` |
| Tier 2 Optimizer | Trace optimization | 3.13+ | Correctness of guards | `Python/optimizer.c`, `Python/optimizer_cases.c.h` |
| JIT Compiler | Native code gen | 3.13 (PEP 744) | Build-time LLVM only | `Tools/jit/`, `jit_stencil.h` |
| REPL | Interactive mode | 3.13 (PEP 762) | Backward compat, terminals | `Lib/_pyrepl/` |

## 4. Analysis

### 4.1 The PEG Parser (PEP 617)

#### Theory and Mechanism

CPython's original parser, `pgen`, was a custom LL(1) parser generator written by Guido van Rossum as "just about the first piece of code" for Python approximately thirty-five years ago [Van Rossum 2019]. The LL(1) formalism required a two-stage process: parsing source into a Concrete Syntax Tree (CST), then transforming the CST into an Abstract Syntax Tree (AST) via `Python/ast.c`. This separation existed because LL(1) grammars could not express Python's syntax directly -- rules had to be distorted to avoid left recursion and first-set conflicts, making the CST structurally different from the desired AST.

PEP 617 [Van Rossum & Galindo Salgado 2020] replaced `pgen` with a PEG parser generated by `pegen`, a parser generator written in Python (`Tools/peg_generator/pegen/c_generator.py`). The grammar specification resides in `Grammar/python.gram` and uses the following syntax:

| Syntax | Meaning |
|---|---|
| `e1 e2` | Match e1 then e2 (sequence) |
| `e1 \| e2` | Ordered choice (try e1 first) |
| `[e]` or `e?` | Optional |
| `e*` / `e+` | Zero-or-more / one-or-more |
| `s.e+` | One-or-more e separated by s |
| `&e` / `!e` | Positive / negative lookahead |
| `~` | Commit to current alternative (cut) |
| `{ action }` | Inline action producing AST node |

A critical innovation is the use of inline actions that generate AST nodes directly during parsing, eliminating the CST intermediate representation entirely. For example:

```
expr[expr_ty]:
    | l=expr '+' r=term { _PyAST_BinOp(l, Add, r, EXTRA) }
    | l=expr '-' r=term { _PyAST_BinOp(l, Sub, r, EXTRA) }
    | t=term { t }
```

This rule demonstrates left recursion (which LL(1) cannot express), named sub-expressions (`l=expr`), and direct AST construction via action blocks. The left recursion is handled through a memoization-based technique that detects recursive calls and iteratively grows the match.

The parser uses packrat parsing with selective memoization. Rather than memoizing every rule at every position (which would consume excessive memory), CPython memoizes only rules that are involved in left recursion or that appear at positions where backtracking is likely. The parser's input is a stream of tokens rather than characters -- CPython retains its separate tokenizer (`Parser/lexer/`) because Python's tokenization (significant whitespace, string prefixes, f-string interpolation) is complex enough to warrant dedicated handling.

#### Literature Evidence

Van Rossum's blog series [Van Rossum 2019a-f] documents the development process in detail, from initial prototypes through integration. The Python Language Summit 2020 presentation [PSF 2020] describes the community decision process. The LWN.net analysis [Corbet 2020] provides independent technical assessment of the trade-offs.

#### Benchmarks

PEP 617 reports the following performance comparison on realistic workloads:

| Workload | New Parser | Old Parser |
|---|---|---|
| 100K lines arithmetic expressions (time to bytecode) | 1.28s | 1.44s |
| 100K lines arithmetic expressions (memory) | 681 MiB | 836 MiB |
| Python 3.8 stdlib, 1641 files (time to bytecode) | 3.290s | 3.367s |
| Python 3.8 stdlib, 1641 files (max RSS) | 77 MiB | 70 MiB |

The new parser is within 10% of the old parser in both speed and memory, with slightly higher memory usage (~10%) for typical code due to memoization tables, offset by the elimination of the CST intermediate representation.

#### Strengths and Limitations

**Strengths**: Eliminates grammar distortion, enabling rules to express intended syntax directly. Removes the CST layer and its associated memory and processing costs. Enables future grammar evolution (e.g., pattern matching in 3.10 was substantially easier to express in PEG). The ordered choice operator eliminates parsing ambiguity by construction.

**Limitations**: The packrat parsing approach uses more memory than a pure LL(1) parser for simple grammars. The generated parser in `Parser/parser.c` is large (>30,000 lines of generated C code) and not human-readable. Error recovery and error message quality required significant additional engineering beyond the core PEG formalism. The separate tokenizer means Python does not benefit from PEG's potential to unify lexing and parsing.

### 4.2 Bytecode Compilation Pipeline

#### Theory and Mechanism

The compilation pipeline transforms an AST into a `PyCodeObject` containing executable bytecode. The entry point is `_PyAST_Compile()` in `Python/compile.c`, which orchestrates five stages:

1. **Future statement analysis**: Scans for `from __future__ import` statements that affect compilation behavior.

2. **Symbol table construction**: `_PySymtable_Build()` in `Python/symtable.c` walks the AST to classify every name reference. The `symtable_visit_xx()` family of functions traverse different node types, calling `symtable_enter_block()` and `symtable_exit_block()` to track scope boundaries. Each name is classified as local, global, free (referenced in an enclosing scope), or cell (referenced by an inner scope). This classification drives the choice of `LOAD_FAST` vs. `LOAD_GLOBAL` vs. `LOAD_DEREF` etc. in the generated bytecode.

3. **Pseudo-instruction generation**: `compiler_codegen()` dispatches via `compiler_visit_xx()` functions that emit abstract "pseudo-instructions" -- opcodes that may not correspond directly to final bytecode but capture the compiler's intent. Macros drive emission: `ADDOP()` for bare opcodes, `ADDOP_I()` for opcodes with integer arguments, `ADDOP_NAME()` for name-bearing opcodes (with mangling support), `ADDOP_JUMP()` for jumps targeting basic blocks, and `ADDOP_LOAD_CONST()` / `ADDOP_LOAD_CONST_NEW()` for constant loading. The helper `compiler_nameop()` consults the symbol table to select the appropriate load/store/delete variant based on scope.

4. **CFG construction and optimization**: `_PyCfg_FromInstructionSequence()` in `Python/flowgraph.c` builds a Control Flow Graph where each node is a basic block -- a sequence of instructions with a single entry point and single exit point. Conditional branches and jumps terminate blocks and create edges. `_PyCfg_OptimizeCodeUnit()` then applies peephole optimizations on the CFG representation, including constant folding, dead code elimination, and jump optimization (removing jumps-to-jumps).

5. **Assembly**: `_PyAssemble_MakeCodeObject()` in `Python/assemble.c` flattens the CFG via post-order depth-first search, backpatches jump offsets, constructs exception and line-number tables, and produces the final `PyCodeObject`.

The `PyCodeObject` (defined in `Include/cpython/code.h`) contains:
- `co_code` (or `co_code_adaptive` in 3.11+): the bytecode byte string
- `co_consts`: tuple of constants referenced by `LOAD_CONST`
- `co_names`: tuple of names referenced by name-bearing opcodes
- `co_varnames`: tuple of local variable names
- `co_stacksize`: maximum evaluation stack depth
- Exception table, line number table, and source location information

Memory management during compilation uses an arena allocator (`Python/pyarena.c`). `PyArena_New()` creates an arena, and all allocations during a compilation unit are registered with the arena. `PyArena_Free()` deallocates everything in a single call, avoiding the need for individual `free()` calls throughout the compiler.

#### .pyc Files and Caching

When Python imports a module, it checks for a cached `.pyc` file in the `__pycache__` directory. The filename encodes the Python version (e.g., `module.cpython-313.pyc`). The `.pyc` file contains a magic number (incremented when the bytecode format changes, tracked in `Python/import.c`), a source hash or timestamp for invalidation, and the marshalled `PyCodeObject`. If the cache is valid, the compilation pipeline is bypassed entirely.

#### The `dis` Module

The `dis` module provides a Python-level interface for bytecode disassembly. `dis.dis()` renders bytecode in human-readable form, showing offsets, opcode names, arguments, and source line mappings. The `Bytecode` class wraps code objects for structured analysis. Since Python 3.11, some instructions are followed by `CACHE` entries representing inline cache slots -- these are visible in `dis` output but consumed by the adaptive interpreter rather than executed as traditional instructions.

#### The `compile()` Built-in

The `compile()` built-in exposes the compilation pipeline to Python code. It accepts source strings (or AST objects), a filename, and a compilation mode (`'exec'`, `'eval'`, or `'single'`), returning a code object. With `ast.PyCF_ONLY_AST` flag, it returns the AST without generating bytecode, enabling programmatic AST manipulation before compilation.

#### Strengths and Limitations

**Strengths**: The staged pipeline (AST -> symbol table -> pseudo-instructions -> CFG -> bytecode) provides clean separation of concerns. The arena allocator simplifies memory management. The CFG representation enables meaningful optimization before final emission. The `dis` module provides excellent introspection.

**Limitations**: The peephole optimizer operates on a relatively limited set of patterns compared to mature compiler backends. There is no inter-procedural optimization or inlining at the bytecode level (these are deferred to Tier 2). The compilation pipeline is single-threaded and cannot be parallelized across modules in the current architecture.

### 4.3 The Evaluation Loop (`ceval.c`)

#### Theory and Mechanism

The evaluation loop in `_PyEval_EvalFrameDefault()` (`Python/ceval.c`) is the heart of CPython's runtime. It implements a fetch-decode-dispatch cycle: fetch the next 16-bit code unit, extract the 8-bit opcode and 8-bit operand, and dispatch to the handler for that opcode.

**Dispatch strategies**. CPython supports two dispatch mechanisms, selected at compile time:

1. **Computed gotos** (preferred, requires GCC/Clang): A static array of label addresses (`opcode_targets[]`) is indexed by opcode value. The `DISPATCH()` macro expands to `goto *opcode_targets[opcode]`, enabling direct jumps without the overhead of a switch statement's comparison chain. Each opcode handler ends with a `DISPATCH()` that fetches the next instruction and jumps directly to its handler.

2. **Switch-case fallback**: For compilers lacking the labels-as-values extension, `TARGET(op)` expands to `case op:` and `DISPATCH()` jumps back to a central dispatch label. This incurs a single indirect branch at the switch statement, which is harder for branch predictors to optimize.

Comments in CPython's source note that computed gotos yield a 15-20% speedup over the switch-based dispatch, primarily because hardware branch predictors can learn the distribution of opcode-to-opcode transitions (each `goto` site has a distinct prediction entry) rather than facing a single unpredictable branch point.

**Frame objects**. Since Python 3.11, CPython uses lightweight `_PyInterpreterFrame` structures allocated on a C stack (per-thread) rather than heap-allocated `PyFrameObject` instances. This change, part of the Faster CPython project, substantially reduced the overhead of function calls. The frame structure contains:

- `f_executable`: pointer to the code object
- `previous`: pointer to the caller's frame (establishing the call stack)
- `localsplus`: a contiguous array holding local variables (indexed by `LOAD_FAST`/`STORE_FAST`) followed by the evaluation stack
- `instr_ptr`: the current instruction pointer
- `stacktop`: the stack pointer offset
- `globals`, `builtins`: namespace dictionaries

Python-to-Python calls are "inlined" by pushing a new `_PyInterpreterFrame` onto the data stack and jumping to the callee's first instruction, avoiding a recursive C-level call to `_PyEval_EvalFrameDefault()`. An `is_entry` flag tracks whether the frame was inlined, enabling proper cleanup on return.

**Operand stack**. The VM is stack-based: `PUSH(x)` expands to `*stack_pointer++ = x`, and `POP()` to `*--stack_pointer`. The compiler statically determines the maximum stack depth (`co_stacksize`) for each code object, ensuring the stack region in `localsplus` is pre-allocated. Local variable access via `LOAD_FAST`/`STORE_FAST` uses integer indexing into `localsplus`, avoiding dictionary lookups.

**GIL interaction**. The evaluation loop periodically checks for pending signals, thread switches, and other asynchronous events. The GIL is released and reacquired around these checks, allowing other threads to execute. In the default (GIL-enabled) build, the `eval_breaker` mechanism triggers these checks every N bytecode instructions (configurable via `sys.setswitchinterval()`).

**Exception handling**. Python 3.11 introduced a new exception handling mechanism based on an exception table rather than block-based `try`/`except` setup instructions. When an exception occurs, the interpreter looks up the current instruction offset in the exception table to find the appropriate handler, eliminating the runtime cost of entering and exiting `try` blocks in the non-exceptional path.

#### Instruction Definition DSL

Since Python 3.12, bytecode instructions are defined in `Python/bytecodes.c` using a domain-specific language. The `cases_generator` tool (invoked via `make regen-cases`) processes these definitions to generate:
- `Python/generated_cases.c.h`: switch cases for the Tier 1 interpreter
- `Python/executor_cases.c.h`: handlers for the Tier 2 micro-op interpreter
- `Python/optimizer_cases.c.h`: optimization rules for the Tier 2 optimizer
- `Include/internal/pycore_opcode_metadata.h`: opcode metadata

This single-source-of-truth design ensures that bytecode semantics remain consistent across all execution tiers.

#### Strengths and Limitations

**Strengths**: Computed gotos provide efficient dispatch with good branch prediction behavior. Inline frames eliminate per-call overhead for Python-to-Python calls. The instruction DSL centralizes bytecode semantics. Zero-cost exception handling removes overhead from the common (non-exceptional) path.

**Limitations**: The stack-based architecture requires more memory traffic than a register-based VM. The GIL (in default builds) remains a throughput bottleneck for CPU-bound multithreaded workloads. The evaluation loop's complexity (thousands of lines of generated code) makes it challenging to modify and debug.

### 4.4 Object Model at the C Level

#### Theory and Mechanism

Every Python value is a `PyObject` -- a C struct containing exactly two fields:

```c
typedef struct _object {
    Py_ssize_t ob_refcnt;
    PyTypeObject *ob_type;
} PyObject;
```

Variable-sized objects (lists, tuples, strings) extend this with `ob_size`:

```c
typedef struct {
    PyObject ob_base;
    Py_ssize_t ob_size;
} PyVarObject;
```

**Struct extension and inheritance**. CPython exploits a C guarantee: a pointer to any struct can be cast to a pointer to its first member. By placing `PyObject` (or `PyVarObject`) as the first member of every object struct, any object pointer can be treated as a `PyObject *`. This implements single inheritance at the C level. For example:

```c
typedef struct {
    PyObject ob_base;
    double ob_fval;
} PyFloatObject;
```

A `PyFloatObject *` can be safely cast to `PyObject *` for generic operations, then back to `PyFloatObject *` when the float-specific value is needed.

**Type objects (`PyTypeObject`)**. Types are themselves objects -- instances of `PyTypeObject`, which begins with `PyVarObject` (since types are variable-sized). The `PyTypeObject` struct contains dozens of function pointer slots (`tp_*` slots) that define object behavior:

| Slot category | Key slots | Purpose |
|---|---|---|
| Lifecycle | `tp_new`, `tp_init`, `tp_dealloc`, `tp_free` | Allocation, initialization, deallocation |
| Representation | `tp_repr`, `tp_str`, `tp_hash` | String conversion, hashing |
| Comparison | `tp_richcompare` | Rich comparison (`__eq__`, `__lt__`, etc.) |
| Attribute access | `tp_getattro`, `tp_setattro` | `__getattr__`, `__setattr__` |
| Numeric ops | `tp_as_number` -> `nb_add`, `nb_multiply`, etc. | Arithmetic operations |
| Sequence ops | `tp_as_sequence` -> `sq_concat`, `sq_item`, etc. | Indexing, concatenation |
| Mapping ops | `tp_as_mapping` -> `mp_subscript`, etc. | Dictionary-style access |
| Call | `tp_call` | Callable objects |
| Iteration | `tp_iter`, `tp_iternext` | Iterator protocol |

**The type/object bootstrap**. CPython faces a fundamental bootstrapping problem: `type` is an instance of itself (`type(type) is type`), and `object` is an instance of `type` (`type(object) is type`), while `type` inherits from `object` (`type.__bases__ == (object,)`). This circular dependency is resolved through static initialization: `PyType_Type` (the C struct for `type`) and `PyBaseObject_Type` (the C struct for `object`) are defined as static globals with their `ob_type` and `tp_base` fields manually wired to each other. `PyType_Ready()` then completes initialization by computing MRO, inheriting slots from bases, and populating the type's `__dict__` with wrapper descriptors.

**Slot-to-special-method mapping**. The `slotdefs[]` array in `Objects/typeobject.c` bidirectionally maps C-level slots to Python special methods:
- When a class defines `__add__()`, `fixup_slot_dispatchers()` sets `nb_add` to a wrapper function (`slot_nb_add()`) that calls the Python method.
- When `PyType_Ready()` processes a statically-defined type with `nb_add` set, `add_operators()` creates a wrapper descriptor in the type's `__dict__` exposing the C function as `__add__`.

**Reference counting**. `ob_refcnt` tracks the number of references to an object. `Py_INCREF()` and `Py_DECREF()` increment and decrement the count; when it reaches zero, `tp_dealloc` is called. This provides deterministic finalization (unlike tracing GC) but cannot handle reference cycles. CPython supplements reference counting with a generational cycle collector (`Modules/gcmodule.c`) that periodically scans container objects to detect and break cycles. The collector maintains three generations: young objects (collected frequently), old objects (collected less frequently), and permanent objects (never collected). Collection triggers when allocations minus deallocations exceed a configurable threshold (default: 700 for generation 0, 10 for the generational promotion ratio).

**Free-threading implications (PEP 703)**. The free-threaded build (Python 3.13+, `--disable-gil`) replaces simple reference counting with biased reference counting [Choi, Shull & Torrellas 2018], which distinguishes between the "owning" thread (which can modify `ob_refcnt` non-atomically) and other threads (which use atomic operations on a separate shared count). Per-object locks protect mutable built-in types (dict, list, set). The `mimalloc` allocator replaces `pymalloc` for thread-safe allocation.

#### Strengths and Limitations

**Strengths**: The `PyObject`/`PyTypeObject` design is elegant and extensible. Struct extension provides zero-cost single inheritance. Reference counting gives deterministic finalization, which is critical for resource management (file handles, database connections). The slot system provides a well-defined interface between the interpreter and type implementations.

**Limitations**: Reference counting has per-operation overhead (every assignment requires increment/decrement). Cyclic reference detection requires periodic GC passes. The struct layout is exposed through the C API, constraining internal changes (a problem HPy aims to solve). The type/object bootstrap is conceptually complex and error-prone for extension authors.

### 4.5 C Extension API

#### Theory and Mechanism

CPython's C API allows native code to create, manipulate, and interact with Python objects. The API exists in three tiers:

1. **Internal API** (`Include/internal/`): Unstable, changes freely between versions. Used only within CPython itself.

2. **Full (public) API** (`Include/cpython/`): Stable within major version (3.x), but extensions must be recompiled for each minor version. Exposes struct layouts and internal details.

3. **Limited API / Stable ABI** (PEP 384, Python 3.2+): A subset of the public API that provides binary compatibility across Python 3.x versions. Extensions compiled with `Py_LIMITED_API` defined can load on any Python >= the target version without recompilation. The compiled extension uses the `abi3` tag (e.g., `module.abi3.so`).

PEP 384 [Lowing 2011] established the stable ABI by restricting access to struct internals and providing opaque accessor functions instead. PEP 652 [Viktorin 2020] formalized the maintenance process. As of 2024, 16 C extensions within the CPython standard library are built using the limited API [Stinner 2024].

**Key limitations of the stable ABI**: Not all C API functions are available. Access to `PyObject` fields must go through accessor functions (`Py_REFCNT()`, `Py_TYPE()`). Some commonly-used patterns (direct struct member access, `PyTuple_GET_ITEM()`) are unavailable. Performance-sensitive extensions often cannot use the limited API.

**PEP 803 (abi3t)**: Addresses the interaction between the stable ABI and free-threaded builds, defining an `abi3t` tag for extensions compatible with both GIL-enabled and free-threaded interpreters.

**Cython**. Cython is the most widely used tool for creating CPython extensions. It translates Cython source (`.pyx` files, a superset of Python with C type declarations) into C code that calls the CPython C API directly. When variables are annotated with C types (`cdef int x`), Cython generates code that operates on C-level values without Python object overhead. Cython's generated code deeply interacts with CPython internals -- accessing `ob_refcnt`, calling `tp_*` slots, manipulating `PyObject *` pointers. Cython 3.x has experimental support for building with the limited API, but coverage is incomplete due to the many internal APIs that Cython uses for performance.

**HPy**. The HPy project [HPy 2024] proposes a fundamentally different C extension API designed for implementation-independence. Key design differences from the CPython C API:
- **Handles instead of pointers**: HPy uses opaque `HPy` handles rather than raw `PyObject *` pointers. The runtime can map handles to objects however it chooses, enabling moving garbage collectors (impossible with raw pointers).
- **Universal ABI**: Extensions compiled for HPy Universal can load on any supporting interpreter (CPython, PyPy, GraalPy) without recompilation.
- **CPython ABI mode**: For maximum performance on CPython, extensions can compile in CPython ABI mode, where `HPy` handles are thin wrappers around `PyObject *`.
- **Debug mode**: The handle-based API enables a debug mode that detects use-after-free, leaked handles, and other common extension bugs.

Real-world ports include `ultrajson-hpy`, `kiwi-solver` (a Matplotlib dependency), and an in-progress numpy port. GraalPy and PyPy provide native HPy implementations.

**PyO3**. PyO3 is a Rust-based alternative for CPython extensions, providing safe Rust abstractions over the C API. Like Cython, it is a major consumer of the C API and has experimental limited-API support.

#### Strengths and Limitations

**Strengths**: The C API's direct `PyObject *` access provides maximum performance for extensions that need it. The stable ABI enables forward-compatible binary distribution. Cython bridges the performance gap while maintaining Python-like syntax.

**Limitations**: The full C API exposes too many implementation details, constraining CPython's ability to change internals. The stable ABI covers only a subset of needed functionality. The ecosystem is fragmented: extensions must choose between performance (full API), portability (stable ABI), and implementation independence (HPy). Free-threading adds a new ABI dimension that further fragments the landscape.

### 4.6 The Specializing Adaptive Interpreter (PEP 659)

#### Theory and Mechanism

PEP 659 [Shannon 2021], implemented in Python 3.11, introduced a specializing adaptive interpreter that dynamically replaces bytecode instructions with type-specialized variants based on observed runtime behavior. The key insight is that most Python operations at any given code location consistently operate on the same types -- a phenomenon called "type stability."

**Quickening**. When a code object is first executed, its bytecode is "quickened": generic instructions that can benefit from specialization are replaced with adaptive variants (e.g., `LOAD_ATTR` becomes `LOAD_ATTR_ADAPTIVE`). Quickened bytecode resides in a writable copy separate from the original immutable bytecode, enabling fallback to the original for tracing and debugging.

**Adaptive instructions**. Each adaptive instruction maintains an execution counter in its first inline cache entry. On each execution, the counter decrements. When it reaches zero, the instruction attempts specialization by calling `_Py_Specialize_XXX()` functions in `Python/specialize.c`. These functions examine the current operand types and, if a suitable specialization exists, rewrite the instruction to a specialized variant. If specialization fails (e.g., the types are too varied), the counter resets to try again later.

**Specialized instructions**. Specialized instructions execute optimized fast paths with guard checks. For example, `LOAD_ATTR_INSTANCE_VALUE` checks that the object's type version matches the cached version (ensuring no descriptor shadowing has occurred) and loads the attribute directly from the object's value array at a cached offset. If the guard fails, the instruction deoptimizes: its opcode is rewritten back to the adaptive variant, and the generic path executes.

**Inline caches**. Specialized instructions store their metadata in inline cache entries -- 16-bit words embedded in the bytecode stream immediately after the instruction. The cache holds type version tags, attribute offsets, function pointers, and other specialization-specific data. All members of an instruction family (adaptive + specialized variants) share the same cache layout and size.

**Instruction families**. Key families include:

| Family | Specialized variants | Specialization target |
|---|---|---|
| `LOAD_ATTR` | `LOAD_ATTR_INSTANCE_VALUE`, `LOAD_ATTR_MODULE`, `LOAD_ATTR_SLOT`, `LOAD_ATTR_CLASS`, `LOAD_ATTR_WITH_HINT` | Attribute source and access pattern |
| `LOAD_GLOBAL` | `LOAD_GLOBAL_MODULE`, `LOAD_GLOBAL_BUILTIN` | Global/builtin namespace stability |
| `BINARY_OP` | `BINARY_OP_ADD_INT`, `BINARY_OP_ADD_FLOAT`, `BINARY_OP_ADD_UNICODE`, `BINARY_OP_MULTIPLY_INT`, etc. | Operand types |
| `CALL` | `CALL_PY_EXACT_ARGS`, `CALL_BUILTIN_FAST`, `CALL_METHOD_DESCRIPTOR_FAST`, etc. | Callee type and calling convention |
| `COMPARE_OP` | `COMPARE_OP_INT`, `COMPARE_OP_FLOAT`, `COMPARE_OP_STR` | Operand types |
| `STORE_ATTR` | `STORE_ATTR_INSTANCE_VALUE`, `STORE_ATTR_SLOT`, `STORE_ATTR_WITH_HINT` | Attribute storage mechanism |

**Deoptimization**. When a specialized instruction's guard fails, it replaces its own opcode with the adaptive variant using a single memory write. This is dramatically simpler than JIT-based deoptimization (which requires invalidating compiled code, reconstructing interpreter state, etc.) because specialization operates at individual instruction granularity. A saturating counter tracks hits and misses; if misses accumulate, the instruction reverts and the adaptive variant will attempt a different specialization (or give up and remain adaptive).

#### Performance Evidence

Python 3.11 achieved approximately 1.25x geometric mean speedup over 3.10 on the pyperformance benchmark suite [PSF 2022]. The specializing adaptive interpreter was the dominant contributor to this improvement. PEP 659 estimates that 25-30% of executed instructions can be usefully specialized, with individual specialization speedups of 10-60% depending on the instruction family and workload.

Memory impact: the inline cache format uses approximately 6 bytes per instruction on 64-bit systems. Python 3.10 used 2 bytes per instruction before specialization; with specialization data, 3.10 used approximately 7.8 bytes per instruction. The break-even point (where 3.11 uses less memory than 3.10 with its specialization data) is when roughly 70% of code is "hot."

#### Strengths and Limitations

**Strengths**: Works on all platforms (no code generation required). Simple deoptimization model (single instruction rewrite). Graceful degradation (adaptive instructions are only slightly slower than generic instructions). The benefit is automatic -- no programmer annotations needed.

**Limitations**: Operates at single-instruction granularity -- cannot optimize across instruction boundaries (e.g., cannot eliminate redundant type checks between consecutive specialized instructions). The inline cache consumes bytecode space even for cold code. Megamorphic sites (instructions that see many types) waste cycles on repeated failed specialization attempts.

### 4.7 JIT Compilation (Python 3.13+)

#### Theory and Mechanism

The copy-and-patch JIT compiler (PEP 744 [Yuka 2024]) extends CPython's execution model with a third tier. The system operates as follows:

**Tier 2 trace formation**. When a `JUMP_BACKWARD` instruction's counter exceeds a threshold (approximately 128 iterations by default), the Tier 1 interpreter invokes the Tier 2 optimizer. `_PyOptimizer_Optimize()` translates the hot loop into a trace of micro-operations (uops). Each Tier 1 instruction is decomposed into one or more micro-ops that capture its semantics at a finer granularity. For example, a specialized `LOAD_ATTR_INSTANCE_VALUE` might decompose into `_CHECK_ATTR_MODULE` + `_LOAD_ATTR_MODULE_VALUE`. Guards are explicit micro-ops (e.g., `_GUARD_TYPE_VERSION`, `_GUARD_DORV_NO_DICT`) that deoptimize back to Tier 1 on failure.

**Tier 2 optimization**. Before execution or JIT compilation, the trace passes through optimization phases in `Python/optimizer.c`:

1. **Symbolic execution**: Each micro-op is evaluated symbolically using `JitOptSymbol` values that track type information, constant status, and null status.
2. **Guard elimination**: Redundant type guards are removed when the symbolic state already guarantees the guard's condition.
3. **Constant propagation**: Operations on known-constant values are evaluated at optimization time.
4. **Copy propagation**: Value flow through `frame->locals` is tracked, enabling direct references to original values.
5. **Dead code removal**: Unused computations are eliminated.

**Tier 2 interpreter**. The optimized trace can be executed by the Tier 2 micro-op interpreter (a dispatch loop similar to Tier 1 but operating on micro-ops). This is available on all platforms and provides speedups from optimization alone.

**Copy-and-patch JIT**. When the build is configured with `--enable-experimental-jit`, optimized traces are additionally compiled to native machine code. The technique works as follows:

1. **Build time**: Each micro-op's C implementation is compiled by LLVM/Clang into a machine code "stencil" -- a template containing the operation's logic with placeholder values (called "holes") for runtime-determined data (operand arguments, next-instruction pointers, etc.). These stencils are stored in `jit_stencil.h`.

2. **Runtime**: The JIT copies each stencil for the trace's micro-ops into an executable memory region and patches the holes with actual runtime values (the `oparg`, the address of the next stencil, pointers to Python objects, etc.). The result is a contiguous region of native machine code that executes the entire trace.

The implementation requires Clang specifically because it is the only C compiler supporting guaranteed tail calls (`musttail`), which are necessary for CPython's continuation-passing-style approach to linking stencils together. LLVM is a build-time dependency only; the runtime JIT consists of approximately 500 lines of C code. The build-time component is approximately 900 lines of Python.

**Security**. The JIT uses W^X (write XOR execute) memory protection: stencils are writable during patching but not executable, and the finished code region is made executable but no longer writable.

**Build requirements**: Clang/LLVM is required. Build time increases by 3-60 seconds depending on platform. Nine platform configurations are tested in CI (x86_64 and aarch64 on Linux, Windows, macOS).

#### Performance Evidence

As of Python 3.13, the JIT performs approximately on par with the Tier 2 interpreter -- it does not yet provide a clear speedup over interpretation. Initial benchmarks showed 2-9% improvement on micro-benchmarks, but the overall pyperformance suite improvement is within noise. The JIT adds 10-20% memory overhead for the machine code regions.

The Faster CPython team's expectation is that the JIT infrastructure enables future optimizations (register allocation, instruction scheduling, advanced code motion) that will produce meaningful speedups in Python 3.14+. The current goal is to increase the fraction of instructions executed by Tier 2 from approximately 40% to near 90%.

Cumulative speedups across versions (geometric mean on pyperformance):
- Python 3.11 vs 3.10: ~1.25x
- Python 3.12 vs 3.10: ~1.30x (incremental gains from Tier 2 infrastructure, comprehension inlining)
- Python 3.13 vs 3.10: ~1.35x (Tier 2 optimizer, initial JIT)
- Python 3.14 vs 3.10: ~1.40-1.50x (improved GC, expanded Tier 2 coverage, JIT maturation)

#### Strengths and Limitations

**Strengths**: The copy-and-patch technique is dramatically simpler than a traditional JIT backend (no IR, no register allocator, no instruction scheduler in the current implementation). LLVM as a build-time-only dependency avoids runtime linking complexity. The instruction DSL ensures semantic consistency across all three tiers. The stencil approach automatically supports all LLVM-supported architectures.

**Limitations**: Current performance gains are modest. The Clang/LLVM build requirement excludes some environments. Copy-and-patch produces lower-quality code than an optimizing JIT (no cross-stencil register allocation or instruction scheduling). The system cannot inline Python-to-Python calls across trace boundaries. Platforms prohibiting runtime code generation (iOS) cannot use the JIT at all.

### 4.8 The REPL and Interactive Mode

#### Theory and Mechanism

Python's interactive mode has historically used a minimal REPL implemented in C (`Modules/main.c` calling the `code` module). The `code.InteractiveConsole` class wraps the `compile()` built-in and `exec()` to provide a read-eval-print loop. `sys.ps1` (default `'>>> '`) and `sys.ps2` (default `'... '`) define the primary and continuation prompts.

PEP 762 [Wouters 2024] introduced PyREPL in Python 3.13, a modern REPL implemented entirely in Python as the private `_pyrepl` module. The implementation is based on `pyrepl`, a third-party library originally written for PyPy. Key features:

**Multi-line editing**: Entire code blocks (functions, classes, loops) can be edited as a single unit, with cursor movement across lines. The old REPL committed each line to the history separately and could not navigate back into a multi-line block.

**Syntax highlighting**: Python 3.14 added real-time syntax highlighting with configurable color themes via the experimental `_colorize.set_theme()` API. Colors are controlled by the `PYTHON_COLORS`, `NO_COLOR`, and `FORCE_COLOR` environment variables.

**Autocompletion**: Tab completion is enhanced in 3.14 with module name completion inside `import` statements and attribute completion based on runtime object inspection.

**History browser**: F2 opens command history in a pager, preserving history across sessions.

**Help browser**: F1 opens the help system in a pager.

**Bracketed paste**: The REPL supports bracketed paste mode (a terminal protocol from 2002), correctly handling multi-line code pasted from external sources.

**Custom commands**: Commands like `exit` and `quit` work directly as statements rather than requiring parenthesized function calls, as long as there is no conflicting name in the reachable scope.

The old C-based REPL remains available as a fallback via `PYTHON_BASIC_REPL=1` or when terminal capabilities are insufficient. The `code` module (`Lib/code.py`) continues to provide `InteractiveConsole` and `InteractiveInterpreter` for programmatic REPL embedding.

#### Strengths and Limitations

**Strengths**: Dramatic usability improvement over the decades-old C REPL. Written in Python for maintainability and extensibility. Backward-compatible (old REPL available as fallback). The color and completion features bring CPython's REPL closer to IPython/Jupyter functionality.

**Limitations**: The `_pyrepl` module is private API, limiting third-party extension. Terminal compatibility can vary. Some users report differences in behavior from the old REPL that affect existing workflows. The REPL is not a full IDE replacement (no variable inspector, no visual debugger).

## 5. Comparative Synthesis

### 5.1 Cross-Cutting Trade-Off Table

| Dimension | CPython 3.10 | CPython 3.13+ | PyPy | GraalPy | RustPython |
|---|---|---|---|---|---|
| **Parser** | LL(1) -> CST -> AST | PEG -> AST (direct) | RPython PEG variant | Truffle PEG | PEG (Rust) |
| **Execution model** | Bytecode interpreter | 3-tier (bytecode + adaptive + JIT) | Tracing JIT (RPython) | Method JIT (Truffle/GraalVM) | Bytecode interpreter |
| **Peak throughput (vs CPython 3.10)** | 1.0x | ~1.4x | ~4-5x | ~4x (JIT warmed) | ~0.1-0.5x |
| **Startup time** | Baseline | ~Same | Slower (JIT warmup) | Slower (JIT warmup) | Similar |
| **C extension compat** | Full (native) | Full (native) | Compatibility layer (slower) | Compatibility layer (slower) | Partial |
| **Memory overhead** | Baseline | +10-20% (JIT) | Higher (JIT metadata) | Higher (GraalVM) | Similar |
| **Free-threading** | GIL only | Experimental (PEP 703) | GIL (STM abandoned) | GraalVM threads | GIL |
| **Deterministic finalization** | Yes (refcounting) | Yes (biased refcounting) | No (tracing GC) | No (JVM GC) | Yes (refcounting) |
| **Platforms** | All major + embedded | All major (JIT: Clang only) | Major platforms | JVM platforms | All Rust targets + WASM |
| **Maintainer accessibility** | High (C, well-documented) | Medium (C + DSL + LLVM) | Low (RPython meta-programming) | Low (Java + Truffle framework) | Medium (Rust) |

### 5.2 Execution Tier Comparison

| Property | Tier 1 (Bytecode) | Tier 1 + Adaptive | Tier 2 (uop interp) | Tier 2 + JIT |
|---|---|---|---|---|
| Code generation | None | None (instruction rewrite) | None | Copy-and-patch |
| Optimization scope | Single instruction | Single instruction | Trace (linear) | Trace (linear) |
| Guard overhead | None | Per-specialized-instruction | Per-guard uop | Per-guard (native branch) |
| Deopt cost | N/A | Instruction rewrite | Trace exit to Tier 1 | Trace exit to Tier 1 |
| Memory | Bytecode only | Bytecode + inline caches | + uop traces | + machine code stencils |
| Platform requirement | Any C compiler | Any C compiler | Any C compiler | Clang/LLVM |

## 6. Open Problems and Gaps

### 6.1 The 5x Target

Mark Shannon's original plan targeted a 5x speedup over four release cycles (3.10 through 3.13). The actual cumulative improvement is approximately 1.4x as of 3.14. Reaching 5x would require the JIT to mature significantly -- achieving cross-trace inlining, register allocation, and escape analysis. Whether this is achievable within CPython's constraints (maintainability, C implementation, backward compatibility) remains an open question.

### 6.2 Free-Threading and the Object Model

PEP 703's free-threaded build fundamentally changes the object model: biased reference counting adds per-operation overhead (measured as the "largest contributor to execution overhead"), per-object locks add contention and complexity, and the C extension ecosystem must be rebuilt for the new ABI. The community must determine whether free-threading eventually becomes the default (removing the GIL entirely) or remains a parallel build, and how to manage the resulting ecosystem fragmentation. The interaction between free-threading and the JIT (which must generate thread-safe code) adds further complexity.

### 6.3 C Extension API Fragmentation

The extension ecosystem now faces a multi-dimensional compatibility matrix: full API vs. limited API vs. HPy, GIL vs. free-threaded ABI, per-version compilation vs. stable ABI. Each combination has different performance and compatibility characteristics. HPy's universal ABI offers the cleanest long-term solution, but adoption is slow and the numpy port (the critical test case) is not yet complete. The gap between the C API's performance ceiling and the limited API's restrictions forces extension authors into difficult trade-offs.

### 6.4 JIT Quality and Coverage

The copy-and-patch JIT currently produces code that is roughly equivalent in speed to the Tier 2 interpreter. To deliver meaningful speedups, it needs:
- Cross-stencil register allocation (avoiding redundant stack operations)
- Trace linking (connecting separate traces for continuous execution)
- Loop unrolling and vectorization for numerical workloads
- Escape analysis and allocation sinking

Each of these features adds substantial implementation complexity to what is currently a minimalist system. The tension between simplicity (a key CPython value) and performance is acute.

### 6.5 Debugging and Profiling in a Multi-Tier World

The adaptive interpreter's instruction rewriting and the JIT's native code generation complicate debugging and profiling. `sys.settrace()` forces deoptimization to Tier 1. The `dis` module shows the original bytecode, not the specialized or JIT-compiled forms (though `dis` does show `CACHE` entries). There is no standard way to inspect Tier 2 traces or JIT-compiled code from Python. The Shannon plan envisions inserting profiling points during quickening, but this is not yet fully realized.

### 6.6 Alternative Parser Frontends

The PEG parser has proven successful, but the generated `parser.c` is enormous (>30K lines) and error messages require extensive hand-tuning. Research on incremental parsing (e.g., Tree-sitter) for IDE integration, and on error-recovery strategies for PEG parsers, could improve the developer experience without replacing the core parser.

### 6.7 Sub-interpreter Isolation

PEP 554 (multiple interpreters) and PEP 734 (sub-interpreters API) propose using isolated sub-interpreters as a concurrency model alternative to free-threading. Each sub-interpreter would have its own GIL, enabling true parallelism without the complexity of per-object locking. The interaction between sub-interpreters, the JIT (which may share compiled code), and the C extension ecosystem (which assumes a single interpreter) presents substantial engineering challenges.

## 7. Conclusion

CPython's architecture has undergone its most significant transformation since the language's creation. The shift from LL(1) to PEG parsing eliminated decades of grammar constraints and removed the CST intermediary. The specializing adaptive interpreter (PEP 659) demonstrated that substantial speedups are achievable without runtime code generation, making Python 3.11 approximately 25% faster than 3.10 through purely interpretive techniques. The Tier 2 optimizer and copy-and-patch JIT (PEP 744) have laid the infrastructure for further gains, even though the JIT's current contribution is modest.

The object model -- `PyObject`, `PyTypeObject`, reference counting, and the slot system -- remains the stable foundation upon which everything else rests, but it is also the primary constraint on future evolution. The C extension API's exposure of implementation details limits internal changes; the stable ABI (PEP 384) and HPy represent different strategies for loosening this coupling. Free-threading (PEP 703) challenges the reference-counting model at its core, requiring biased reference counting, per-object locks, and a new memory allocator.

The cumulative trajectory -- from 3.10's baseline through 3.14's approximately 1.4-1.5x speedup -- validates the Faster CPython project's incremental approach: each release delivers measurable improvement without breaking the ecosystem. Whether the original 5x target is achievable within CPython's design constraints remains to be seen; the answer likely depends on the JIT's maturation, the success of free-threading, and the community's ability to maintain the increasingly complex multi-tier execution engine without sacrificing CPython's accessibility to contributors.

## References

1. Shannon, M. (2020). "A plan to make CPython faster." GitHub repository. https://github.com/markshannon/faster-cpython/blob/master/plan.md

2. Van Rossum, G., & Galindo Salgado, P. (2020). "PEP 617 -- New PEG parser for CPython." Python Enhancement Proposals. https://peps.python.org/pep-0617/

3. Shannon, M. (2021). "PEP 659 -- Specializing Adaptive Interpreter." Python Enhancement Proposals. https://peps.python.org/pep-0659/

4. Yuka, B. (2024). "PEP 744 -- JIT Compilation." Python Enhancement Proposals. https://peps.python.org/pep-0744/

5. Wouters, T. (2024). "PEP 762 -- REPL-acing the default REPL." Python Enhancement Proposals. https://peps.python.org/pep-0762/

6. Colesbury, S. (2023). "PEP 703 -- Making the Global Interpreter Lock Optional in CPython." Python Enhancement Proposals. https://peps.python.org/pep-0703/

7. Lowing, M. (2011). "PEP 384 -- Defining a Stable ABI." Python Enhancement Proposals. https://peps.python.org/pep-0384/

8. Viktorin, P. (2020). "PEP 652 -- Maintaining the Stable ABI." Python Enhancement Proposals. https://peps.python.org/pep-0652/

9. (2025). "PEP 803 -- abi3t: Stable ABI for Free-Threaded Builds." Python Enhancement Proposals. https://peps.python.org/pep-0803/

10. (2025). "PEP 809 -- Stable ABI for the Future." Python Enhancement Proposals. https://peps.python.org/pep-0809/

11. Van Rossum, G. (2019). "PEG Parsing Series Overview." Medium. https://medium.com/@gvanrossum_83706/peg-parsing-series-de5d41b2ed60

12. Van Rossum, G. (2019). "PEG Parsers." Medium. https://medium.com/@gvanrossum_83706/peg-parsers-7ed72462f97c

13. Corbet, J. (2020). "A new parser for CPython." LWN.net. https://lwn.net/Articles/816922/

14. Python Software Foundation. (2020). "Replacing CPython's parser -- Python Language Summit 2020." https://pyfound.blogspot.com/2020/04/replacing-cpythons-parser-python.html

15. Python Software Foundation. (2022). "The 2022 Python Language Summit: Performance Improvements by the Faster CPython team." https://pyfound.blogspot.com/2022/05/the-2022-python-language-summit_2.html

16. (2024). "CPython InternalDocs: compiler.md." GitHub. https://github.com/python/cpython/blob/main/InternalDocs/compiler.md

17. (2024). "CPython InternalDocs: interpreter.md." GitHub. https://github.com/python/cpython/blob/main/InternalDocs/interpreter.md

18. (2024). "CPython InternalDocs: parser.md." GitHub. https://github.com/python/cpython/blob/main/InternalDocs/parser.md

19. Python Software Foundation. (2025). "Design of the CPython Compiler (PEP 339)." https://peps.python.org/pep-0339/

20. Python Software Foundation. (2025). "dis -- Disassembler for Python bytecode." https://docs.python.org/3/library/dis.html

21. Python Software Foundation. (2025). "C API Stability." https://docs.python.org/3/c-api/stable.html

22. Python Software Foundation. (2025). "Type Object Structures." https://docs.python.org/3/c-api/typeobj.html

23. Stinner, V. (2024). "Status of the Python Limited C API (March 2024)." https://vstinner.github.io/status-limited-c-api-march-2024.html

24. HPy Project. (2024). "HPy: a better API for Python." https://hpyproject.org/

25. HPy Project. (2024). "HPy Overview." https://docs.hpyproject.org/en/latest/overview.html

26. Baloney, A. (2024). "Python 3.13 gets a JIT." https://tonybaloney.github.io/posts/python-gets-a-jit.html

27. Coding Confessions. (2024). "The Design & Implementation of the CPython Virtual Machine." https://blog.codingconfessions.com/p/cpython-vm-internals

28. Ten Thousand Meters. (2021). "Python behind the scenes #4: how Python bytecode is executed." https://tenthousandmeters.com/blog/python-behind-the-scenes-4-how-python-bytecode-is-executed/

29. Ten Thousand Meters. (2021). "Python behind the scenes #6: how Python object system works." https://tenthousandmeters.com/blog/python-behind-the-scenes-6-how-python-object-system-works/

30. Bendersky, E. (2012). "Computed goto for efficient dispatch tables." https://eli.thegreenplace.net/2012/07/12/computed-goto-for-efficient-dispatch-tables

31. Real Python. (2024). "Python 3.13: Free Threading and a JIT Compiler." https://realpython.com/python313-free-threading-jit/

32. Real Python. (2024). "Python 3.13: A Modern REPL." https://realpython.com/python313-repl/

33. Real Python. (2025). "Python 3.14: REPL Autocompletion and Highlighting." https://realpython.com/python-repl-autocompletion-highlighting/

34. Python Software Foundation. (2024). "The Python Language Summit 2024: PyREPL." https://pyfound.blogspot.com/2024/06/python-language-summit-2024-pyrepl-new-default-repl-for-python.html

35. Microsoft for Python Developers. (2022). "A Team at Microsoft is Helping Make Python Faster." https://devblogs.microsoft.com/python/python-311-faster-cpython-team/

36. LWN.net. (2023). "GIL removal and the Faster CPython project." https://lwn.net/Articles/939981/

37. LWN.net. (2024). "Python JIT stabilization." https://lwn.net/Articles/970397/

38. Faster CPython Project. (2024). "Benchmarking Public Repository." https://github.com/faster-cpython/benchmarking-public

39. Python Speed Center. (2025). "Performance Comparison." https://speed.python.org/comparison/

40. DeepWiki. (2025). "python/cpython." https://deepwiki.com/python/cpython

41. Choi, J., Shull, T., & Torrellas, J. (2018). "Biased Reference Counting: Minimizing Atomic Operations in Garbage Collection." PACT 2018.

42. Ford, B. (2004). "Parsing Expression Grammars: A Recognition-Based Syntactic Foundation." POPL 2004.

43. Warth, A., Douglass, J.R., & Millstein, T. (2008). "Packrat Parsers Can Support Left Recursion." PEPM 2008.

44. Cython Project. (2025). "The Limited API and Stable ABI." https://cython.readthedocs.io/en/3.1.x/src/userguide/limited_api.html

45. Devguide. (2025). "CPython's internals." https://devguide.python.org/internals/

46. Devguide. (2025). "Design of CPython's Garbage Collector." https://devguide.python.org/garbage_collector/

## Practitioner Resources

- **CPython Source Code** -- https://github.com/python/cpython -- The authoritative source. The `InternalDocs/` directory contains developer-facing documentation on the compiler, interpreter, parser, and garbage collector.

- **CPython Developer Guide** -- https://devguide.python.org/ -- Official guide for CPython contributors. The "Internals" section covers compiler design, garbage collection, and the extension API.

- **Faster CPython Ideas** -- https://github.com/faster-cpython/ideas -- The planning repository for the Faster CPython project. Contains per-release design documents, performance analysis, and issue tracking for optimization work.

- **Faster CPython Benchmarks** -- https://github.com/faster-cpython/benchmarking-public -- Public mirror of the benchmark runner. Results are published to https://speed.python.org/.

- **pyperformance** -- https://pyperformance.readthedocs.io/ -- The official Python performance benchmark suite. Contains ~60 benchmarks covering real-world workloads (Django template rendering, async I/O, regular expressions, numeric computation).

- **`dis` Module** -- https://docs.python.org/3/library/dis.html -- Built-in bytecode disassembler. Essential for understanding what the compiler produces and how specialization transforms it. Use `dis.dis()` for function disassembly and `dis.Bytecode()` for structured analysis.

- **`compile()` Built-in + `ast` Module** -- https://docs.python.org/3/library/ast.html -- Enables programmatic access to the compilation pipeline. `compile(source, filename, mode, ast.PyCF_ONLY_AST)` returns the AST for inspection.

- **HPy Documentation** -- https://docs.hpyproject.org/en/latest/ -- Comprehensive guide to the HPy extension API, including migration guides from the CPython C API, universal vs. CPython ABI modes, and debug mode usage.

- **Cython** -- https://cython.org/ -- The most widely used CPython extension compiler. The annotation feature (`cython -a`) produces HTML reports showing Python-interaction intensity per source line, guiding optimization.

- **PyO3** -- https://pyo3.rs/ -- Rust bindings for the CPython API. Provides safe abstractions over `PyObject` manipulation and supports the limited API experimentally.

- **"Python behind the scenes" Blog Series** -- https://tenthousandmeters.com/ -- Victor Skvortsov's detailed technical series covering bytecode execution, the object system, the GIL, and the import system at the C level.

- **Python PEPs** -- https://peps.python.org/ -- The canonical record of Python's design decisions. Key PEPs for internals: 339 (compiler design), 384 (stable ABI), 617 (PEG parser), 652 (stable ABI maintenance), 659 (adaptive interpreter), 703 (free threading), 744 (JIT), 762 (REPL).
