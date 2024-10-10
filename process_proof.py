def process_proof(input_text):
    lines = input_text.split('\n')
    
    sections = {}
    current_section = None
    current_content = []
    
    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith('##'):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            current_section = stripped_line[2:].strip()
            current_content = []
        else:
            current_content.append(line)

    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    helper_lemmas = sections.get('Helper Lemmas', '')
    proof = sections.get('Proof', '')
    
    lemmas = []
    lemma_lines = []
    in_lemma = False
    for line in helper_lemmas.split('\n'):
        if line.strip().startswith('lemma'):
            if lemma_lines:
                lemmas.append('\n'.join(lemma_lines))
                lemma_lines = []
            in_lemma = True
        if in_lemma:
            lemma_lines.append(line)
        else:
            pass
    if lemma_lines:
        lemmas.append('\n'.join(lemma_lines))
    
    lemmas_not_in_proof = []
    for lemma in lemmas:
        lemma_name_line = lemma.strip().split('\n')[0]
        lemma_name = lemma_name_line.strip().split()[1]
        if lemma_name not in proof:
            lemmas_not_in_proof.append(lemma)
    
    proof_lines = proof.split('\n')
    new_proof_lines = []
    inserted_lemmas = False
    for i, line in enumerate(proof_lines):
        if line.strip().startswith('theorem'):
            if lemmas_not_in_proof:
                new_proof_lines.extend([''] + lemmas_not_in_proof + [''])
                inserted_lemmas = True
            new_proof_lines.append(line)
        else:
            new_proof_lines.append(line)
    if not inserted_lemmas and lemmas_not_in_proof:

        new_proof_lines.extend([''] + lemmas_not_in_proof + [''])
    
    formal_statement = sections.get('Formal Statement', '')
    has_assumes = any('assumes' in line for line in formal_statement.split('\n'))
    sledge_text = 'using assms sledgehammer' if has_assumes else 'sledgehammer'
    
    processed_proof_lines = []
    for line in new_proof_lines:
        stripped_line = line.strip()
        if stripped_line.endswith('sledgehammer'):
            processed_proof_lines.append(line)
        elif stripped_line.endswith('sorry'):
            processed_proof_lines.append(line.replace('sorry', sledge_text))
        elif stripped_line == '':
            processed_proof_lines.append(line)
        else:
            if any(stripped_line.startswith(prefix) for prefix in ['have', 'then have', 'show', 'then show', 'also have', 'finally have']):
                if any(stripped_line.endswith(method) for method in ['by', 'using', 'proof', 'sorry', 'sledgehammer']):
                    processed_proof_lines.append(line)
                else:
                    processed_proof_lines.append(line + '\n  ' + sledge_text)
            else:
                processed_proof_lines.append(line)
    new_proof = '\n'.join(processed_proof_lines)
    
    output_sections = []
    for section_name in ['Problems', 'Informal proof', 'Formal Statement', 'Helper Lemmas', 'Proof']:
        if section_name in sections:
            output_sections.append('## ' + section_name)
            if section_name == 'Proof':
                output_sections.append(new_proof)
            else:
                output_sections.append(sections[section_name])
    output_text = '\n'.join(output_sections)
    return output_text

if __name__ == "__main__":
    input_text = '''Here is the actual problem. Create a formal proof sketch placing `using assms sledgehammer` in the gaps of the proof sketch, taking inspiration from the previous examples.
If there are no assumptions in the formal statement, i.e. no line beginning with `assumes`, then just use `sledgehammer` instead of `using assms sledgehammer` in the gaps.
Use the lemmas provided to you, if any, to help close goals in the proof.
## Problems
Prove that the fraction $\frac{21n+4}{14n+3}$ is irreducible for every natural number $n$.

## Informal proof
Step 1: Apply the Euclidean algorithm to find the greatest common divisor (gcd) of $21n + 4$ and $14n + 3$.
Step 2: Simplify the gcd expression to $(7n + 1, 14n + 3)$.
Step 3: Further simplify the gcd expression to $(7n + 1, 1)$.
Step 4: Conclude that the gcd is 1, hence the fraction $\frac{21n+4}{14n+3}$ is irreducible.

## Formal Statement
```isabelle
theorem imo_1959_p1:
fixes n :: nat
shows "gcd (21*n + 4) (14*n + 3) = 1"
```

## Helper Lemmas
(* lemma 0. A lemma proving the Euclidean algorithm for finding the gcd of two numbers would be useful for steps 1 to 3. *)
lemma euclidean_algorithm:
fixes a b :: nat
shows "gcd a b = gcd (a - b * (a div b)) b"
sledgehammer

(* lemma 1. A lemma showing that the gcd of any number and 1 is always 1 would be useful for step 4. *)
lemma gcd_with_1:
fixes a :: nat
shows "gcd a 1 = 1"
sledgehammer



## Proof
```isabelle

(* formal statement copy from the input *)
theorem imo_1959_p1:
fixes n :: nat
shows "gcd (21*n + 4) (14*n + 3) = 1"
proof -
(* Step 1: Apply the Euclidean algorithm to find the greatest common divisor (gcd) of $21n + 4$ and $14n + 3$. *)
have c0: "gcd (21*n + 4) (14*n + 3) = gcd ((21*n + 4) - (14*n + 3) * ((21*n + 4) div (14*n + 3))) (14*n + 3)"
    using euclidean_algorithm sledgehammer

(* Step 2: Simplify the gcd expression to $(7n + 1, 14n + 3)$. *)
also have "... = gcd (7*n + 1) (14*n + 3)"
    sledgehammer

(* Step 3: Further simplify the gcd expression to $(7n + 1, 1)$. *)
also have "... = gcd (7*n + 1) (1)"
    sledgehammer

(* Step 4: Conclude that the gcd is 1, hence the fraction $\frac{21n+4}{14n+3}$ is irreducible. *)
also have "... = 1"
    using gcd_with_1 sledgehammer
finally show ?thesis .
qed
```
'''
    output_text = process_proof(input_text)
    print(output_text)