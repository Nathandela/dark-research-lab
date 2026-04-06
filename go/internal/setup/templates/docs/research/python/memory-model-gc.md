---
title: "Python's Memory Model and Garbage Collection: Reference Counting, Generational GC, and the Free-Threaded Future"
date: 2026-03-25
summary: A comprehensive survey of CPython's memory management internals -- from PyObject layout and reference counting through the generational cyclic garbage collector, pymalloc's arena/pool/block hierarchy, and object caching strategies, to the biased reference counting and deferred reference counting mechanisms that enable GIL-free execution under PEP 703.
keywords: [python, memory-model, garbage-collection, reference-counting, pymalloc]
---

# Python's Memory Model and Garbage Collection: Reference Counting, Generational GC, and the Free-Threaded Future

*2026-03-25*

## Abstract

CPython, the reference implementation of Python, employs a hybrid memory management strategy that combines immediate reference counting with a generational cycle-detecting garbage collector. Every Python object carries an embedded reference count that triggers deterministic deallocation when it reaches zero, while a supplementary tracing collector handles the reference cycles that pure reference counting cannot resolve. Beneath this dual-strategy reclamation system lies pymalloc, a specialized small-object allocator organized into a three-level arena/pool/block hierarchy optimized for the allocation patterns typical of Python programs -- frequent creation and rapid destruction of small, short-lived objects.

This survey examines CPython's memory management at PhD depth across eight interconnected dimensions: (1) the `PyObject` and `PyVarObject` memory layout that underpins all Python objects; (2) the reference counting protocol including `Py_INCREF`/`Py_DECREF` semantics, owned vs. borrowed references, and the zero-refcount deallocation path; (3) the cyclic garbage collector's generational design, `tp_traverse`-based cycle detection, and threshold-driven scheduling; (4) pymalloc's arena, pool, and block architecture alongside the `PyMem_*` API layer hierarchy; (5) object caching and interning strategies including the small integer cache, string interning, `__slots__`, and free lists; (6) weak references and their interaction with the garbage collector; (7) the free-threaded Python initiative (PEP 703) and its biased/deferred reference counting schemes; and (8) memory profiling and debugging tools. The analysis traces each mechanism from its C-level implementation through its observable behavior at the Python level, situates CPython's design within the broader landscape of managed language runtimes (PyPy, GraalPy, JVM, CLR), and identifies the open problems confronting Python's memory management as it transitions toward a GIL-free future.

---

## 1. Introduction

### 1.1 Problem Statement

Memory management is the hidden infrastructure of every programming language runtime. Its design determines not only whether a program leaks memory or crashes from use-after-free errors, but also the fundamental performance characteristics of the language: allocation throughput, deallocation latency, cache behavior, and scalability across threads. For Python -- a language whose design prioritizes programmer productivity over bare-metal performance -- the memory management system must satisfy a particularly demanding set of constraints. It must be invisible to the programmer in the common case, deterministic enough to support resource management idioms (context managers, file handles, database connections), efficient enough for workloads ranging from scripting to data science, and extensible enough to support the vast ecosystem of C extensions that give Python its reach.

CPython's answer to these constraints is a layered architecture. At the foundation, pymalloc provides a custom allocator optimized for the small, numerous objects that dominate Python's allocation profile. Above it, a reference counting system provides immediate, deterministic reclamation of most objects. A cyclic garbage collector supplements reference counting to handle the reference cycles that are both common in Python (mutual references between objects, self-referencing data structures) and fundamentally unresolvable by reference counting alone. Object caching and interning strategies amortize allocation costs for frequently used immutable values. And weak references provide a mechanism for observing object lifetimes without preventing collection.

This architecture has served CPython well for over three decades. But the arrival of free-threaded Python (PEP 703), which removes the Global Interpreter Lock to enable true multi-threaded parallelism, demands a fundamental rethinking of reference counting semantics, garbage collector design, and memory allocator thread safety. Understanding CPython's current memory model -- and the pressures driving its evolution -- requires examining each layer in detail.

### 1.2 Scope

This survey is CPython-centric, focusing on the reference implementation as of Python 3.13/3.14 (2024-2026). PyPy and GraalPy are discussed comparatively in Section 8, but the primary analysis concerns CPython's C-level implementation. The treatment is intended at PhD academic depth: we examine source-level data structures, algorithm complexity, and design trade-offs rather than limiting ourselves to user-facing API descriptions.

### 1.3 Key Definitions

**Reference count**: An integer field embedded in every Python object header (`ob_refcnt`) that tracks the number of active pointers to that object. When the count reaches zero, the object is immediately deallocated.

**Cyclic garbage**: A set of objects that reference each other in a cycle, maintaining non-zero reference counts despite being unreachable from the program's root set. Such objects cannot be reclaimed by reference counting alone.

**Generational hypothesis**: The empirical observation that most dynamically allocated objects die young -- they become unreachable shortly after creation [Ungar 1984]. Generational garbage collectors exploit this by collecting young objects more frequently.

**pymalloc**: CPython's built-in small-object allocator, implementing a three-level hierarchy (arena -> pool -> block) optimized for allocations of 512 bytes or fewer.

**Immortal object**: An object whose reference count is set to a sentinel value (PEP 683, Python 3.12+) such that `Py_INCREF` and `Py_DECREF` operations are no-ops, eliminating cache line invalidation for frequently accessed immutable objects.

**Free-threaded Python**: The experimental build mode (PEP 703, Python 3.13+) that removes the Global Interpreter Lock, replacing standard reference counting with biased and deferred reference counting schemes to maintain memory safety without global serialization.

---

## 2. Foundations

### 2.1 The Duality of Reference Counting and Tracing Collection

Bacon, Cheng, and Rajan's influential paper "A Unified Theory of Garbage Collection" (2004) demonstrated that reference counting and tracing garbage collection are not fundamentally different approaches but duals of one another [Bacon et al. 2004]. Tracing collectors determine liveness by computing the transitive closure of the root set (identifying what is alive); reference counting determines liveness by tracking the complement (identifying when something becomes dead). Every practical garbage collector is a hybrid that sits somewhere on the spectrum between these two extremes.

CPython's design is an explicit hybrid. Reference counting handles the common case -- the vast majority of objects have short, acyclic lifetimes and are reclaimed immediately when their last reference disappears. The cyclic garbage collector handles the pathological case -- reference cycles among container objects that maintain non-zero reference counts despite being unreachable. This hybrid approach trades some memory overhead (the per-object reference count field, the GC header on container objects) for the deterministic deallocation behavior that Python programmers have come to rely upon.

### 2.2 Memory Allocation in Managed Runtimes

Managed language runtimes face a common allocation challenge: programs create and destroy enormous numbers of small objects. A typical Python program may allocate millions of objects per second, most of which survive for only a few microseconds. General-purpose system allocators (`malloc`/`free`) are designed for a different workload -- larger, longer-lived allocations with less predictable size distributions -- and suffer from fragmentation, lock contention, and metadata overhead when confronted with Python's allocation profile.

The standard solution is a custom allocator layered atop the system allocator. The JVM uses a bump-pointer allocator within thread-local allocation buffers (TLABs). Go uses a size-segregated allocator with span-based management. CPython uses pymalloc, which pre-allocates memory in large chunks (arenas) and carves them into fixed-size blocks organized by size class. Each approach optimizes for the specific allocation patterns of its language.

### 2.3 The GIL and Memory Safety

The Global Interpreter Lock (GIL) is CPython's mechanism for ensuring thread safety of the reference counting system. Because `Py_INCREF` and `Py_DECREF` are non-atomic operations in the default build, concurrent execution of Python bytecode by multiple threads would corrupt reference counts, leading to use-after-free errors or memory leaks. The GIL serializes all Python bytecode execution, ensuring that only one thread manipulates reference counts at a time.

The GIL's simplicity is both its strength and its limitation. It makes single-threaded reference counting fast (no atomic operations, no memory barriers) and makes C extension development relatively straightforward (extensions can assume single-threaded access to Python objects while holding the GIL). But it prevents Python from exploiting multi-core processors for CPU-bound workloads, a limitation that has driven the free-threaded Python initiative.

---

## 3. Taxonomy of Python Memory Management Mechanisms

### 3.1 Classification Framework

Python's memory management mechanisms can be organized along two orthogonal axes: the *layer* of the runtime they operate at (allocator, reclamation, optimization) and the *scope* of objects they affect (all objects, container objects only, specific types).

| Mechanism | Layer | Scope | Deterministic? | Handles Cycles? |
|---|---|---|---|---|
| pymalloc | Allocation | All small objects (<=512B) | N/A | N/A |
| Reference counting | Reclamation | All objects | Yes | No |
| Cyclic GC | Reclamation | Container objects | No | Yes |
| Immortalization | Optimization | Builtin singletons, types | N/A | N/A |
| Small int cache | Optimization | Integers -5 to 256 | N/A | N/A |
| String interning | Optimization | Qualifying strings | N/A | N/A |
| Free lists | Optimization | Specific types (tuple, list, dict, float) | N/A | N/A |
| `__slots__` | Optimization | User-defined classes | N/A | N/A |
| Weak references | Observation | Weakly-referenceable objects | N/A | N/A |

### 3.2 Interaction Map

These mechanisms do not operate in isolation. The cyclic GC depends on reference counting to handle the common case, and its `tp_clear` implementations trigger cascading reference count decrements. Immortalized objects bypass both reference counting and garbage collection. Free lists interact with pymalloc by recycling objects at the Python level before they reach the allocator. Weak references register callbacks that fire during the garbage collector's finalization phase. Understanding any single mechanism requires understanding its interactions with the others.

---

## 4. Object Memory Layout

### 4.1 Theory

Every Python object, regardless of type, begins with a common header defined by the `PyObject` struct. This header is the foundation of CPython's polymorphic object system: all object pointers can be cast to `PyObject *`, enabling type-generic operations (reference counting, type checking, attribute lookup) without knowledge of the object's concrete type.

### 4.2 Evidence: The PyObject and PyVarObject Headers

The `PyObject` header, defined in `Include/object.h`, contains two fields in a release build:

```c
typedef struct _object {
    Py_ssize_t ob_refcnt;    // Reference count
    PyTypeObject *ob_type;   // Pointer to the type object
} PyObject;
```

In debug builds (`Py_TRACE_REFS`), additional fields are prepended for a doubly-linked list of all live objects, enabling leak detection:

```c
typedef struct _object {
    struct _object *_ob_next;   // Debug only
    struct _object *_ob_prev;   // Debug only
    Py_ssize_t ob_refcnt;
    PyTypeObject *ob_type;
} PyObject;
```

Variable-length objects (lists, tuples, strings, bytes) extend `PyObject` with an `ob_size` field:

```c
typedef struct {
    PyObject ob_base;
    Py_ssize_t ob_size;        // Number of items (not bytes)
} PyVarObject;
```

On a 64-bit system, the `PyObject` header consumes 16 bytes (8 for `ob_refcnt`, 8 for `ob_type`). `PyVarObject` adds another 8 bytes for `ob_size`, totaling 24 bytes of header before any instance-specific data. This overhead is significant: a Python `int` that holds the value 42 consumes 28 bytes (24 header + 4 for the digit), compared to 4 or 8 bytes for a C integer.

### 4.3 Implementation: Header Macros and Access Patterns

CPython provides macros for header initialization and field access:

- `PyObject_HEAD`: Expands to `ob_refcnt` + `ob_type` (for fixed-size objects)
- `PyObject_VAR_HEAD`: Expands to `PyObject_HEAD` + `ob_size` (for variable-size objects)
- `Py_TYPE(op)`: Returns `((PyObject *)(op))->ob_type`
- `Py_REFCNT(op)`: Returns `((PyObject *)(op))->ob_refcnt`
- `Py_SIZE(op)`: Returns `((PyVarObject *)(op))->ob_size`

Direct field access is discouraged across all modern CPython versions. The macro-based API allows internal layout changes (such as the free-threaded build's expanded header) without breaking C extensions compiled against the stable ABI.

### 4.4 Object Size Calculation

The `__sizeof__` method and `sys.getsizeof()` function expose object memory consumption at the Python level:

```python
import sys

sys.getsizeof(42)           # 28 bytes (int)
sys.getsizeof(3.14)         # 24 bytes (float)
sys.getsizeof("hello")      # 54 bytes (str, compact ASCII)
sys.getsizeof([1, 2, 3])    # 88 bytes (list, not counting elements)
sys.getsizeof((1, 2, 3))    # 64 bytes (tuple)
sys.getsizeof({})            # 64 bytes (empty dict)
```

`sys.getsizeof()` adds the garbage collector header overhead (typically 16 bytes for the `PyGC_Head` on container objects) to the value returned by `__sizeof__`. It reports only the *shallow* size of the object -- the memory directly allocated for the object itself, not the memory consumed by objects it references.

### 4.5 Free-Threaded Build Header Changes

Under PEP 703, the `PyObject` header expands significantly to accommodate thread-safe reference counting:

```c
// Free-threaded build (conceptual layout)
typedef struct _object {
    uintptr_t ob_tid;         // Owning thread ID (8 bytes on 64-bit)
    uint16_t _padding;
    uint8_t ob_flags;
    uint8_t ob_gc_bits;       // GC tracking bits
    uint32_t ob_ref_local;    // Thread-local reference count
    Py_ssize_t ob_ref_shared; // Shared (atomic) reference count
    PyTypeObject *ob_type;
} PyObject;
```

This expands the per-object header from 16 bytes to approximately 24-32 bytes, a non-trivial increase in memory overhead that is offset by the elimination of the GIL's scalability bottleneck.

### 4.6 Strengths and Limitations

**Strengths**: The uniform `PyObject` header enables CPython's remarkably flexible dynamic type system. Any function that accepts a `PyObject *` can operate on any Python object. The reference count field in the header enables immediate deallocation without a separate bookkeeping structure.

**Limitations**: The per-object overhead is substantial. A `PyObject` header consumes 16 bytes even for a boolean value that semantically requires a single bit. This overhead is a fundamental consequence of CPython's design choice to represent every value as a heap-allocated object, and it drives the caching and interning optimizations discussed in Section 8.

---

## 5. Reference Counting

### 5.1 Theory

Reference counting is the oldest automatic memory management technique, dating to Collins (1960). The principle is simple: maintain a count of the number of pointers to each object; when the count reaches zero, the object is garbage and may be immediately reclaimed. The elegance of reference counting lies in its incrementality -- each pointer operation performs a bounded amount of work -- and its determinism -- objects are freed at the precise moment they become unreachable.

The well-known limitations of reference counting are equally fundamental. First, maintaining the count imposes overhead on every pointer assignment (one increment, one decrement, and potentially one deallocation). Second, reference counting cannot reclaim cyclic garbage -- objects that reference each other in a cycle maintain non-zero reference counts even when the entire cycle is unreachable. Third, reference count updates have poor cache behavior because they mutate the object header on every pointer operation, invalidating cache lines.

### 5.2 Evidence: Py_INCREF and Py_DECREF

CPython's reference counting protocol is implemented through two fundamental macros defined in `Include/object.h`:

**Py_INCREF(op)**: Increments the reference count of `op`. In the default (GIL-protected) build, this is a simple non-atomic increment:

```c
static inline void Py_INCREF(PyObject *op) {
    // Skip if immortal (Python 3.12+)
    if (_Py_IsImmortal(op)) {
        return;
    }
    op->ob_refcnt++;
}
```

**Py_DECREF(op)**: Decrements the reference count. If the count reaches zero, the object's type-specific deallocator is invoked:

```c
static inline void Py_DECREF(PyObject *op) {
    if (_Py_IsImmortal(op)) {
        return;
    }
    if (--op->ob_refcnt == 0) {
        _Py_Dealloc(op);
    }
}
```

The `_Py_Dealloc` function invokes the type's `tp_dealloc` slot, which typically frees the object's instance-specific data, decrements reference counts of objects it owns (potentially triggering cascading deallocations), and returns the memory to the allocator.

### 5.3 Owned vs. Borrowed References

The distinction between owned and borrowed references is the central discipline of CPython's C API. An **owned reference** is a reference for which the holder is responsible for calling `Py_DECREF` when the reference is no longer needed. A **borrowed reference** is one where some other code owns the reference, and the borrower must not call `Py_DECREF` (and must not use the reference after the owner may have released it).

**Functions that return owned references** (caller must decref): `PyObject_GetAttrString`, `PySequence_GetItem`, `PyDict_GetItemWithError`, `Py_BuildValue`.

**Functions that return borrowed references** (caller must not decref): `PyList_GetItem`, `PyTuple_GetItem`, `PyDict_GetItem`, `PyList_GET_ITEM`.

**Functions that steal references** (callee assumes ownership): `PyList_SetItem`, `PyTuple_SetItem`, `PyModule_AddObject`.

Mismanaging owned vs. borrowed references is the single most common source of bugs in C extensions. A forgotten `Py_DECREF` on an owned reference causes a memory leak; an erroneous `Py_DECREF` on a borrowed reference causes a use-after-free. The subtlety is compounded by the fact that some API pairs behave inconsistently: `PyList_GetItem` returns a borrowed reference, but `PySequence_GetItem` (which may call the same underlying code) returns an owned reference.

### 5.4 The Deallocation Path

When `Py_DECREF` drives a reference count to zero, the following sequence occurs:

1. `_Py_Dealloc(op)` is called, which invokes `Py_TYPE(op)->tp_dealloc(op)`.
2. The `tp_dealloc` handler performs type-specific cleanup:
   - For containers (list, dict, set): iterates over contained references, calling `Py_XDECREF` on each. This may trigger recursive deallocations.
   - For objects with `__del__` (mapped to `tp_finalize` per PEP 442): the finalizer is called before reference clearing.
   - For objects tracked by the cyclic GC: `PyObject_GC_UnTrack` removes them from the GC's tracking lists.
3. The memory is returned to the allocator (pymalloc or system `free`).

A critical subtlety: deallocation can be *re-entrant*. When a container's `tp_dealloc` decrements the reference counts of its contained objects, those objects may themselves reach zero and trigger their own deallocation. This creates a chain of deallocations that can be arbitrarily deep, potentially exhausting the C stack for deeply nested structures. CPython mitigates this with a "trashcan" mechanism (`Py_TRASHCAN_SAFE_BEGIN`/`Py_TRASHCAN_SAFE_END`) that defers nested deallocations beyond a configurable depth.

### 5.5 Immortal Objects (PEP 683)

Python 3.12 introduced immortal objects (PEP 683) to address a specific performance problem: frequently accessed immutable objects (`None`, `True`, `False`, small integers, type objects) have their reference counts continuously incremented and decremented, causing cache line invalidation even though these objects are never actually deallocated.

Immortal objects have their `ob_refcnt` set to `_Py_IMMORTAL_REFCNT`, a value with the two topmost available bits set. The `_Py_IsImmortal` check tests the top bit:

```c
static inline int _Py_IsImmortal(PyObject *op) {
    return (op->ob_refcnt & _Py_IMMORTAL_BIT) != 0;
}
```

When an object is immortal, both `Py_INCREF` and `Py_DECREF` become no-ops. The reference count never changes, the cache line is never invalidated, and the object is never deallocated (except during interpreter shutdown).

The performance impact of immortalization is carefully measured: a naive implementation imposed approximately 4% overhead due to the additional branch in every `Py_INCREF`/`Py_DECREF`. Optimizations (using 32-bit comparison tricks that enable efficient register-based checks) reduced this to approximately performance-neutral, within the 2% acceptable threshold established at the 2022 Language Summit.

### 5.6 Reference Counting in C Extensions

C extensions are the primary consumers of the reference counting API, and the correctness burden falls entirely on the extension author. Common patterns include:

```c
// Correct: create new object, manipulate, return owned reference
PyObject *result = PyLong_FromLong(42);  // New reference (owned)
if (result == NULL) return NULL;          // Error handling
// ... use result ...
return result;  // Transfer ownership to caller

// Correct: borrowed reference from container, incref to keep
PyObject *item = PyList_GetItem(list, 0);  // Borrowed
Py_INCREF(item);                            // Now owned
// ... safe to use item even if list is modified ...
Py_DECREF(item);                            // Release when done

// Bug: forgetting to decref on error path
PyObject *a = PyLong_FromLong(1);
PyObject *b = PyLong_FromLong(2);  // If this fails, 'a' is leaked
if (b == NULL) {
    Py_DECREF(a);  // Must clean up 'a' before returning
    return NULL;
}
```

### 5.7 Strengths and Limitations

**Strengths**: (1) Deterministic deallocation enables resource management patterns (files closed when the last reference disappears, not at some future GC cycle). (2) Incremental work: each operation does bounded work, avoiding GC pauses. (3) Excellent locality for short-lived objects: allocation and deallocation touch only the object itself. (4) Simple mental model for C extension authors (once owned/borrowed is understood).

**Limitations**: (1) Cannot handle cyclic garbage. (2) Per-pointer-operation overhead (increment + decrement on every assignment). (3) Cache-unfriendly mutation of object headers. (4) Cascading deallocation can create latency spikes. (5) Thread-unsafe without the GIL or atomic operations.

---

## 6. Cyclic Garbage Collector

### 6.1 Theory

The cyclic garbage collector exists to solve reference counting's fundamental blind spot: reference cycles. Consider two objects A and B where A references B and B references A. If no external references to either object exist, both have a reference count of 1 (from the other object in the cycle) and will never be reclaimed by reference counting alone.

CPython's cycle collector is a tracing collector that operates only on "container" objects -- objects that can reference other objects (lists, dicts, sets, class instances, etc.). Non-container objects (ints, floats, strings) cannot participate in reference cycles and are excluded from GC tracking, reducing the collector's work.

### 6.2 Evidence: The Generational Design

CPython's GC implements a generational strategy based on the weak generational hypothesis. As of Python 3.12+, the collector uses two logical generations: young and old.

**Young generation**: Contains all newly allocated container objects. Collection is triggered when the allocation count minus deallocation count exceeds `threshold0` (default: 700).

**Old generation**: Contains objects that survived at least one young generation collection. The old generation is divided into two sublists -- `pending` (unscanned) and `visited` (recently scanned) -- that are processed incrementally.

The default thresholds are configured via `gc.get_threshold()`:

```python
import gc
gc.get_threshold()  # (700, 10, 10)
# threshold0 = 700: triggers young gen collection
# threshold1 = 10: controls old gen scan frequency
# threshold2 = 10: currently ignored in modern CPython
```

### 6.3 The Cycle Detection Algorithm

The cycle detection algorithm operates in three phases, using the `tp_traverse` slot to enumerate each container's references:

**Phase 1 -- Initialize gc_refs**: For each object in the candidate set, a temporary field `gc_refs` is initialized to the object's current reference count (`ob_refcnt`). This field is stored by reusing bits in the `_gc_prev` pointer of the GC header (a "fat pointer" technique that avoids allocating additional per-object storage).

**Phase 2 -- Subtract internal references**: The collector iterates over every object in the candidate set and calls its `tp_traverse` function with a visitor callback that decrements `gc_refs` for each referenced object that is also in the candidate set. After this phase, `gc_refs` reflects only *external* references -- references from outside the candidate set.

```c
// Conceptual visitor callback during Phase 2
static int visit_decref(PyObject *op, void *data) {
    if (IS_TRACKED(op)) {
        gc_refs(op)--;
    }
    return 0;
}
```

**Phase 3 -- Identify unreachable objects**: Objects with `gc_refs == 0` are tentatively marked unreachable and moved to an "unreachable" list. However, `gc_refs == 0` does not guarantee unreachability: another object in the candidate set with `gc_refs > 0` (reachable from outside) might reference the tentatively unreachable object. The collector therefore traverses each object with `gc_refs > 0`, using `tp_traverse` to "rescue" any tentatively unreachable objects it can reach, moving them back to the reachable set. This is effectively a breadth-first search from the externally-referenced root set.

The algorithm's elegance lies in its efficiency: it requires no recursion, no additional memory proportional to the number of objects or pointers, and visits each object a bounded number of times. The time complexity is O(N + E) where N is the number of tracked objects and E is the number of inter-object references.

### 6.4 The tp_traverse Protocol

Every container type must implement `tp_traverse`, a function that calls a visitor callback for each object the container directly references. For example, a list's `tp_traverse`:

```c
static int list_traverse(PyListObject *o, visitproc visit, void *arg) {
    Py_ssize_t i;
    for (i = Py_SIZE(o); --i >= 0; ) {
        Py_VISIT(o->ob_item[i]);
    }
    return 0;
}
```

The `Py_VISIT` macro encapsulates the visitor call with null-checking:

```c
#define Py_VISIT(op) \
    do { \
        if (op) { \
            int vret = visit((PyObject *)(op), arg); \
            if (vret) return vret; \
        } \
    } while (0)
```

Types that support GC tracking must also set `Py_TPFLAGS_HAVE_GC` in their `tp_flags` and implement `tp_clear` for breaking reference cycles during collection.

### 6.5 Finalization and PEP 442

The finalization of unreachable objects follows a carefully ordered protocol, refined by PEP 442 (Safe Object Finalization, Python 3.4):

1. **Weak reference callbacks**: For reachable weak references pointing to unreachable objects, callbacks are invoked. The weak reference itself receives `None` for its referent.
2. **Finalizers (tp_finalize)**: Objects with `__del__` methods (mapped to the `tp_finalize` slot) have their finalizers called. Crucially, PEP 442 ensures the finalizer receives a *valid, alive* object -- internal references have not yet been cleared.
3. **Resurrection check**: After finalization, the collector re-traverses the unreachable set. If a finalizer has resurrected an object (by storing a reference to it in a reachable object), the entire cycle is moved back to the reachable set and collection is aborted for that cycle.
4. **Legacy finalizers (tp_del)**: Objects using the deprecated `tp_del` slot are moved to `gc.garbage` rather than being collected, preserving backward compatibility.
5. **Reference clearing (tp_clear)**: For confirmed unreachable objects, `tp_clear` is called to break internal references. This triggers cascading `Py_XDECREF` calls that actually deallocate the objects via the reference counting mechanism.

The PEP 442 protocol guarantees that each object's finalizer is called exactly once, solving the "resurrection problem" that previously made finalizers on cyclic objects unsafe.

### 6.6 The gc Module Interface

The `gc` module exposes the collector's state and controls to Python code:

```python
import gc

gc.collect()              # Force a full collection; returns number of unreachable objects found
gc.collect(generation=0)  # Collect only the young generation

gc.get_threshold()        # (700, 10, 10) -- allocation thresholds
gc.set_threshold(1000, 15, 15)  # Tune thresholds

gc.get_count()            # (alloc_count - dealloc_count, gen1_count, gen2_count)
gc.get_stats()            # Per-generation collection statistics

gc.disable()              # Disable automatic collection (reference counting still works)
gc.enable()               # Re-enable automatic collection

gc.get_objects()          # List of all tracked objects (expensive; debugging only)
gc.get_referrers(*objs)   # Objects that reference any of the given objects
gc.get_referents(*objs)   # Objects referenced by the given objects

gc.garbage                # List of uncollectable objects (with tp_del, pre-PEP 442)
gc.callbacks              # List of functions called before/after collection
```

### 6.7 Incremental Collection in the Old Generation

Starting from Python 3.12 development, CPython experimented with incremental collection of the old generation to reduce GC pause times for programs with large heaps. The approach divides the old generation into `pending` and `visited` sublists, processing only a portion of the old generation per collection cycle.

Each incremental step processes:
1. The entire young generation
2. A portion of the `pending` old generation (the least recently scanned objects)
3. The transitive closure of reachable objects discovered during scanning

The transitive closure computation is critical for correctness: if any object in a reference cycle is in the current increment, all objects in that cycle must be included to ensure complete cycle detection.

An incremental GC was briefly included in Python 3.13 development but was removed before release after benchmarks showed it caused a 40% regression in Sphinx documentation builds (1.28s -> 1.80s). The feature remains under development for Python 3.14+, with the core developers noting the need for "a bit more of a value proposition."

### 6.8 Strengths and Limitations

**Strengths**: (1) Handles cyclic garbage that reference counting cannot. (2) Generational design keeps most collections cheap by focusing on young objects. (3) O(N + E) complexity with no extra memory proportional to the graph size. (4) PEP 442 enables safe finalization of cyclic objects.

**Limitations**: (1) Non-deterministic timing -- collection happens at threshold crossings, not at predictable points. (2) Stop-the-world pauses scale with heap size for old generation collections. (3) Only tracks container objects -- a non-container type involved in a cycle (unusual but possible via C extensions) would not be collected. (4) The `tp_traverse`/`tp_clear` protocol places a correctness burden on type authors.

---

## 7. Memory Allocators

### 7.1 Theory

CPython's memory allocation subsystem is organized into three layers, each optimized for different allocation patterns. The design reflects a key insight: Python's allocation profile is dominated by small, short-lived objects, and a general-purpose allocator wastes significant time and space on these allocations.

### 7.2 The Three Allocation Domains

CPython defines three allocation domains, each backed by its own allocator:

| Domain | API | Default Allocator | Thread State | Use Case |
|---|---|---|---|---|
| `PYMEM_DOMAIN_RAW` | `PyMem_RawMalloc/Free` | System `malloc`/`free` | Not required | I/O buffers, non-Python data |
| `PYMEM_DOMAIN_MEM` | `PyMem_Malloc/Free` | pymalloc | Required | Python buffers, general data |
| `PYMEM_DOMAIN_OBJ` | `PyObject_Malloc/Free` | pymalloc | Required | Python object allocation |

A critical invariant: memory allocated in one domain must be freed in the same domain. Mixing domains (e.g., allocating with `PyObject_Malloc` and freeing with `PyMem_Free`) is undefined behavior and will be caught by debug hooks.

### 7.3 pymalloc: Arena, Pool, Block

pymalloc is CPython's small-object allocator, optimized for allocations of 512 bytes or fewer. It organizes memory into a three-level hierarchy:

**Arenas** (256 KiB on 32-bit, 1 MiB on 64-bit): The largest unit, obtained from the OS via `mmap()` (POSIX) or `VirtualAlloc()` (Windows). Each arena contains multiple pools. Arenas are linked in a doubly-linked list, sorted by the number of free pools (most-full first) to encourage memory reuse and eventual release of empty arenas back to the OS.

**Pools** (4 KiB, matching the system page size): Each pool is dedicated to a single size class. A pool contains a header at its start that tracks the free block list, the pool's size class index, and links to other pools of the same size class. Pools cycle through three states: `full` (no free blocks), `used` (some free blocks), and `empty` (all blocks free).

**Blocks** (8 to 512 bytes, in 8-byte increments): The atomic unit of allocation. pymalloc uses 64 size classes:

| Size Class Index | Block Size | Requested Size Range |
|---|---|---|
| 0 | 8 bytes | 1-8 bytes |
| 1 | 16 bytes | 9-16 bytes |
| 2 | 24 bytes | 17-24 bytes |
| ... | ... | ... |
| 63 | 512 bytes | 505-512 bytes |

Within a pool, blocks are managed via a singly-linked free list. When a block is freed, it is prepended to its pool's free list. A key optimization: blocks are not pre-linked when a pool is initialized. Instead, pymalloc lazily initializes blocks as they are first allocated, avoiding touching memory that may never be needed. This is consistent with pymalloc's philosophy of never touching memory until actually needed.

### 7.4 Allocation and Deallocation Paths

**Allocation** (`PyObject_Malloc(size)`):
1. If `size > 512`: delegate to `PyMem_RawMalloc` (system allocator).
2. Compute size class index: `(size - 1) >> 3` (equivalent to `ceil(size / 8) - 1`).
3. Find a pool for that size class in the `usedpools` table.
4. If a pool exists: pop a block from its free list and return it.
5. If no used pool exists: allocate a new pool from an arena (or allocate a new arena from the OS), initialize it for the requested size class, and return its first block.

**Deallocation** (`PyObject_Free(ptr)`):
1. Determine if `ptr` belongs to a pymalloc arena (by checking if the address falls within a known arena's range).
2. If yes: return the block to its pool's free list. If the pool transitions from `full` to `used`, link it into the `usedpools` table. If the pool becomes `empty`, return it to its arena. If the arena becomes fully empty, return it to the OS.
3. If no (large allocation): delegate to `PyMem_RawFree`.

### 7.5 Arena Release Policy

A common misconception is that pymalloc never returns memory to the OS. In fact, pymalloc returns empty arenas to the OS, but this happens only when *every pool* in an arena becomes empty. Because pools within an arena serve different size classes, fragmentation can prevent arenas from ever becoming completely empty, leading to the appearance of a "memory leak" in long-running processes.

The arena sorting strategy (most-full arenas first) is designed to mitigate this: by preferring allocations from nearly-full arenas, pymalloc concentrates usage and increases the probability that sparsely-used arenas drain completely.

### 7.6 PYTHONMALLOC Configuration

The `PYTHONMALLOC` environment variable controls which allocators back each domain:

| Value | Raw Domain | Mem Domain | Obj Domain |
|---|---|---|---|
| `pymalloc` (default) | system `malloc` | pymalloc | pymalloc |
| `pymalloc_debug` | `malloc` + debug | pymalloc + debug | pymalloc + debug |
| `malloc` | system `malloc` | system `malloc` | system `malloc` |
| `malloc_debug` | `malloc` + debug | `malloc` + debug | `malloc` + debug |
| `mimalloc` (free-threaded) | mimalloc | mimalloc | mimalloc |
| `mimalloc_debug` | mimalloc + debug | mimalloc + debug | mimalloc + debug |

Setting `PYTHONMALLOC=malloc` disables pymalloc entirely, routing all allocations through the system allocator. This is useful for memory debugging with Valgrind or AddressSanitizer, which understand the system allocator but not pymalloc's internal bookkeeping.

### 7.7 Debug Hooks

When debug mode is enabled (via `PYTHONMALLOC=debug` or `PyMem_SetupDebugHooks()`), each allocation is wrapped with guard bytes and metadata:

- `0xCD` (PYMEM_CLEANBYTE): Fills newly allocated memory to detect use of uninitialized data.
- `0xDD` (PYMEM_DEADBYTE): Fills freed memory to detect use-after-free.
- `0xFD` (PYMEM_FORBIDDENBYTE): Guard bytes before and after the allocation to detect buffer overflows/underflows.

The debug allocator also detects API domain violations (e.g., allocating with `PyObject_Malloc` but freeing with `PyMem_Free`).

### 7.8 mimalloc in Free-Threaded Builds

Free-threaded CPython (Python 3.13+) replaces pymalloc with mimalloc, a general-purpose thread-safe allocator developed by Microsoft Research. mimalloc provides:

- **Per-thread heaps**: Each thread allocates from its own heap, eliminating lock contention on the fast path.
- **Size-segregated allocation**: Similar to pymalloc but with no upper size limit.
- **Page-based organization**: mimalloc "pages" (not OS pages) contain fixed-size blocks, enabling efficient GC traversal.
- **Heap separation**: The free-threaded build maintains three separate heaps (non-GC objects, GC objects with managed dicts, GC objects without) to ensure that freed memory is reused only for objects of the same category.

### 7.9 Strengths and Limitations

**Strengths**: (1) pymalloc provides fast allocation for the common case (small objects). (2) The three-domain API enforces discipline and enables per-domain debugging. (3) Debug hooks catch common memory corruption bugs. (4) mimalloc integration enables scalable allocation in multi-threaded contexts.

**Limitations**: (1) pymalloc fragmentation can prevent arena release in long-running processes. (2) pymalloc's 512-byte threshold means medium-sized allocations (513 bytes to a few KB) go directly to the system allocator, potentially missing optimization opportunities. (3) The free-threaded build's three-heap design adds complexity and potential fragmentation.

---

## 8. Object Caching and Interning

### 8.1 Theory

Object caching and interning are memory optimization strategies that exploit the observation that certain values are created so frequently that pre-allocating or reusing them yields significant performance gains. These strategies trade startup memory cost for reduced allocation frequency during execution.

### 8.2 Small Integer Cache

CPython pre-allocates integer objects for the range [-5, 256] at interpreter startup. Any operation that produces an integer in this range returns a pointer to the pre-allocated object rather than creating a new one:

```python
a = 256
b = 256
a is b  # True -- same pre-allocated object

a = 257
b = 257
a is b  # False in the general case (implementation-dependent)
```

The range [-5, 256] was chosen empirically: these integers appear with overwhelming frequency in typical Python programs (loop counters, array indices, boolean conversions, error codes). The cache consumes approximately 262 * 28 bytes = ~7 KB at startup -- a negligible cost for the allocation savings.

With PEP 683 (Python 3.12+), these cached integers are also immortalized, meaning their reference counts are never modified. This eliminates cache line invalidation when multiple threads or code paths use the same small integer.

### 8.3 String Interning

CPython interns (deduplicates) certain strings so that string comparisons can use pointer equality (`is`) instead of character-by-character comparison:

**Automatically interned**: Identifier-like strings (matching `[a-zA-Z0-9_]+`) encountered during compilation, attribute names, dictionary keys that are strings, and module names. Starting with Python 3.12, the automatic interning threshold was expanded.

**Manually interned**: `sys.intern(s)` forces a string to be interned, which is useful for strings used as dictionary keys in performance-sensitive code.

```python
import sys
a = sys.intern("hello_world")
b = sys.intern("hello_world")
a is b  # True -- guaranteed same object
```

Interned strings provide two benefits: (1) reduced memory when the same string value appears many times, and (2) O(1) equality comparison (pointer comparison) instead of O(n) character comparison. The second benefit is particularly significant for dictionary lookups, where key comparison is on the critical path.

### 8.4 __slots__ and Per-Instance Memory

By default, Python class instances store their attributes in a per-instance `__dict__` dictionary. The `__slots__` mechanism replaces this dictionary with a fixed-layout struct:

```python
class Point:
    __slots__ = ('x', 'y')
    def __init__(self, x, y):
        self.x = x
        self.y = y

class PointDict:
    def __init__(self, x, y):
        self.x = x
        self.y = y
```

The memory savings are substantial:

```python
import sys
sys.getsizeof(Point(1, 2))       # ~56 bytes
sys.getsizeof(PointDict(1, 2))   # ~48 bytes for the object + ~104 bytes for __dict__
```

A `__slots__` class instance avoids the ~104-byte per-instance `__dict__` overhead. For classes with millions of instances (data records, tree nodes, graph vertices), this can reduce memory consumption by 50-70%.

Trade-offs: `__slots__` classes cannot have arbitrary attributes, do not support `__dict__`-based introspection by default, and complicate inheritance (each class in the hierarchy must declare its own `__slots__`). If `__weakref__` is needed but not in `__slots__`, weak referencing is disabled for the class.

### 8.5 Free Lists

CPython maintains type-specific free lists that cache recently deallocated objects for reuse, avoiding trips to the allocator:

**Tuple free list**: CPython caches empty tuples (the empty tuple `()` is a singleton) and maintains free lists for tuples of length 1 through 20. When a tuple of length N is deallocated, it is added to the free list for that length rather than being freed. The next allocation of a tuple of length N reuses the cached structure.

**Float free list**: Deallocated float objects are cached in a free list. Since all floats have the same size (24 bytes on 64-bit), a single free list suffices.

**List free list**: The list *object* (not its backing array) is cached. The backing array (`ob_item`) is allocated separately and may be resized.

**Dict free list**: Similar to lists, the dict object structure is cached while the hash table storage is managed separately.

Free lists are bounded in size (typically 80-2000 entries, depending on the type) to prevent unbounded memory growth. They are cleared during full GC collections or when `gc.collect()` is called with generation 2.

### 8.6 Strengths and Limitations

**Strengths**: (1) The small integer cache eliminates millions of allocations in typical programs. (2) String interning enables O(1) dictionary key comparisons. (3) `__slots__` gives the programmer explicit control over per-instance memory. (4) Free lists reduce allocation overhead for frequently created/destroyed types.

**Limitations**: (1) Caching and interning consume memory even when the cached values are not needed. (2) The small integer cache range is hardcoded and not tunable. (3) String interning criteria are implementation-defined and can surprise users. (4) Free lists delay memory release back to the allocator.

---

## 9. Weak References

### 9.1 Theory

Weak references solve a fundamental tension in reference-counted systems: the need to observe or cache an object without preventing its collection. A strong reference (the default in Python) prevents the referenced object from being deallocated; a weak reference allows observation without contributing to the reference count.

### 9.2 The weakref Module

Python's `weakref` module provides several weak reference types:

```python
import weakref

class MyObj:
    pass

obj = MyObj()
ref = weakref.ref(obj)          # Create a weak reference
ref()                            # Dereference: returns obj (or None if collected)

# Callback on collection
def on_finalize(r):
    print(f"Object collected, ref={r}")

ref = weakref.ref(obj, on_finalize)
del obj                          # Triggers callback

# Weak-valued containers
d = weakref.WeakValueDictionary()
d['key'] = MyObj()              # Entry disappears when object is collected

s = weakref.WeakSet()
s.add(MyObj())                  # Entry disappears when object is collected
```

### 9.3 The __weakref__ Slot

For an object to support weak references, its type must allocate space for a `__weakref__` slot -- a pointer in the object's memory layout that heads a linked list of weak references to that object. Most built-in types and user-defined classes (unless using `__slots__` without `__weakref__`) support weak references by default.

When `__slots__` is used, weak reference support is disabled unless `'__weakref__'` is explicitly included:

```python
class NoWeakRef:
    __slots__ = ('x',)

class WithWeakRef:
    __slots__ = ('x', '__weakref__')

weakref.ref(NoWeakRef())     # TypeError: cannot create weak reference
weakref.ref(WithWeakRef())   # Works
```

### 9.4 Interaction with Garbage Collection

Weak references interact with the cyclic GC during the finalization phase. When the collector identifies unreachable objects:

1. Weak references to unreachable objects that have callbacks are processed first. If the weak reference itself is reachable, its callback is invoked with the weak reference object as the argument.
2. The weak reference's internal pointer (`wr_object`) is set to `Py_None`, causing subsequent dereferences to return `None`.
3. `WeakValueDictionary` and `WeakKeyDictionary` use these callbacks to remove entries whose values/keys have been collected.

A subtle correctness issue: weak reference callbacks must not resurrect the unreachable object. The GC processes weak references before calling `tp_finalize` or `tp_clear`, ensuring callbacks see a consistent state.

### 9.5 Implementation: WeakValueDictionary

`WeakValueDictionary` wraps each value in a `KeyedRef` (a subclass of `weakref.ref`) that stores the dictionary key alongside the weak reference. The `KeyedRef`'s callback, registered at creation time, removes the corresponding entry from the dictionary when the value is collected:

```python
# Simplified internal logic
class KeyedRef(weakref.ref):
    __slots__ = ('key',)
    def __new__(type, ob, callback, key):
        self = super().__new__(type, ob, callback)
        self.key = key
        return self
```

This design ensures O(1) cleanup when a value is collected -- the callback knows exactly which key to remove -- but introduces a subtle lifecycle dependency: the dictionary must remain alive for the callback to execute safely.

### 9.6 Use Cases and Patterns

- **Caches**: Cache expensive-to-compute objects without preventing their collection when memory pressure increases.
- **Observer patterns**: Allow observers to register interest in objects without creating ownership cycles.
- **Parent-child relationships**: Children hold weak references to parents, avoiding reference cycles.
- **Canonicalization maps**: `WeakValueDictionary` for deduplicating objects by identity.

### 9.7 Strengths and Limitations

**Strengths**: (1) Breaks reference cycles without manual intervention. (2) Callbacks enable reactive cleanup (cache eviction, observer removal). (3) `WeakValueDictionary` provides transparent caching with automatic eviction.

**Limitations**: (1) Not all types support weak references (e.g., `int`, `str`, `tuple`). (2) Callback ordering is LIFO (most recently registered first), which can be surprising. (3) Weak references add per-object overhead (the `__weakref__` slot and the weak reference object itself). (4) Thread safety of callbacks requires careful consideration in free-threaded builds.

---

## 10. Memory in Free-Threaded Python (PEP 703)

### 10.1 Theory

The Global Interpreter Lock has been CPython's mechanism for memory safety since the early 1990s. By ensuring that only one thread executes Python bytecode at a time, the GIL makes non-atomic reference counting safe, simplifies C extension development, and avoids the need for fine-grained locking of Python's internal data structures. But the GIL prevents Python from exploiting multi-core processors for CPU-bound workloads, a limitation that has become increasingly painful as core counts grow.

PEP 703 (accepted July 2023) proposes making the GIL optional by replacing CPython's reference counting and garbage collection with thread-safe variants. The key challenge is maintaining reference counting's performance characteristics (deterministic deallocation, low per-operation overhead) while eliminating the assumption of single-threaded execution.

### 10.2 Biased Reference Counting

The centerpiece of PEP 703's memory management is biased reference counting, based on work by Choi, Shull, and Torrellas (2018). The key observation is that most objects are accessed primarily by a single thread (their creator), even in multi-threaded programs. Biased reference counting exploits this by maintaining separate local and shared reference counts:

**Object header fields**:
- `ob_tid`: The thread ID of the owning thread (the thread that created the object).
- `ob_ref_local`: A thread-local reference count, modified by the owning thread using non-atomic operations.
- `ob_ref_shared`: A shared reference count, modified by other threads using atomic compare-and-swap operations.
- `ob_mutex`: A per-object lock (1 byte) for fine-grained critical sections.

**Increment semantics**:
- If the current thread is the owning thread: `ob_ref_local++` (non-atomic, fast).
- Otherwise: `atomic_add(&ob_ref_shared, 4)` (the shift by 2 accounts for two state bits in the low bits of `ob_ref_shared`).

**Decrement semantics**:
- If the current thread is the owning thread: `ob_ref_local--`. If `ob_ref_local` reaches zero, the thread attempts to merge counts and potentially deallocate.
- Otherwise: `atomic_sub(&ob_ref_shared, 4)`.

**State machine**: The two low bits of `ob_ref_shared` encode the object's state:
- `0b00` (Default): Fast deallocation path available; initial state.
- `0b01` (Weakrefs): Supports concurrent weak reference access.
- `0b10` (Queued): A non-owning thread has requested reference count merge.
- `0b11` (Merged): Object is no longer owned by any specific thread.

Objects can only be deallocated from the Default or Merged states. Transitions to the Merged state require atomic compare-and-swap operations.

### 10.3 Deferred Reference Counting

For objects accessed frequently across threads -- top-level functions, code objects, modules, methods -- even biased reference counting would create contention. PEP 703 introduces deferred reference counting for these objects:

The interpreter skips `Py_INCREF`/`Py_DECREF` operations for objects marked as using deferred reference counting (indicated by the two most significant bits of `ob_ref_local`). The true reference count is the sum of the reference count fields plus any stack references across all threads -- but this sum can only be safely computed when all threads are paused during garbage collection.

Deferred reference counting objects can only be deallocated during GC cycles. This is acceptable because these objects already naturally form reference cycles in CPython (e.g., functions reference their module, modules reference their functions), so they would typically be collected by the cyclic GC anyway.

### 10.4 Garbage Collection Changes

The free-threaded build makes fundamental changes to the garbage collector:

**Stop-the-world pausing**: The collector must pause all threads to compute correct reference counts. Thread states transition through `ATTACHED` -> `GC` -> `ATTACHED`, with the GC thread coordinating pauses via the eval breaker mechanism.

**Non-generational collection**: The free-threaded build eliminates generational collection, using a single generation for all tracked objects. The rationale is that frequent stop-the-world pauses for young generation collection would have disproportionate impact on multi-threaded applications, and reference counting already handles most short-lived objects.

**Deferred reference integration**: During collection, the GC thread traverses every thread's stack to resolve deferred references, incrementing `gc_refs` for each deferred reference found.

**mimalloc page traversal**: Instead of maintaining explicit doubly-linked lists of tracked objects, the free-threaded GC leverages mimalloc's page structure to enumerate objects efficiently.

### 10.5 Per-Object Locking

Every container object in the free-threaded build gains a lightweight 1-byte `ob_mutex` for fine-grained locking. Critical sections are managed through four macros:

```c
Py_BEGIN_CRITICAL_SECTION(op);     // Lock one object
Py_END_CRITICAL_SECTION();          // Unlock

Py_BEGIN_CRITICAL_SECTION2(a, b);  // Lock two objects (ordered by address)
Py_END_CRITICAL_SECTION2();         // Unlock both
```

Read-heavy operations (e.g., `list[idx]`, `dict[key]`) use an optimistic approach: they attempt a lock-free read with a conditional reference increment, falling back to locking only when another thread is concurrently modifying the container.

### 10.6 Performance Characteristics

PEP 703's implementation introduces measurable overhead:

| Metric | Overhead vs. GIL Build |
|---|---|
| Single-threaded (pyperformance) | ~5-6% slower |
| Multi-threaded workloads | ~7-8% overhead, but with true parallelism |
| Memory per object | +8-16 bytes (expanded header) |

The overhead comes primarily from biased reference counting checks (owning-thread comparison on every incref/decref), per-object mutex initialization, and the expanded object header. For multi-threaded CPU-bound workloads, the parallelism gains far exceed the per-operation overhead; for single-threaded workloads, the overhead is the price of a unified runtime.

### 10.7 Strengths and Limitations

**Strengths**: (1) Enables true multi-threaded parallelism for CPU-bound Python. (2) Biased reference counting preserves deterministic deallocation for the common case (single-threaded object access). (3) Per-object locking avoids coarse-grained serialization. (4) The design maintains backward compatibility with correctly written C extensions.

**Limitations**: (1) 5-8% single-threaded overhead is non-trivial for workloads that are already I/O-bound. (2) Expanded object header increases memory consumption. (3) C extensions that relied on the GIL for thread safety may break. (4) Stop-the-world GC pauses affect all threads simultaneously. (5) The free-threaded build remains experimental as of Python 3.14.

---

## 11. Memory Profiling and Debugging

### 11.1 tracemalloc

`tracemalloc` is CPython's built-in memory tracing framework (Python 3.4+). It hooks into the memory allocation domains to record the Python traceback for each allocation:

```python
import tracemalloc

tracemalloc.start(25)  # Record 25 frames of traceback per allocation

# ... run code ...

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')  # Group by source line
for stat in top_stats[:10]:
    print(stat)

# Compare two snapshots to find leaks
snapshot1 = tracemalloc.take_snapshot()
# ... more code ...
snapshot2 = tracemalloc.take_snapshot()
diff = snapshot2.compare_to(snapshot1, 'lineno')
for stat in diff[:10]:
    print(stat)
```

tracemalloc adds ~30% overhead to allocation-heavy workloads, as it must record and store a Python traceback for each allocation. It can be started at interpreter launch with `PYTHONTRACEMALLOC=NFRAME` or `-X tracemalloc=NFRAME`.

**Interaction with pymalloc**: When pymalloc is active, tracemalloc records allocations at the pymalloc level (individual objects), not at the arena/pool level. Setting `PYTHONMALLOC=malloc` before running with tracemalloc ensures that each allocation corresponds to a distinct system allocator call, providing cleaner attribution.

### 11.2 objgraph

`objgraph` is a third-party tool for visualizing Python object reference graphs:

```python
import objgraph

objgraph.show_most_common_types(limit=10)  # Most common object types
objgraph.show_growth()                      # Types that grew since last call
objgraph.show_backrefs(obj, max_depth=3,   # Graph of objects referencing 'obj'
                       filename='refs.png')
objgraph.find_backref_chain(obj, objgraph.is_proper_module)  # Chain to a module
```

objgraph uses `gc.get_referrers()` and `gc.get_referents()` to traverse the object graph. Its primary use case is diagnosing memory leaks by visualizing unexpected references that prevent object collection.

### 11.3 memory_profiler

`memory_profiler` provides line-by-line memory usage profiling:

```python
from memory_profiler import profile

@profile
def compute():
    a = [1] * 1_000_000
    b = [2] * 2_000_000
    del b
    return a
```

Output:
```
Line #    Mem usage    Increment   Line Contents
     3    45.2 MiB     45.2 MiB   def compute():
     4    52.8 MiB      7.6 MiB       a = [1] * 1_000_000
     5    68.1 MiB     15.3 MiB       b = [2] * 2_000_000
     6    52.8 MiB    -15.3 MiB       del b
     7    52.8 MiB      0.0 MiB       return a
```

`memory_profiler` samples the process's RSS (Resident Set Size) from `/proc/self/statm` (Linux) or equivalent, so its measurements reflect OS-level memory usage rather than Python-level allocations. This means it captures memory from C extensions and system allocator overhead but cannot attribute memory to individual Python objects.

### 11.4 pympler

`pympler` provides object-level memory measurement and tracking:

```python
from pympler import asizeof, tracker

# Deep size measurement (recursive, unlike sys.getsizeof)
asizeof.asizeof([1, 2, [3, 4, 5]])  # Includes size of nested objects

# Object tracking
tr = tracker.SummaryTracker()
# ... run code ...
tr.print_diff()  # Show new objects since last call
```

`pympler.asizeof` is the deep-size alternative to `sys.getsizeof`: it recursively follows references to compute the total memory consumed by an object and all objects it transitively references. This is essential for understanding the true memory cost of complex data structures.

### 11.5 Valgrind and AddressSanitizer Integration

For diagnosing memory corruption in C extensions, CPython integrates with system-level memory debugging tools:

**Valgrind**: CPython provides a `valgrind.supp` suppression file to filter false positives from pymalloc's internal bookkeeping. For best results, run with `PYTHONMALLOC=malloc` to disable pymalloc:

```bash
PYTHONMALLOC=malloc valgrind --suppressions=Misc/valgrind-python.supp \
    python script.py
```

**AddressSanitizer (ASan)**: CPython can be compiled with ASan to detect buffer overflows, use-after-free, and other memory errors:

```bash
CC=clang CXX=clang++ \
    CFLAGS="-fsanitize=address -fno-omit-frame-pointer" \
    LDFLAGS="-fsanitize=address" \
    ./configure --with-pydebug --without-pymalloc
make
```

The `--without-pymalloc` flag is critical: ASan needs to see individual allocations to detect errors, but pymalloc's internal pooling hides them.

### 11.6 Choosing the Right Tool

| Need | Tool | Granularity | Overhead |
|---|---|---|---|
| Where is memory allocated? | `tracemalloc` | Per-allocation with traceback | ~30% |
| What objects exist? | `objgraph` | Per-object type | Low (snapshot) |
| Which lines use memory? | `memory_profiler` | Per-line RSS | ~10-20% |
| Deep object size? | `pympler.asizeof` | Recursive object graph | High (traversal) |
| C extension bugs? | Valgrind / ASan | Per-byte | 10-50x slowdown |
| pymalloc statistics? | `PYTHONMALLOCSTATS` | Per-pool/arena | None |

---

## 12. Comparative Synthesis

### 12.1 CPython vs. PyPy vs. GraalPy

| Dimension | CPython | PyPy | GraalPy |
|---|---|---|---|
| **Primary GC** | Reference counting + cyclic GC | Tracing (mark-and-sweep) | Tracing (JVM/Truffle GC) |
| **Generational?** | Yes (2 generations) | Yes (nursery + old) | Yes (JVM generational) |
| **Deterministic dealloc?** | Yes (refcount zero) | No (GC-dependent) | No (GC-dependent) |
| **Cycle handling** | Supplementary tracing GC | Built into tracing GC | Built into tracing GC |
| **Object header overhead** | 16 bytes (default), 24-32 bytes (free-threaded) | Lower (no refcount field) | JVM object header |
| **Allocator** | pymalloc (arena/pool/block) | Nursery bump-pointer + OS allocator | JVM allocator |
| **GIL** | Yes (optional in 3.13+) | Yes (with STM research) | No (JVM threading) |
| **C extension compat** | Native | cpyext (compatibility layer) | GraalPy C API (emulation) |
| **Typical memory usage** | Baseline | Often lower (no per-object refcount) | Often higher (JVM overhead) |
| **Typical throughput** | Baseline | ~4x faster (JIT-compiled) | ~4x faster (JIT), ~4x slower (interpreted) |
| **GC pause behavior** | Bounded (young gen), potentially long (old gen) | Incremental nursery, stop-the-world major | Varies by JVM GC (G1, ZGC, etc.) |

### 12.2 CPython vs. JVM and CLR

CPython's hybrid approach contrasts sharply with the JVM and CLR, which use pure tracing collectors without reference counting:

**Deallocation determinism**: CPython's reference counting provides deterministic deallocation that the JVM and CLR cannot match. This is why Python's `with` statement for resource management is more of a best practice, while Java's `try-with-resources` is a necessity -- Java cannot rely on prompt finalization.

**Throughput**: The JVM's generational collectors (G1, ZGC, Shenandoah) achieve higher allocation throughput through bump-pointer allocation in thread-local buffers and concurrent collection. CPython's pymalloc is fast but cannot match bump-pointer allocation's single-instruction fast path.

**Pause times**: Modern JVM collectors (ZGC, Shenandoah) achieve sub-millisecond pause times through concurrent marking and compaction. CPython's cyclic GC pause times scale with the number of tracked objects, though most collections (young generation) are fast.

**Memory overhead**: CPython's per-object reference count adds 8 bytes per object. The JVM's mark bits are stored separately (or in the object header's mark word, which serves multiple purposes), resulting in lower per-object overhead for GC metadata.

### 12.3 The Unified Theory Perspective

Bacon et al.'s unified theory illuminates why CPython's hybrid approach is effective. Reference counting is a form of "eager" garbage collection that processes each pointer mutation immediately, while tracing is "lazy" -- it defers all work to collection time. CPython's hybrid captures the best of both: eager processing for the common case (short-lived acyclic objects), lazy processing for the hard case (cycles). The cost is maintaining two separate mechanisms with their own data structures and protocols.

---

## 13. Open Problems

### 13.1 Free-Threaded Build Maturity

The free-threaded build (PEP 703) is experimental as of Python 3.14. Key open problems include:

- **C extension ecosystem**: The vast majority of C extensions assume the GIL. While many popular libraries (NumPy, pandas) are being updated, the long tail of extensions will take years to become thread-safe.
- **Performance parity**: The 5-8% single-threaded overhead is a significant concern for workloads that do not benefit from parallelism.
- **GC pause scalability**: The stop-the-world non-generational GC in the free-threaded build may cause unacceptable pauses for programs with large heaps.

### 13.2 Incremental and Concurrent GC

CPython's cyclic GC performs stop-the-world collections that scale with heap size. The incremental GC experiment for Python 3.13 was reverted due to performance regressions. Achieving low-latency collection for large Python heaps remains an open problem. Concurrent GC (where collection proceeds alongside mutator execution) would require write barriers that CPython currently lacks.

### 13.3 Memory Fragmentation in Long-Running Processes

pymalloc's inability to compact memory (move objects to consolidate free space) means that long-running processes (web servers, data pipelines) can suffer from fragmentation. Arenas that contain even a single live object cannot be returned to the OS, leading to gradually increasing RSS over time. The mimalloc allocator in free-threaded builds may partially address this through its different allocation strategy, but compaction remains impossible without a moving GC.

### 13.4 Sub-Interpreter Memory Isolation

PEP 554 (Multiple Interpreters in the Stdlib) and PEP 684 (A Per-Interpreter GIL) move toward memory isolation between sub-interpreters. Open problems include: how to share immutable objects between interpreters without reference count contention, how to handle cross-interpreter references, and how to manage memory for interpreters with independent GCs.

### 13.5 Memory-Efficient Object Representations

CPython's 16-byte-minimum per-object header makes it impractical for workloads involving millions of small values (e.g., numerical computing). Projects like NumPy, Arrow, and Polars work around this by storing data in contiguous C arrays outside the Python object model. A more fundamental solution would require changes to CPython's object representation -- compact value types, inline storage for small objects, or tagged pointers -- that conflict with the current `PyObject *` abstraction.

---

## 14. Conclusion

CPython's memory management is a carefully evolved hybrid system that balances determinism, simplicity, and performance. Reference counting provides the immediate, predictable deallocation that Python programmers rely upon for resource management. The cyclic garbage collector handles the cycles that reference counting cannot. pymalloc optimizes for Python's characteristic allocation pattern of small, short-lived objects. Object caching and interning amortize the cost of frequently used values. And weak references enable observation without ownership.

The free-threaded Python initiative represents the most fundamental change to this architecture in CPython's history. Biased reference counting preserves the single-threaded fast path while enabling thread safety. Deferred reference counting addresses contention for frequently shared objects. The replacement of pymalloc with mimalloc provides thread-scalable allocation. And the per-object mutex system enables fine-grained concurrency control without the GIL's global serialization.

The transition is neither simple nor complete. The 5-8% single-threaded overhead, the expanded object header, the stop-the-world GC, and the C extension compatibility challenges represent real costs. But the architectural direction is clear: CPython's memory management is evolving from a GIL-protected sequential system to a thread-safe concurrent system, preserving as much as possible of the deterministic, incremental character that has served Python for three decades.

---

## References

1. Bacon, D.F., Cheng, P., and Rajan, V.T. "A Unified Theory of Garbage Collection." OOPSLA 2004. [https://web.eecs.umich.edu/~weimerw/2008-415/reading/bacon-garbage.pdf](https://web.eecs.umich.edu/~weimerw/2008-415/reading/bacon-garbage.pdf)

2. Choi, J., Shull, T., and Torrellas, J. "Biased Reference Counting: Minimizing Atomic Operations in Garbage Collection." PACT 2018.

3. Collins, G.E. "A Method for Overlapping and Erasure of Lists." Communications of the ACM, 3(12), 1960.

4. CPython Developer Guide. "Design of CPython's Garbage Collector." [https://github.com/python/cpython/blob/main/InternalDocs/garbage_collector.md](https://github.com/python/cpython/blob/main/InternalDocs/garbage_collector.md)

5. CPython Documentation. "Memory Management." Python 3.14 C API Reference. [https://docs.python.org/3/c-api/memory.html](https://docs.python.org/3/c-api/memory.html)

6. CPython Documentation. "gc -- Garbage Collector Interface." [https://docs.python.org/3/library/gc.html](https://docs.python.org/3/library/gc.html)

7. CPython Documentation. "weakref -- Weak References." [https://docs.python.org/3/library/weakref.html](https://docs.python.org/3/library/weakref.html)

8. CPython Documentation. "Common Object Structures." [https://docs.python.org/3/c-api/structures.html](https://docs.python.org/3/c-api/structures.html)

9. CPython Documentation. "Reference Counting." [https://docs.python.org/3/c-api/refcounting.html](https://docs.python.org/3/c-api/refcounting.html)

10. CPython Documentation. "Supporting Cyclic Garbage Collection." [https://docs.python.org/3/c-api/gcsupport.html](https://docs.python.org/3/c-api/gcsupport.html)

11. CPython Source. `Include/object.h` -- PyObject and PyVarObject definitions. [https://github.com/python/cpython/blob/main/Include/object.h](https://github.com/python/cpython/blob/main/Include/object.h)

12. CPython Source. `Objects/obmalloc.c` -- pymalloc implementation. [https://github.com/python/cpython/blob/main/Objects/obmalloc.c](https://github.com/python/cpython/blob/main/Objects/obmalloc.c)

13. Elizondo, E. "Implement Immortal Objects." CPython PR #19474. [https://github.com/python/cpython/pull/19474](https://github.com/python/cpython/pull/19474)

14. Grossman, D., Morrisett, G., Jim, T., Hicks, M., Wang, Y., and Cheney, J. "Region-Based Memory Management in Cyclone." PLDI 2002.

15. Jones, E. "Improving Python's Memory Allocator." [https://www.evanjones.ca/memoryallocator/](https://www.evanjones.ca/memoryallocator/)

16. Leijen, D. "mimalloc: Free List Sharding in Action." MSR Technical Report, 2019.

17. Memray Documentation. "Python Allocators." Bloomberg. [https://bloomberg.github.io/memray/python_allocators.html](https://bloomberg.github.io/memray/python_allocators.html)

18. PEP 442. "Safe Object Finalization." Pitrou, A. [https://peps.python.org/pep-0442/](https://peps.python.org/pep-0442/)

19. PEP 445. "Add New APIs to Customize Python Memory Allocators." Stinner, V. [https://peps.python.org/pep-0445/](https://peps.python.org/pep-0445/)

20. PEP 683. "Immortal Objects, Using a Fixed Refcount." Elizondo, E. [https://peps.python.org/pep-0683/](https://peps.python.org/pep-0683/)

21. PEP 703. "Making the Global Interpreter Lock Optional in CPython." Gross, S. [https://peps.python.org/pep-0703/](https://peps.python.org/pep-0703/)

22. PyPy Documentation. "Differences Between PyPy and CPython." [https://doc.pypy.org/en/latest/cpython_differences.html](https://doc.pypy.org/en/latest/cpython_differences.html)

23. PyPy Documentation. "Garbage Collector Documentation and Configuration." [https://doc.pypy.org/en/latest/gc_info.html](https://doc.pypy.org/en/latest/gc_info.html)

24. Rushter. "Memory Management in Python." [https://rushter.com/blog/python-memory-managment/](https://rushter.com/blog/python-memory-managment/)

25. Stinner, V. "A New C API for CPython." [https://vstinner.github.io/new-python-c-api.html](https://vstinner.github.io/new-python-c-api.html)

26. Ungar, D. "Generation Scavenging: A Non-Disruptive High Performance Storage Reclamation Algorithm." SOSP 1984.

27. Coding Confessions. "CPython Garbage Collection: The Internal Mechanics and Algorithms." [https://blog.codingconfessions.com/p/cpython-garbage-collection-internals](https://blog.codingconfessions.com/p/cpython-garbage-collection-internals)

28. Coding Confessions. "How CPython Implements Reference Counting." [https://blog.codingconfessions.com/p/cpython-reference-counting-internals](https://blog.codingconfessions.com/p/cpython-reference-counting-internals)

29. Coding Confessions. "Understanding Immortal Objects in Python 3.12." [https://blog.codingconfessions.com/p/understanding-immortal-objects-in](https://blog.codingconfessions.com/p/understanding-immortal-objects-in)

30. CPython Internals (zpoint). "Garbage Collector." [https://github.com/zpoint/CPython-Internals/blob/master/Interpreter/gc/gc.md](https://github.com/zpoint/CPython-Internals/blob/master/Interpreter/gc/gc.md)

31. Python Extension Patterns. "PyObjects and Reference Counting." [https://pythonextensionpatterns.readthedocs.io/en/latest/refcount.html](https://pythonextensionpatterns.readthedocs.io/en/latest/refcount.html)

32. GraalVM Documentation. "Python Performance." [https://www.graalvm.org/jdk22/reference-manual/python/Performance/](https://www.graalvm.org/jdk22/reference-manual/python/Performance/)

---

## Practitioner Resources

### Quick Reference: When Objects Are Collected

| Scenario | Mechanism | Timing |
|---|---|---|
| Last reference removed (acyclic) | Reference counting | Immediate |
| Reference cycle, no finalizer | Cyclic GC | Next GC pass |
| Reference cycle with `__del__` | Cyclic GC + PEP 442 | Next GC pass, finalizer runs first |
| Immortal object | Never | Interpreter shutdown only |
| Deferred refcount (free-threaded) | Cyclic GC | Next GC cycle |

### Quick Reference: Memory Debugging Checklist

1. **Suspect a leak?** Start with `tracemalloc` snapshots:
   ```python
   tracemalloc.start()
   snap1 = tracemalloc.take_snapshot()
   # ... run suspected leaky code ...
   snap2 = tracemalloc.take_snapshot()
   for stat in snap2.compare_to(snap1, 'lineno')[:10]:
       print(stat)
   ```

2. **Need to find what holds a reference?** Use `objgraph`:
   ```python
   objgraph.show_backrefs(suspect_obj, max_depth=5, filename='refs.png')
   ```

3. **C extension memory corruption?** Run with Valgrind or ASan:
   ```bash
   PYTHONMALLOC=malloc valgrind python script.py
   ```

4. **Want pymalloc statistics?** Set the environment variable:
   ```bash
   PYTHONMALLOCSTATS=1 python script.py
   ```

5. **Need line-by-line memory usage?** Use `memory_profiler`:
   ```python
   @profile
   def suspicious_function():
       ...
   ```

### Quick Reference: gc Module Tuning

```python
import gc

# Disable GC for batch processing (rely on reference counting)
gc.disable()
process_batch()
gc.enable()
gc.collect()  # Force collection after batch

# Tune thresholds for low-latency applications
gc.set_threshold(1000, 15, 15)  # Less frequent collection

# Register a callback for GC monitoring
def gc_callback(phase, info):
    if phase == 'stop':
        print(f"GC gen {info['generation']}: collected {info['collected']}, "
              f"uncollectable {info['uncollectable']}")
gc.callbacks.append(gc_callback)
```

### Key PEPs for Memory Management

| PEP | Title | Python Version | Status |
|---|---|---|---|
| PEP 442 | Safe Object Finalization | 3.4 | Final |
| PEP 445 | Customize Memory Allocators | 3.4 | Final |
| PEP 683 | Immortal Objects | 3.12 | Final |
| PEP 703 | Optional GIL | 3.13+ (experimental) | Accepted |
| PEP 554 | Multiple Interpreters | 3.12+ | Draft |
| PEP 684 | Per-Interpreter GIL | 3.12 | Final |
