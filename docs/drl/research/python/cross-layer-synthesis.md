---
title: "Cross-Layer Synthesis: Python's Architecture of Productive Compromise"
date: 2026-03-25
summary: The capstone synthesis of a 10-paper Python survey, tracing seven interaction chains that connect Python's type system, interpreter, memory model, concurrency, packaging, and scientific computing into a coherent architectural narrative.
keywords: [python, synthesis, architecture, cross-layer, language-design]
---

# Cross-Layer Synthesis: Python's Architecture of Productive Compromise

*2026-03-25*

## Abstract

Python's dominance across scientific computing, machine learning, web development, and scripting is not explained by any single design decision. It emerges from the interactions between decisions -- the way dynamic typing shapes the interpreter, the interpreter shapes memory management, memory management shapes concurrency, concurrency shapes the scientific computing architecture, and a design philosophy of productive compromise holds the entire structure together. Each subsystem embodies a trade-off that appears suboptimal in isolation but enables something essential elsewhere.

This paper traces seven interaction chains across the nine preceding papers in this survey: the dynamic typing cascade from duck typing through the GIL to the two-language architecture of scientific computing; the performance paradox where readability creates interpreter overhead that motivates a C extension ecosystem that then locks in the GIL; the gradual typing bridge that adds static analysis without changing runtime semantics; the metaprogramming-packaging tension where framework magic complicates tooling; the protocol architecture that layers dunder methods into a scientific computing stack; the free-threaded revolution that stress-tests every subsystem simultaneously; and the "batteries included" versus ecosystem tension that shapes how Python grows.

The central thesis is that Python's architecture is not a collection of independent design choices but a system of productive compromises -- each layer constraining and enabling the others -- held together by a philosophy that explicitly prioritizes practicality over purity. Understanding Python deeply requires understanding these cross-layer interactions, not just the individual subsystems.

## 1. Introduction

### 1.1 The Synthesis Question

The preceding nine papers in this survey examined CPython's major subsystems in depth: the PEG parser and adaptive interpreter [Paper 1], reference counting and garbage collection [Paper 2], duck typing and gradual typing [Paper 3], the data model and metaprogramming [Paper 4], the GIL and concurrency mechanisms [Paper 5], performance engineering from profiling to JIT compilation [Paper 6], the module system and packaging ecosystem [Paper 7], the scientific computing stack from buffer protocol to ML frameworks [Paper 8], and the design philosophy governing Python's evolution [Paper 9]. Each paper identified internal strengths, limitations, and open problems within its domain.

But Python's most distinctive characteristics are not properties of any single subsystem. They are *emergent properties* of the interactions between subsystems. The GIL exists because of reference counting. Reference counting exists because of the C extension API. The C extension API exists because Python's dynamic typing creates a performance gap that requires compiled language escape hatches. The performance gap exists because the interpreter must resolve every operation at runtime. And the interpreter must resolve every operation at runtime because duck typing defers all type decisions to the moment of use.

This paper traces these interaction chains -- the causal links that connect design decisions across architectural layers -- to reveal Python's architecture as a coherent system of productive compromises rather than a collection of historical accidents.

### 1.2 Why Cross-Layer Analysis Matters

Single-layer analysis produces misleading conclusions. Examining the GIL in isolation suggests it should be removed (it limits parallelism). Examining reference counting in isolation suggests it should be replaced with tracing GC (it cannot handle cycles and requires the GIL). Examining the C extension API in isolation suggests it should be redesigned (it exposes too many implementation details). But each of these conclusions ignores the dependencies that connect these subsystems. The GIL protects reference counting, which enables deterministic finalization, which the C extension ecosystem depends on, which the scientific computing stack is built upon. Removing any single element without addressing the chain creates cascading failures.

Cross-layer analysis reveals why Python's architecture has been remarkably stable for three decades despite continuous criticism of individual design choices. It also reveals why the free-threaded Python initiative (PEP 703) is so architecturally significant: it is the first change that simultaneously stresses every layer of the stack.

### 1.3 Methodology

Each interaction chain in Section 3 is constructed by identifying a design decision in one paper, tracing its consequences through at least three other papers, and documenting the causal mechanism at each link. We use the notation [Paper N] to reference specific findings from the preceding survey papers. Cross-references to specific sections within those papers are provided where the finding is drawn from a specific analysis.

## 2. Foundations: The Architectural Invariants

Before tracing individual interaction chains, we identify five architectural invariants -- deep design commitments that constrain all layers of the Python stack.

### 2.1 Invariant 1: Everything Is a PyObject

Every Python value -- integers, strings, functions, classes, modules, None -- is represented at the C level as a `PyObject *`: a heap-allocated structure carrying a reference count and a type pointer [Paper 1, Section 4.4]. This uniform representation enables the extraordinary flexibility of Python's object model (any value can be passed to any function, stored in any container, introspected at runtime) but imposes a per-object overhead of at least 16 bytes on 64-bit systems, plus heap allocation costs [Paper 2, Section 4.2].

This invariant is the root cause of Python's performance gap. A Python integer consumes 28 bytes where a C integer consumes 4-8 bytes. A list of N integers requires N separate heap allocations for the integer objects, N pointer slots in the list, and the list object itself -- roughly 36 KB for data that occupies 4 KB as a C `int32_t` array [Paper 6, Section 2.1]. The entire performance engineering landscape -- PyPy, Cython, Numba, the JIT, the scientific computing two-language architecture -- exists to work around this invariant without violating it.

### 2.2 Invariant 2: Names Are Resolved at Runtime

Python's duck typing philosophy means that attribute access, method dispatch, and operator resolution all occur at runtime through dictionary lookups and the descriptor protocol [Paper 3, Section 2.1; Paper 4, Section 3.4]. When the interpreter executes `obj.attr`, it traverses the MRO checking for data descriptors, then the instance dictionary, then non-data descriptors [Paper 4, Section 3.4.2]. When it evaluates `a + b`, it must look up `__add__` on `type(a)`, potentially fall back to `__radd__` on `type(b)`, and handle `NotImplemented` returns [Paper 4, Section 3.6].

This invariant is what makes duck typing work -- and what makes the adaptive interpreter's specialization so impactful. PEP 659's specialized instructions (e.g., `LOAD_ATTR_INSTANCE_VALUE`, `BINARY_OP_ADD_INT`) bypass the dictionary lookup chain when types are stable, achieving 25-30% speedups by exploiting the empirical observation that most code locations see consistent types [Paper 1, Section 4.6].

### 2.3 Invariant 3: Reference Counting Provides Deterministic Finalization

CPython's hybrid memory management -- immediate reference counting supplemented by cyclic garbage collection -- provides deterministic deallocation for the common case: objects are freed at the exact moment their last reference disappears [Paper 2, Section 5.1]. This determinism is not merely an implementation detail; it is a *relied-upon behavior* of the language. Context managers, file handles, database connections, and locks depend on `__del__` firing promptly when an object's last reference is released. The entire C extension ecosystem assumes this behavior.

This invariant is what makes the GIL necessary (non-atomic reference count operations require serialization) and what makes GIL removal so difficult (every alternative must preserve the determinism that code depends on).

### 2.4 Invariant 4: C Extensions Are First-Class Citizens

Python's C extension API, dating to the language's earliest versions, allows native code to create, manipulate, and interact with Python objects through raw `PyObject *` pointers [Paper 1, Section 4.5]. This API is the mechanism through which NumPy, SciPy, pandas, PyTorch, and thousands of other packages achieve performance. The API exposes internal implementation details -- struct layouts, reference counting macros, type object slots -- because that exposure is what enables zero-overhead interoperation.

This invariant creates the "C extension lock-in": any change to CPython's internals risks breaking the extension ecosystem. The stable ABI (PEP 384) provides a restricted subset for binary compatibility, but the most performance-critical extensions cannot use it [Paper 1, Section 4.5].

### 2.5 Invariant 5: Practicality Beats Purity

The Zen of Python's most consequential aphorism -- "Special cases aren't special enough to break the rules. Although practicality beats purity." -- encodes a meta-principle that governs all architectural decisions [Paper 9, Section 3.2]. Python's designers consistently choose pragmatic solutions over theoretically optimal ones: reference counting over tracing GC (pragmatic for C interop), the GIL over fine-grained locking (pragmatic for simplicity), dynamic typing over static typing (pragmatic for rapid iteration), gradual typing that does not affect runtime semantics (pragmatic for adoption).

This invariant explains why Python's architecture looks "wrong" from any single theoretical perspective but "right" from the perspective of productive compromise.

## 3. Interaction Chain Analysis

### 3.1 The Dynamic Typing Cascade

**Chain**: Duck typing [Paper 3] --> runtime attribute lookup [Paper 1] --> GIL for memory safety [Papers 2, 5] --> limited parallelism [Paper 5] --> two-language scientific computing [Paper 8]

This is Python's most consequential interaction chain, connecting the language's foundational design philosophy to its most criticized limitation and its most successful ecosystem.

**Link 1: Duck typing forces runtime resolution.** Python's duck typing philosophy -- "if it walks like a duck and quacks like a duck, it's a duck" -- means that the suitability of an object for any operation is determined at the moment of use [Paper 3, Section 2.1]. When the interpreter encounters `len(x)`, it cannot know at compile time whether `x` has a `__len__` method; it must look up `__len__` through the descriptor protocol at runtime. Every attribute access, every method call, every arithmetic operation triggers a runtime lookup chain that traverses dictionaries and the MRO [Paper 4, Section 3.4].

**Link 2: Runtime resolution creates per-operation overhead.** Each runtime lookup involves dictionary hash computations, probe sequences, key comparisons, and descriptor protocol dispatch. A simple attribute access that a C compiler resolves as a fixed-offset memory load requires dozens of operations in CPython. Noronha et al. (2021) measured that name access opcodes (`LOAD_ATTR`, `LOAD_GLOBAL`, `LOAD_FAST`) dominate execution time across pyperformance benchmarks [Paper 6, Section 2.2]. The cumulative result is CPython being 10-100x slower than C for equivalent computations.

**Link 3: Per-operation overhead includes reference counting.** Every value that flows through the interpreter -- arguments, return values, temporaries -- triggers `Py_INCREF` on creation and `Py_DECREF` on disposal. Reference counting consumes 5-10% of total execution time [Paper 6, Section 2.2]. These operations mutate the `ob_refcnt` field in the object header, and since they are non-atomic in the default build, concurrent execution by multiple threads would corrupt reference counts, causing use-after-free or memory leaks [Paper 2, Section 2.3].

**Link 4: Reference counting safety requires the GIL.** The GIL serializes all Python bytecode execution, making reference count operations implicitly atomic [Paper 5, Section 2.1]. Guido van Rossum's 2007 constraint -- "any replacement must not degrade single-threaded performance" -- eliminated the naive alternative of per-object locks, which Greg Stein's 1999 patch showed incurred 40-50% single-threaded overhead [Paper 5, Section 8.1]. The GIL makes single-threaded reference counting fast (no atomics, no memory barriers) at the cost of serializing all CPU-bound Python execution.

**Link 5: GIL serialization prevents multi-core parallelism.** A CPU-bound Python program running on a 64-core server uses exactly one core [Paper 5, Section 1.1]. David Beazley's measurements showed that adding a CPU-bound thread to a network server degraded throughput by approximately 7x under the old tick-based GIL [Paper 5, Section 2.3]. The time-based GIL (Python 3.2+) reduced this penalty but cannot eliminate the fundamental serialization.

**Link 6: Parallelism limits drive the two-language architecture.** The scientific computing community resolved the performance and parallelism constraints not by fixing Python but by building a layered architecture where Python serves as the orchestration layer atop compiled C/Fortran/CUDA kernels [Paper 8, Section 2.2]. The buffer protocol (PEP 3118) enables zero-copy data sharing between Python and compiled code [Paper 8, Section 4]. NumPy operates on contiguous memory buffers with compiled C loops, achieving orders-of-magnitude speedups not by making Python faster but by ensuring numerical workloads never execute scalar loops in Python [Paper 8, Section 5.4].

**Emergent property**: Python's dynamic typing, through a chain of six causal links, produces the two-language architecture that defines modern scientific computing. The architecture succeeds because it respects rather than fights the cascade: Python handles what it is good at (orchestration, expressiveness, interactivity) while compiled languages handle what Python cannot do efficiently (tight numerical loops, parallelism).

| Layer | Decision | Consequence | Paper |
|-------|----------|-------------|-------|
| Type system | Duck typing | Runtime attribute lookup | 3 |
| Interpreter | Dynamic dispatch | 10-100x overhead vs. C | 1, 6 |
| Memory | Reference counting | Non-atomic `ob_refcnt` | 2 |
| Concurrency | GIL | Single-core Python execution | 5 |
| Scientific | Two-language architecture | Python + C/Fortran/CUDA | 8 |

### 3.2 The Performance Paradox

**Chain**: "Readability counts" [Paper 9] --> interpreter simplicity [Paper 1] --> performance gap [Paper 6] --> C extension ecosystem [Paper 1] --> GIL dependency [Paper 5] --> free-threaded C extension challenge [Papers 2, 5]

This chain reveals a paradox: the design principles that made Python successful created the performance constraints that made C extensions necessary, and those extensions now constrain Python's ability to evolve.

**Link 1: Readability drives interpreter simplicity.** Python's design philosophy -- "readability counts," "simple is better than complex," "the implementation should be easy to explain" [Paper 9, Section 3.2] -- shaped CPython's implementation priorities. The reference interpreter was designed to be accessible to "contributors with undergraduate-level computer science knowledge" [Paper 1, Section 1.1]. This ruled out sophisticated optimization techniques (tracing JIT, advanced type inference, moving GC) that would improve performance but increase implementation complexity.

**Link 2: Interpreter simplicity creates the performance gap.** CPython's stack-based bytecode VM with dynamic dispatch executes a fetch-decode-dispatch cycle for every instruction [Paper 1, Section 4.3]. Computed gotos provide 15-20% speedup over switch dispatch [Paper 1, Section 4.3], but the fundamental overhead remains: each Python operation requires interpreter loop iteration, type checking, method dispatch, and reference counting. The Faster CPython project has achieved cumulative 40-50% speedup from Python 3.10 to 3.14, but this still leaves Python 10-50x slower than compiled languages for CPU-bound workloads [Paper 6, Section 2.3].

**Link 3: The performance gap motivates C extensions.** Since Python cannot achieve compiled-language performance internally, the ecosystem builds performance-critical components in C, C++, Fortran, or Rust and calls them through CPython's C API [Paper 6, Section 4.7]. NumPy, SciPy, pandas, PyTorch, TensorFlow, and Polars all use this approach. The C extension mechanism is so central to Python's utility that it has become an architectural pillar rather than an optimization technique.

**Link 4: C extensions depend on the GIL.** C extension authors write code that assumes single-threaded access to Python objects while holding the GIL. The extension API's reference counting protocol (`Py_INCREF`/`Py_DECREF`) uses non-atomic operations. Internal data structures within extensions are not protected by per-object locks. The GIL provides implicit thread safety that extension authors depend on without realizing it -- the safety is invisible because it is universal [Paper 5, Section 2.2; Paper 1, Section 4.5].

**Link 5: Free-threading breaks C extension assumptions.** PEP 703's free-threaded build removes the GIL, replacing non-atomic reference counting with biased reference counting and requiring extensions to opt in via `Py_mod_gil = Py_MOD_GIL_NOT_USED` [Paper 5, Section 8.5]. Extensions that have not opted in cause the GIL to be automatically re-enabled when imported, defeating the purpose of the free-threaded build. As of early 2026, the long tail of thousands of C extensions on PyPI remains largely untested for free-threading compatibility [Paper 5, Section 11.1].

**The paradox**: Python's readability philosophy created a performance gap that necessitated C extensions, and those extensions now create the strongest resistance to removing the GIL -- the very limitation that the performance gap also motivates working around. The ecosystem is locked in a loop: the GIL constrains performance, but removing it threatens the C extensions that exist to compensate for the performance constraints.

### 3.3 The Gradual Typing Bridge

**Chain**: Optional type hints [Paper 3] --> mypyc/Cython optimization [Paper 6] --> IDE experience [Paper 3] --> no runtime effect [Paper 1] --> static/dynamic duality

This chain traces how gradual typing creates a unique architectural layer that sits between Python's dynamic runtime and a static analysis overlay, connecting to but never altering the interpreter.

**Link 1: PEP 484 introduces type hints as metadata.** Python's gradual typing, grounded in Siek and Taha's theory (2006), adds type annotations that are "not enforced at runtime by the interpreter" [Paper 3, Section 3.3]. The annotations are stored in `__annotations__` dictionaries but have zero effect on bytecode generation, dispatch, or execution. The interpreter treats `def f(x: int) -> str` identically to `def f(x)` [Paper 1].

**Link 2: Type annotations enable ahead-of-time optimization.** mypyc exploits the insight that if a codebase is fully annotated for mypy, those annotations contain sufficient information to generate efficient C code [Paper 6, Section 4.6]. Type-annotated classes become C structs with fixed-offset attribute access; annotated function signatures become C functions with optimized calling convention. The mypy type checker itself has been compiled with mypyc since 2019, achieving 4x performance improvement [Paper 6, Section 4.6.2]. Cython's pure Python mode similarly leverages standard annotations for type-directed compilation [Paper 6, Section 4.4.3].

**Link 3: Type annotations transform the IDE experience.** pyright (Microsoft, Rust-based architecture) and mypy provide real-time type checking, autocompletion, rename refactoring, and go-to-definition powered by type information [Paper 3]. Protocols (PEP 544) formalize duck typing for static analysis -- "static duck typing" -- enabling type checkers to verify interface contracts without requiring inheritance [Paper 3, Section 4.3]. The 2024-2025 Python Typing Surveys show that type annotations have become standard practice in production codebases.

**Link 4: The static/dynamic duality is unique.** Python occupies a singular position: a dynamically typed language with a comprehensive static type annotation system that the runtime ignores. This creates a "two-language" effect within the language itself -- the Python that type checkers analyze is not the Python that CPython executes. The type system is deliberately unsound (it cannot prevent runtime type errors) because soundness would require either pervasive runtime checks or restrictions on dynamic features [Paper 3, Section 3.4]. The `Any` type propagates through partially annotated code, and `# type: ignore` comments allow developers to override the checker.

**Emergent property**: Gradual typing creates a bridge layer between Python's dynamic and static worlds. It enables optimization (mypyc), improves tooling (IDE experience), and facilitates large-codebase maintenance, all without altering the fundamental runtime architecture. But the bridge is one-directional: static types inform tools about the code, but the code does not change to respect the types. This duality -- the same source code meaning different things to different tools -- is unique to Python among mainstream languages.

### 3.4 The Metaprogramming-Packaging Tension

**Chain**: Metaclasses and import hooks [Papers 4, 7] --> framework magic [Paper 4] --> static analysis complexity [Paper 3] --> packaging challenges [Paper 7]

Python's metaprogramming power enables the framework ecosystem that makes the language productive, but that same power creates cascading difficulties for tools that must reason about Python code without executing it.

**Link 1: The data model enables arbitrary customization.** Python's dunder method protocol delegates virtually every operation to user-overridable special methods [Paper 4, Section 1]. Metaclasses control class creation via `__new__`, `__init__`, and `__prepare__` [Paper 4, Section 5]. Import hooks (custom finders and loaders on `sys.meta_path`) can transform module loading [Paper 7, Section 4.1]. Descriptors intercept attribute access [Paper 4, Section 4]. This creates a metaprogramming surface that is unmatched among mainstream languages.

**Link 2: Frameworks exploit metaprogramming extensively.** Django uses metaclasses to transform class definitions into ORM models with database-backed attribute access. SQLAlchemy uses descriptors and metaclasses to map Python classes to SQL tables. Pydantic uses `__init_subclass__` and class introspection to generate validation logic from type annotations. These frameworks achieve remarkable developer ergonomics -- a Django model class reads like a declarative schema but produces a full database-backed object with query capabilities [Paper 4].

**Link 3: Metaprogramming defeats static analysis.** Type checkers must reason about code without executing it, but metaclasses and descriptors can transform the meaning of class definitions in ways that are only determinable at runtime [Paper 3]. A metaclass that dynamically adds methods to a class produces attributes that no static analyzer can predict without simulating the metaclass's `__new__`. Django's model fields, which use descriptors to transform attribute access into database queries, require dedicated type checker plugins (django-stubs) to be typed correctly. The `__array_function__` protocol (NumPy) intercepts function calls based on argument types, creating dispatch behavior that type checkers cannot follow [Paper 8, Section 5.5].

**Link 4: Metaprogramming complicates packaging.** The import system's extensibility means that a package's behavior can change based on import hooks, `__init__.py` side effects, and dynamic path manipulation [Paper 7, Section 4.1]. Before the `pyproject.toml` revolution, even determining a package's dependencies required executing `setup.py` -- arbitrary Python code that could import modules, read files, or make network requests [Paper 7, Section 2.1]. Build backends must handle packages that use metaclasses to generate code at import time, import hooks that transform source before execution, and `__init__.py` files that modify `sys.path` during import.

**Emergent property**: There is a fundamental tension between metaprogramming power and toolability. Every mechanism that makes Python code more expressive at runtime makes it harder to analyze statically and harder to package reliably. The typing ecosystem's response (Protocols, plugins, stubs) adds complexity to bridge this gap, while the packaging ecosystem's response (declarative `pyproject.toml`, PEP 517 isolation) attempts to contain the damage. The tension is irresolvable because it reflects a genuine trade-off between runtime flexibility and static predictability.

### 3.5 The Protocol Architecture

**Chain**: Dunder protocols [Paper 4] --> buffer protocol [Paper 8] --> NumPy array protocols [Paper 8] --> framework-agnostic scientific code --> cumulative complexity

Python's data model's extensibility, realized through dunder methods, forms a layered protocol architecture that enables the scientific computing ecosystem -- each layer building on the one below it, and each layer adding interoperability at the cost of complexity.

**Link 1: Dunder methods establish the protocol pattern.** The data model's dunder methods -- `__len__`, `__iter__`, `__getitem__`, `__add__`, `__enter__`, `__exit__` -- define a structural interface pattern: objects declare their capabilities through method presence rather than inheritance [Paper 4, Section 3]. The `collections.abc` module formalizes this with `__subclasshook__`, enabling `isinstance(obj, Iterable)` to return `True` for any object with `__iter__` regardless of class hierarchy [Paper 4, Section 3.7.2]. This pattern -- interfaces defined by method presence, checked structurally -- becomes the template for every interoperability protocol in the scientific stack.

**Link 2: The buffer protocol enables zero-copy memory sharing.** PEP 3118's buffer protocol extends the dunder pattern to the C level: objects implement `bf_getbuffer` and `bf_releasebuffer` to expose raw memory regions [Paper 8, Section 4]. The `Py_buffer` structure describes the memory layout (pointer, shape, strides, format), enabling any buffer-aware consumer to operate directly on the producer's memory without copying. PEP 688 (Python 3.12) brought this to the Python level with `__buffer__` and `__release_buffer__` [Paper 8, Section 4.3].

**Link 3: NumPy builds array protocols atop the buffer protocol.** NumPy's ndarray implements the buffer protocol to expose its data memory, and extends the interoperability pattern with three array-specific protocols: `__array__` (conversion to ndarray), `__array_ufunc__` (override ufunc behavior), and `__array_function__` (override any NumPy function) [Paper 8, Section 5.5]. These protocols enable libraries like Dask (lazy computation graphs), CuPy (GPU arrays), and Pint (unit-aware arrays) to intercept NumPy operations and provide alternative implementations.

**Link 4: The array API standard generalizes the pattern.** The array API standard (`__array_namespace__`, data-apis.org) defines a minimal, well-specified interface for N-dimensional arrays, enabling framework-agnostic code that works identically on NumPy, CuPy, PyTorch, JAX, and Dask arrays [Paper 8, Section 6]. SciPy and scikit-learn have begun adopting this standard, enabling their algorithms to operate on GPU arrays without code changes [Paper 8, Section 6.4]. The DataFrame interchange protocol (`__dataframe__`) extends the same pattern to tabular data.

**Link 5: Each protocol layer adds complexity.** The stack is now five layers deep: dunder methods --> buffer protocol --> array protocols --> array API standard --> framework-specific protocols (`__torch_function__`, JAX pytree protocol). Each layer provides genuine interoperability, but the cumulative complexity is substantial. Library authors must decide which protocol layers to implement. Framework-agnostic code must navigate the `array_namespace` pattern. The `__array_function__` protocol's requirement that overriding libraries re-implement every NumPy function they intercept creates a large maintenance surface [Paper 8, Section 5.5].

**Emergent property**: The protocol architecture is Python's unique contribution to scientific computing ecosystem design. No other language has achieved comparable library interoperability through layered structural protocols. But the architecture's power comes at the cost of accretion: each new protocol layer is motivated by limitations of the previous one, creating a growing stack that is difficult to comprehend in its totality.

### 3.6 The Free-Threaded Revolution

**Chain**: PEP 703 [Paper 5] --> biased refcounting [Paper 2] --> C extension API breakage [Paper 1] --> scientific stack threat [Paper 8] --> dual-build packaging [Paper 7] --> philosophy tension [Paper 9]

The free-threaded Python initiative is the most architecturally significant change in CPython's history because it simultaneously stresses every layer of the stack. It serves as a natural stress test for the entire architecture of productive compromise.

**Link 1: PEP 703 removes the GIL.** Sam Gross's PEP 703 provides the technical foundation for GIL-free execution through biased reference counting (thread-local fast paths for the owning thread, atomic operations for other threads), deferred reference counting (for high-contention objects like code objects and module constants), immortalization (for global immutables like `None`, `True`, small integers), per-object locks (for mutable built-in types), and mimalloc (replacing pymalloc for thread-safe allocation) [Paper 5, Section 8.2].

**Link 2: Biased reference counting changes the object header.** The free-threaded build expands the `PyObject` header from 16 bytes to approximately 24-32 bytes, adding `ob_tid` (owning thread ID), `ob_ref_local` (thread-local count), `ob_ref_shared` (atomic shared count), and GC tracking bits [Paper 2, Section 4.5]. This per-object overhead increase affects every Python object, impacting memory consumption across all workloads. The biased scheme maintains near-zero overhead for the common case (>90% of reference count operations occur on the owning thread) but introduces measurable overhead when objects are shared across threads [Paper 5, Section 8.2].

**Link 3: The C extension API faces its greatest challenge.** Extensions compiled for the GIL-enabled build assume non-atomic reference counting. The free-threaded build requires extensions to declare compatibility via `Py_mod_gil = Py_MOD_GIL_NOT_USED` [Paper 5, Section 8.5]. Extensions with internal shared mutable state must add their own synchronization. Extensions that relied on GIL-provided atomicity for compound operations (e.g., `counter += 1` across threads) will exhibit new data races. The stable ABI must be extended with `abi3t` (PEP 803) for extensions compatible with both builds [Paper 1, Section 4.5].

**Link 4: The scientific stack is most exposed.** NumPy, SciPy, pandas, and PyTorch are among the most heavily used C extensions, and they are deeply intertwined with CPython's internal APIs for performance. NumPy's ufunc execution holds the GIL during most operations [Paper 8, Section 5.4]. SciPy's Cython extensions access internal CPython structures through the full (non-limited) API [Paper 8, Section 7.2]. The scientific stack's migration to free-threading-compatible builds is a multi-year effort that has begun (NumPy and Cython have preliminary support as of Python 3.14) but is far from complete [Paper 5, Section 8.4].

**Link 5: The packaging ecosystem must handle dual builds.** The wheel format must distinguish between GIL-enabled and free-threaded builds, since extensions compiled for one may not work with the other. Until a unified stable ABI can serve both builds (the Phase III criterion in PEP 779), PyPI must host separate wheels, package managers must select the correct variant, and build backends must produce both [Paper 7]. This doubles the binary distribution surface for every package with compiled extensions.

**Link 6: The design philosophy faces a fundamental question.** The Zen of Python's emphasis on simplicity is tested by free-threading's introduction of shared-memory concurrency hazards to a language community historically insulated by the GIL [Paper 9]. Python programmers will encounter data races, deadlocks, and memory ordering issues for the first time. The Steering Council must balance "move fast" (enabling parallelism for performance-critical workloads) against ecosystem stability (avoiding breakage of the millions of Python programs that assume GIL-serialized execution) [Paper 5, Section 11.3; Paper 9].

**Emergent property**: The free-threaded transition is an architectural stress test. It reveals every hidden dependency between Python's subsystems -- every assumption that the GIL made invisible. The fact that removing a single mutex requires changes to the memory model, object layout, C API, scientific stack, packaging system, and community education strategy demonstrates how deeply interconnected Python's architecture is.

### 3.7 The "Batteries Included" vs Ecosystem Tension

**Chain**: Stdlib philosophy [Paper 9] --> packaging ecosystem shape [Paper 7] --> scientific stack outside stdlib [Paper 8] --> typing bridges both [Paper 3]

Python's standard library philosophy has shaped not only what is inside the language distribution but also what grew outside it, and the bridge between these two worlds reveals a productive tension that drives the ecosystem's evolution.

**Link 1: "Batteries included" provides a capable baseline.** Python's standard library -- `os`, `json`, `re`, `sqlite3`, `http`, `asyncio`, `pathlib`, `dataclasses`, `itertools` -- provides sufficient functionality for many tasks without any third-party dependencies [Paper 9, Section 8.1]. This philosophy was critical in Python's early decades when package installation was cumbersome. The stdlib serves as the stable foundation that all Python code can rely on, with a backward compatibility guarantee enforced by the "never again" commitment against Python 2-to-3-scale breakage [Paper 9, Section 7.1.4].

**Link 2: The packaging ecosystem emerged to fill gaps.** The stdlib cannot serve every domain. Its annual release cycle is too slow for fast-moving fields (ML, data science), its maintenance burden limits scope expansion, and some domains require compiled dependencies that the stdlib cannot portably include [Paper 9, Section 8.4]. The packaging ecosystem -- pip, PyPI, virtual environments, build backends -- emerged to enable a third-party library ecosystem that could move independently [Paper 7]. The evolution from `distutils` through `setup.py` to `pyproject.toml` represents the gradual formalization of this parallel distribution channel [Paper 7, Section 2.1].

**Link 3: Scientific computing grew entirely outside the stdlib.** NumPy, SciPy, pandas, matplotlib, scikit-learn, PyTorch, and JAX are all third-party packages [Paper 8]. The scientific stack could not have developed within the stdlib because it requires compiled extensions (C, Fortran, CUDA), has complex build dependencies (BLAS/LAPACK, GPU drivers), and iterates faster than the annual Python release cycle. The Scientific Python project (scientific-python.org) coordinates the ecosystem through SPEC documents rather than through stdlib inclusion [Paper 8, Section 2.3].

**Link 4: Typing bridges stdlib and ecosystem.** The `typing` module lives in the stdlib, but its evolution is driven by the needs of both stdlib and third-party code [Paper 3]. `typing_extensions` provides a backport mechanism that stages new typing features for older Python versions, effectively decoupling the typing system's evolution from the stdlib's release cycle [Paper 3]. Runtime validation libraries (pydantic, beartype, msgspec) use the same type annotation syntax for both stdlib types and third-party types, creating a unified type vocabulary across the entire ecosystem [Paper 3].

**Emergent property**: The stdlib/ecosystem tension is a feature, not a bug. The stdlib provides stability and universality; the ecosystem provides agility and specialization. The typing system serves as the connective tissue, providing a shared vocabulary that works identically for `dict[str, int]` (stdlib) and `DataFrame[Schema]` (third-party). The tension drives evolution: successful third-party innovations (dataclasses from attrs, tomllib from tomli) are selectively absorbed into the stdlib, while the ecosystem continues to push boundaries that the stdlib cannot.

## 4. Emergent Properties

The seven interaction chains reveal properties of Python's architecture that cannot be attributed to any single subsystem.

### 4.1 The Optimization Boundary

Python's architecture creates a sharp boundary between "Python-speed" and "C-speed" code. Above the boundary, everything passes through the interpreter's dynamic dispatch, reference counting, and dictionary lookups. Below the boundary, compiled code operates on raw memory with static dispatch and register allocation. The entire performance engineering landscape -- from NumPy's vectorized operations to PyTorch's compiled computation graphs to Polars' Rust-backed DataFrames -- is organized around minimizing the number of times execution crosses this boundary per unit of useful computational work [Paper 6; Paper 8, Section 2.1].

This boundary is *architectural*, not merely performance-related. It determines which design patterns are viable: vectorized NumPy operations (one boundary crossing per array operation) succeed where Python loops over the same data (N boundary crossings for N elements) fail. The array API standard, ufunc dispatch, and buffer protocol all exist to manage efficient passage across this boundary.

### 4.2 The Extensibility-Analyzability Trade-off

Python's metaprogramming facilities (metaclasses, descriptors, import hooks, `__getattr__`) make it extraordinarily extensible -- framework authors can transform the semantics of classes, modules, and attribute access in ways that feel like language extensions. But every extensibility mechanism is a deduction that static analysis cannot make. The typing ecosystem's response -- Protocols, plugins, stubs, `@override` -- adds layers of annotation to recover what the dynamic semantics obscure. The packaging ecosystem's response -- declarative `pyproject.toml`, build isolation -- attempts to constrain the damage that executable configuration can cause.

This trade-off is not resolvable because it reflects a fundamental tension in programming language design between expressiveness and tractability. Python's position -- maximizing extensibility while retrofitting analyzability through optional typing -- is distinctive among mainstream languages.

### 4.3 The Stability-Evolution Tension

Python's ecosystem depends on stability (the "never again" commitment, C extension backward compatibility, the Zen's emphasis on consistency) but also demands evolution (free-threading, JIT compilation, new typing features, packaging improvements). The interaction chains reveal how stability constraints propagate: the C extension API's stability guarantee constrains the memory model, which constrains the concurrency model, which constrains the performance strategy. Conversely, evolutionary pressures propagate: the demand for parallelism drives free-threading, which requires memory model changes, which require C extension migration, which requires packaging infrastructure for dual builds.

The PEP process mediates this tension by requiring backward compatibility analysis for every proposal and by providing deprecation pathways that span multiple releases [Paper 9, Section 4]. The Python 2-to-3 transition taught the community that even beneficial breaking changes can cost a decade of migration [Paper 9, Section 7.1].

### 4.4 The Community-Architecture Feedback Loop

Python's design philosophy is not merely a rationale for past decisions; it actively shapes future evolution through the PEP process and community norms [Paper 9]. When a proposed feature is criticized as "un-Pythonic," the objection carries architectural weight because the Zen's principles are design constraints. Conversely, when the architecture makes something impossible (e.g., true parallelism before PEP 703), the community develops workarounds (multiprocessing, C extensions that release the GIL) that become established patterns, which then constrain future architectural changes (because those workarounds must continue to work).

## 5. The Free-Threaded Transition as Architectural Stress Test

Section 3.6 traced the free-threaded revolution as an interaction chain. Here we examine it as a stress test that reveals the load-bearing structures of Python's architecture.

### 5.1 Which Assumptions Break

The GIL provides an implicit invariant that propagates through every layer: "only one thread executes Python bytecode at a time." Removing this invariant breaks assumptions in:

| Subsystem | Assumption | What Breaks | Mitigation |
|-----------|-----------|-------------|------------|
| Memory model | `Py_INCREF`/`Py_DECREF` are non-atomic | Race conditions on refcounts | Biased reference counting [Paper 2] |
| Object allocator | pymalloc is single-threaded | Allocation data corruption | mimalloc replacement [Paper 5] |
| Cyclic GC | Collector runs without contention | Concurrent mutation during traversal | Stop-the-world pauses [Paper 2] |
| Eval loop | Frame state is thread-private | Shared frame corruption | Per-thread frame stacks [Paper 1] |
| Built-in types | dict/list/set internal consistency | Concurrent modification crashes | Per-object locks [Paper 5] |
| C extensions | Implicit thread safety | Data races, crashes | Explicit opt-in [Paper 5] |
| Scientific stack | GIL held during ufunc execution | Race conditions in array ops | Extension migration [Paper 8] |
| Packaging | One binary per platform | Need GIL/no-GIL variants | Dual wheel builds [Paper 7] |

### 5.2 The Migration Path

PEP 703's phased approach -- experimental (3.13), officially supported (3.14), potentially default (3.16+) -- is a direct lesson from the Python 2-to-3 transition [Paper 9, Section 7.1.4]. The automatic GIL re-enablement when importing incompatible extensions provides a safety net that allows incremental ecosystem migration: programs that use only compatible extensions get free-threading benefits; programs that use incompatible extensions fall back to GIL-serialized execution without crashing.

The single-threaded performance penalty has been reduced from approximately 40% in early 3.13 development to 5-10% in 3.14 [Paper 5, Section 8.4; Paper 6, Section 4.9.2]. PEP 779 defines criteria for Phase III (free-threading as default): performance overhead must be "acceptable," ecosystem coverage must be "sufficient," and ideally a unified stable ABI should serve both builds from a single wheel.

### 5.3 What the Stress Test Reveals

The free-threaded transition reveals that Python's architecture is more tightly coupled than its modular appearance suggests. A change to the memory model (biased reference counting) requires changes to the object header layout, the C extension API, the garbage collector, the memory allocator, the evaluation loop, the packaging format, and the community's mental model of thread safety. This coupling is the cost of the "productive compromise" architecture: each layer's simplicity depends on assumptions provided by other layers (particularly the GIL), and removing those assumptions requires coordinated changes across all layers.

## 6. Comparative Perspective

### 6.1 Python vs. Go: Productive Compromise vs. Deliberate Constraints

Go's architecture, analyzed in the companion survey, is built on *deliberate constraints* -- the intentional omission of features (exceptions, generics until 1.18, inheritance, operator overloading) that simplifies each remaining feature and enables fast compilation, simple tooling, and predictable performance [Go Survey, Cross-Layer Synthesis]. Python's architecture is built on *productive compromise* -- the acceptance of trade-offs (dynamic typing is slow but productive, the GIL limits parallelism but simplifies the ecosystem, gradual typing is unsound but practical) that individually look suboptimal but collectively enable an exceptionally wide range of use cases.

| Dimension | Python | Go |
|-----------|--------|-----|
| Type system strategy | Dynamic + gradual typing overlay | Static, structural, deliberately simple |
| Performance strategy | Two-language architecture (Python + C) | Single language, compiled to native |
| Concurrency strategy | GIL (transitioning to free-threaded) | Goroutines + channels (from day one) |
| Memory strategy | Reference counting + cyclic GC | Concurrent mark-sweep GC |
| Extension strategy | C API, PyO3, pybind11 | cgo (deliberately limited) |
| Philosophy | "Practicality beats purity" | "Less is exponentially more" |

Go deliberately limits extensibility (no operator overloading, limited metaprogramming) to ensure static analyzability and fast compilation. Python maximizes extensibility (full operator overloading, metaclasses, import hooks) and accepts the tooling complexity that results. Both approaches are internally coherent; they represent different answers to the fundamental extensibility-analyzability trade-off identified in Section 4.2.

### 6.2 Python vs. Rust: Productive Compromise vs. Safety Without Sacrifice

Rust's architecture, analyzed in the companion survey, is built on *safety without sacrifice* -- the ownership system, trait system, and unsafe boundary work together to provide memory safety without garbage collection overhead [Rust Survey, Cross-Layer Synthesis]. Python's architecture accepts runtime overhead (reference counting, dynamic dispatch, GIL) in exchange for developer productivity and ecosystem reach.

| Dimension | Python | Rust |
|-----------|--------|------|
| Memory management | Ref counting + cyclic GC (runtime) | Ownership + borrowing (compile-time) |
| Type safety | Gradual, unsound, optional | Static, sound, mandatory |
| Concurrency safety | GIL (historically) / runtime locks | Send + Sync (compile-time) |
| Performance model | Interpreted + compiled extensions | Compiled, zero-cost abstractions |
| Metaprogramming | Runtime (metaclasses, descriptors) | Compile-time (macros, const fn) |
| Learning curve | Shallow entry, deep mastery | Steep entry, productive mastery |

The most illuminating comparison is in how each language handles the two-language problem. Python accepts it (the scientific stack is Python + C/Fortran/Rust). Rust eliminates it (a single language provides both high-level ergonomics and low-level performance). But Python's acceptance of the two-language architecture enables a larger ecosystem: any compiled language can participate as a backend (NumPy in C, SciPy in Fortran, Polars in Rust, PyTorch in C++), while Rust's single-language approach requires everything to be written in Rust.

### 6.3 Where Python Is Unique

Python's architectural position is distinctive among mainstream languages in three ways:

1. **The gradual typing bridge**: No other language has successfully retrofitted a comprehensive static type system onto a dynamically typed runtime without altering runtime semantics. TypeScript alters JavaScript's semantics (through class desugaring, enum compilation, etc.). Python's type annotations are purely metadata.

2. **The protocol-based scientific ecosystem**: No other language has achieved comparable library interoperability through layered structural protocols (buffer protocol, array protocols, array API standard) that enable zero-copy data sharing across independently maintained libraries.

3. **The productive-compromise philosophy**: Most languages are designed around a strong organizing principle (Rust: safety, Go: simplicity, Haskell: purity). Python is designed around the absence of a single organizing principle -- "practicality beats purity" is itself a meta-principle that permits trade-offs other languages refuse.

## 7. Open Architectural Questions

### 7.1 Can Free-Threading Become the Default?

PEP 779's criteria for Phase III (free-threading as default) include acceptable single-threaded overhead, sufficient ecosystem coverage, and ideally a unified stable ABI. The single-threaded penalty (currently 5-10%) is approaching the acceptable threshold. Ecosystem coverage is progressing but the long tail of C extensions remains. The unified ABI is the hardest problem: it requires extensions compiled once to work with both GIL-enabled and free-threaded interpreters, which demands resolving differences in object header layout and reference counting semantics.

### 7.2 Can the JIT Close the Performance Gap?

The copy-and-patch JIT (PEP 744) achieves 5-9% speedup in Python 3.14-3.15 [Paper 6, Section 4.2.3]. The long-term question is whether it can reach the 2-5x range needed to meaningfully narrow the gap with compiled languages. This requires advanced optimizations -- loop unrolling, escape analysis, register allocation across traces, inlining -- that the current infrastructure does not yet support. The answer determines whether Python's two-language architecture remains necessary or begins to dissolve.

### 7.3 Will Gradual Typing Become Effectively Mandatory?

As type annotations become standard in production codebases, libraries, and tools, the practical cost of writing untyped Python increases (poorer IDE experience, incompatibility with mypyc optimization, reduced static bug detection). The question is whether Python reaches a tipping point where untyped code becomes a liability, effectively making gradual typing mandatory despite its optional status. This would represent a cultural shift in the "consenting adults" philosophy [Paper 9, Section 9.3].

### 7.4 Can Packaging Converge?

The packaging ecosystem has been converging around `pyproject.toml` (PEP 621), the PEP 517 build protocol, and uv as the performance standard for package management [Paper 7]. The open questions are lockfile standardization (no PEP yet accepted), the conda/pip divide (native library dependencies remain outside pip's scope), and whether a single tool can serve all use cases (scripts, libraries, applications, scientific computing, ML pipelines).

### 7.5 What Happens When Python Has Two Concurrency Models?

The coexistence of GIL-enabled and free-threaded builds creates a period where Python effectively has two concurrency models. Code written for the GIL-enabled build may rely on implicit atomicity guarantees that do not hold in the free-threaded build. The educational burden of teaching shared-memory concurrency to Python's broad user base is substantial [Paper 5, Section 11.2]. The structured concurrency movement (`asyncio.TaskGroup`, inspired by trio's nurseries [Paper 5, Section 5.4]) provides one answer, but the threading world has no equivalent "thread nursery" in the stdlib [Paper 5, Section 11.6].

## 8. Conclusion

Python's architecture is a system of productive compromises. Duck typing enables unparalleled flexibility at the cost of runtime overhead. Reference counting provides deterministic finalization at the cost of the GIL. The GIL simplifies the ecosystem at the cost of parallelism. C extensions compensate for performance at the cost of coupling. Gradual typing bridges the static and dynamic worlds at the cost of unsoundness. The standard library provides universality at the cost of agility. Each compromise is locally suboptimal and globally essential.

The seven interaction chains traced in this paper demonstrate that these compromises are not independent. They form a connected system where each design decision constrains and enables decisions at other layers. Understanding Python deeply means understanding these connections -- why the GIL exists (because of reference counting), why reference counting exists (because of the C extension API), why the C API exposes implementation details (because of the performance gap), why the performance gap exists (because of dynamic typing), and why dynamic typing persists (because it is the foundation of Python's productivity and reach).

The free-threaded transition is the most significant test this architecture has faced. By removing the GIL -- the single artifact that more than any other held the architecture together -- PEP 703 reveals every hidden dependency, every implicit assumption, every load-bearing compromise. The fact that this transition is proceeding incrementally, with backward compatibility, with automatic fallback, and with years-long migration timelines, demonstrates that the community has learned the lessons of the Python 2-to-3 transition.

Python's architecture is not optimal for any single dimension -- not for performance, not for safety, not for concurrency, not for static analysis, not for simplicity. It is optimized for the interaction between all of them: the productive compromise that enables a single language to serve as the world's most widely adopted programming language across domains as different as machine learning, web development, scientific computing, and scripting. That is the architecture this survey has documented.

## References

### Survey Papers (This Series)

1. "CPython Internals: From PEG Parser to Adaptive Interpreter" (python-cpython-internals.md)
2. "Python's Memory Model and Garbage Collection: Reference Counting, Generational GC, and the Free-Threaded Future" (python-memory-model-gc.md)
3. "Python's Type System: From Duck Typing to Gradual Typing and Beyond" (python-type-system-gradual-typing.md)
4. "Python's Data Model and Metaprogramming: Descriptors, Metaclasses, and the Object Protocol" (python-data-model-metaprogramming.md)
5. "Python's Concurrency Model: The GIL, asyncio, and the Free-Threaded Future" (python-concurrency-model.md)
6. "Python Performance Engineering: From Profiling to JIT Compilation" (python-performance-engineering.md)
7. "Python's Module System and Packaging Ecosystem: From Import Machinery to Modern Distribution" (python-module-packaging.md)
8. "Python's Scientific Computing Architecture: From Buffer Protocol to ML Frameworks" (python-scientific-computing.md)
9. "Python's Design Philosophy and Language Evolution: From ABC to Free-Threaded Python" (python-design-philosophy-evolution.md)

### Companion Survey Series

10. "Go's Architecture of Deliberate Constraints: Cross-Layer Synthesis" (go/go-cross-layer-synthesis.md)
11. "Cross-Layer Synthesis: Rust's Architecture of Safety Without Sacrifice" (rust/rust-cross-layer-synthesis.md)

### External References

12. Siek, J. and Taha, W. "Gradual Typing for Functional Languages." Scheme and Functional Programming Workshop, 2006.
13. Bacon, D., Cheng, P., and Rajan, V.T. "A Unified Theory of Garbage Collection." OOPSLA 2004.
14. Choi, J., Shull, T., and Torrellas, J. "Biased Reference Counting: Minimizing Atomic Operations in Garbage Collection." PACT 2018.
15. Shannon, M. "PEP 659 -- Specializing Adaptive Interpreter." 2021. https://peps.python.org/pep-0659/
16. Gross, S. "PEP 703 -- Making the Global Interpreter Lock Optional in CPython." 2023. https://peps.python.org/pep-0703/
17. Noronha, R. et al. "An empirical study of CPython's interpretation overhead." Journal of Systems and Software, 2021.
18. Bezanson, J. et al. "Julia: A Fresh Approach to Numerical Computing." SIAM Review, 2017.
19. Van Rossum, G. "PEP 3000 -- Python 3000." 2006. https://peps.python.org/pep-3000/
20. Peters, T. "PEP 20 -- The Zen of Python." 2004. https://peps.python.org/pep-0020/
21. Xu, H. and Kjolstad, F. "Copy-and-Patch Compilation." OOPSLA 2021.
22. Oliphant, T. "PEP 3118 -- Revising the Buffer Protocol." 2007. https://peps.python.org/pep-3118/

## Practitioner Resources

### Reading This Survey

- **Sequential**: Read Papers 1-9 in order, then this synthesis. Builds from implementation details to cross-layer understanding.
- **By interest**: Start with Paper 5 (Concurrency) for the GIL story, Paper 8 (Scientific Computing) for the two-language architecture, or Paper 9 (Philosophy) for the cultural context. Then read this synthesis for how they connect.
- **Quick overview**: Read this synthesis alone for the cross-layer thesis, then dive into individual papers as needed.

### Key Architectural Decisions for Python Developers

1. **Performance**: Think in terms of the optimization boundary. Minimize Python/C boundary crossings per unit of useful work. Use vectorized operations (NumPy), compiled extensions (Cython, Rust via PyO3), or JIT compilation (Numba) for numerical hot paths.
2. **Concurrency**: Choose based on workload profile. I/O-bound: asyncio or threading. CPU-bound (pre-3.13): multiprocessing. CPU-bound (3.13+): free-threaded Python or subinterpreters. See Paper 5, Section 10.2 for the full decision framework.
3. **Typing**: Adopt gradual typing for all new production code. Use Protocols (PEP 544) for duck typing interfaces. Configure pyright or mypy in CI. Consider mypyc for performance-critical modules with full type coverage.
4. **Packaging**: Use `pyproject.toml` with PEP 621 metadata. Choose uv for speed, Poetry for workflow integration, or pip for simplicity. For compiled extensions, use maturin (Rust), scikit-build-core (CMake), or setuptools (C/Fortran).
5. **Free-threading**: Begin testing critical code paths with `PYTHON_GIL=0` on Python 3.14+. Audit C extensions for thread safety. Watch PEP 779's Phase III criteria for the timeline toward free-threading as default.
