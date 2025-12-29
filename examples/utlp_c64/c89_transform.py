#!/usr/bin/env python3
"""
C89 Transformation Script for cc65 Compatibility

Transforms C99 code into C89-compatible code for cc65 compilation.
Run this on utlp_skeleton.c before compiling for C64.

Transformations applied:
1. Move for-loop variable declarations outside the loop
2. Split declaration-with-initialization into separate statements
3. Replace #pragma once with include guards (in headers)
4. Transform C99 designated initializers to C89 positional
5. Remove inline keyword

Usage:
    python c89_transform.py input.c output.c
    python c89_transform.py input.h output.h
"""

import re
import sys
import os


def transform_for_loop_declarations(code):
    """
    Transform for-loop variable declarations from C99 to C89.

    C99: for (uint8_t i = 0; i < n; i++)
    C89: uint8_t i; for (i = 0; i < n; i++)
    """
    # Pattern: for (TYPE VAR = INIT; ...)
    pattern = r'for\s*\(\s*((?:const\s+)?(?:unsigned\s+)?(?:u?int(?:8|16|32|64)_t|int|char|short|long|size_t|bool))\s+(\w+)\s*=\s*([^;]+);([^)]+)\)'

    def replace_for(match):
        var_type = match.group(1)
        var_name = match.group(2)
        init_value = match.group(3)
        rest = match.group(4)
        return f'{var_type} {var_name};\n    for ({var_name} = {init_value};{rest})'

    return re.sub(pattern, replace_for, code)


def transform_designated_initializers(code):
    """
    Transform C99 designated initializers to C89 positional initializers.

    C99: = { .field1 = val1, .field2 = val2 }
    C89: = { val1, val2 }

    Note: This only works if fields are in declaration order!
    """
    # Pattern: = { .field = value, .field2 = value2, ... }
    # We'll remove the ".field = " parts, keeping just values

    def replace_designated(match):
        full_init = match.group(0)
        # Remove all ".fieldname = " patterns, keep the values
        result = re.sub(r'\.\w+\s*=\s*', '', full_init)
        return result

    # Match struct initializer blocks with designated initializers
    pattern = r'=\s*\{[^}]*\.\w+\s*=[^}]*\}'
    return re.sub(pattern, replace_designated, code)


def transform_mid_block_declarations(code):
    """
    Split declaration-with-initialization into declaration + assignment.

    C99: uint64_t x = get_value();
    C89: uint64_t x; x = get_value();

    This doesn't move declarations to block start, but helps cc65 parse them.
    Combined with --standard cc65, this may be enough.
    """
    # Common type patterns
    types = r'(?:const\s+)?(?:unsigned\s+)?(?:u?int(?:8|16|32|64)_t|int|char|short|long|long\s+long|size_t|bool|int64_t|uint64_t)'

    # Pattern: TYPE VAR = EXPR; (not inside for-loop, not a function definition)
    # Look for declarations that have an = and end with ;
    # But NOT: typedef, static declarations at file scope, or #define

    def split_declaration(match):
        indent = match.group(1)
        var_type = match.group(2)
        var_name = match.group(3)
        init_expr = match.group(4)

        # Don't transform static/const at file scope (they're OK)
        # This is a heuristic: if indent is empty or very small, might be file scope
        # But we can't reliably detect this, so transform anyway

        return f'{indent}{var_type} {var_name};\n{indent}{var_name} = {init_expr};'

    # Match: [indent]TYPE VARNAME = EXPRESSION;
    # Capture: indent, type, varname, expression
    pattern = rf'^(\s+)({types})\s+(\w+)\s*=\s*(.+);$'

    lines = code.split('\n')
    result = []
    in_function = False
    brace_depth = 0

    for line in lines:
        # Track if we're inside a function (simplified heuristic)
        if '{' in line:
            brace_depth += line.count('{')
            in_function = True
        if '}' in line:
            brace_depth -= line.count('}')
            if brace_depth == 0:
                in_function = False

        # Only transform inside functions (brace_depth > 0)
        if brace_depth > 0:
            match = re.match(pattern, line, re.MULTILINE)
            if match:
                # Check it's not a simple constant or array declaration
                init_expr = match.group(4)
                # Skip if init is just a number, string, or simple literal
                if not re.match(r'^[\d\s\-+.]+$', init_expr) and \
                   not re.match(r'^".*"$', init_expr) and \
                   not re.match(r"^'.*'$", init_expr) and \
                   not init_expr.strip() in ('true', 'false', 'NULL', '0'):
                    line = split_declaration(match)

        result.append(line)

    return '\n'.join(result)


def transform_pragma_once(code, filename):
    """
    Replace #pragma once with traditional include guards.
    """
    if not filename.endswith('.h'):
        return code

    if '#pragma once' not in code:
        return code

    # Generate guard name from filename
    guard = os.path.basename(filename).upper().replace('.', '_').replace('-', '_')
    guard = f'_{guard}_'

    # Remove #pragma once
    code = code.replace('#pragma once', '')

    # Add include guards
    header = f'#ifndef {guard}\n#define {guard}\n'
    footer = f'\n#endif /* {guard} */\n'

    return header + code + footer


def transform_static_inline(code):
    """
    cc65 doesn't support 'inline'. Remove it.
    """
    code = re.sub(r'\bstatic\s+inline\b', 'static', code)
    code = re.sub(r'\binline\s+static\b', 'static', code)
    code = re.sub(r'\binline\b', '', code)
    return code


def add_cc65_compat_header(code):
    """
    Add cc65-specific compatibility note at the top of C files.
    """
    compat = '''/* cc65 C89 compatibility - auto-generated */
#ifdef __CC65__
/* cc65 doesn't support some C99 features */
/* This file was transformed by c89_transform.py */
#endif

'''
    include_match = re.search(r'^#include', code, re.MULTILINE)
    if include_match:
        pos = include_match.start()
        return code[:pos] + compat + code[pos:]
    return compat + code


def transform_file(input_path, output_path):
    """
    Apply all C89 transformations to a file.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        code = f.read()

    filename = os.path.basename(input_path)

    # Apply transformations in order
    code = transform_pragma_once(code, filename)
    code = transform_static_inline(code)
    code = transform_designated_initializers(code)
    code = transform_for_loop_declarations(code)
    code = transform_mid_block_declarations(code)

    # Add compatibility header for C files
    if input_path.endswith('.c'):
        code = add_cc65_compat_header(code)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(code)

    print(f"Transformed: {input_path} -> {output_path}")


def main():
    if len(sys.argv) < 3:
        print("Usage: python c89_transform.py <input> <output>")
        print("       python c89_transform.py --check <file>")
        sys.exit(1)

    if sys.argv[1] == '--check':
        with open(sys.argv[2], 'r') as f:
            code = f.read()

        issues = []
        if '#pragma once' in code:
            issues.append("- #pragma once (will add include guards)")
        if re.search(r'for\s*\(\s*(?:u?int|char|short|long|size_t|bool)', code):
            issues.append("- for-loop variable declarations (will extract)")
        if 'inline' in code:
            issues.append("- inline keyword (will remove)")
        if re.search(r'\.\w+\s*=', code):
            issues.append("- designated initializers (will convert to positional)")

        if issues:
            print(f"C89 issues found in {sys.argv[2]}:")
            for issue in issues:
                print(issue)
        else:
            print(f"No C89 issues found in {sys.argv[2]}")

        sys.exit(0)

    transform_file(sys.argv[1], sys.argv[2])


if __name__ == '__main__':
    main()
